import json
import math

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.authentication import SessionAuthentication

from .identity import IdentityError, player_id_for
from .models import (
    ActivityAttempt,
    ActivityStory,
    AnimationEvent,
    ClassLevel,
    Chapter,
    LearningActivity,
    Learner,
    MissionObjective,
    PlayerStoryProgress,
    Practical,
    PracticalAttempt,
    PracticalStep,
    Question,
    StoryBranch,
    StoryCharacter,
    StoryDialogue,
    StoryMission,
    StoryReward,
    StoryScene,
    Subject,
)
from .story_engine import StoryGenerationError, generate_story_blueprint, validate_story_blueprint
from .story_records import store_story, story_payload, stored_story_blueprint


def read_json(request):
    try:
        value = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Request body must be valid JSON.") from None
    if not isinstance(value, dict):
        raise ValueError("Request body must be a JSON object.")
    return value


def error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def identity_error_response(exc):
    return error(exc.message, exc.status)


def owned_attempt(attempt_id, learner_id):
    try:
        return PracticalAttempt.objects.select_related("practical", "learner").get(
            attempt_id=attempt_id, learner_id=learner_id
        )
    except PracticalAttempt.DoesNotExist:
        return None


def sample_by_slug(practical, slug):
    return next((sample for sample in practical.samples if sample.get("slug") == slug), None)


def practical_payload(practical):
    steps = []
    for step in practical.steps.prefetch_related("equipment").all():
        steps.append(
            {
                "order": step.order,
                "instruction": step.instruction,
                "action": step.action,
                "equipment": list(step.equipment.values("slug", "name")),
            }
        )
    return {
        "slug": practical.slug,
        "title": practical.title,
        "class": practical.chapter.class_level.number,
        "subject": practical.chapter.subject.name,
        "chapter": practical.chapter.title,
        "difficulty": practical.difficulty,
        "estimated_minutes": practical.estimated_minutes,
        "objective": practical.objective,
        "introduction": practical.introduction,
        "safety_information": practical.safety_information,
        "steps": steps,
        "samples": [
            {"slug": sample["slug"], "name": sample["name"]}
            for sample in practical.samples
        ],
        "story": story_payload(
            practical.stories.filter(status=ActivityStory.Status.PUBLISHED)
            .order_by("-generated_at")
            .first()
        ),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return JsonResponse({"status": "ok", "service": "eduplay-api"})


@api_view(["GET"])
@permission_classes([AllowAny])
def curriculum(request):
    raw_class = request.GET.get("class", "10")
    try:
        class_number = int(raw_class)
    except ValueError:
        return error("class must be a number from 1 to 12.")
    if class_number < 1 or class_number > 12:
        return error("class must be a number from 1 to 12.")

    subjects = []
    for subject in Subject.objects.filter(classes__number=class_number).distinct().prefetch_related("chapters"):
        chapters = subject.chapters.filter(class_level__number=class_number)
        subjects.append(
            {
                "slug": subject.slug,
                "name": subject.name,
                "building": subject.building,
                "chapters": [
                    {
                        "id": chapter.id,
                        "title": chapter.title,
                        "syllabus_url": chapter.syllabus_url,
                        "activities_count": chapter.activities.count(),
                    }
                    for chapter in chapters
                ],
            }
        )
    return JsonResponse(
        {"classes": list(ClassLevel.objects.values_list("number", flat=True)), "selected_class": class_number, "subjects": subjects}
    )


def activity_summary(activity):
    return {
        "slug": activity.slug,
        "title": activity.title,
        "activity_type": activity.activity_type,
        "objective": activity.objective,
        "estimated_minutes": activity.estimated_minutes,
        "steps_count": len(activity.instructions),
        "resources": activity.resources,
        "simulation": activity.simulation,
    }


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAdminUser])
def generate_story_draft(request):
    try:
        data = read_json(request)
    except ValueError as exc:
        return error(str(exc))

    activity_slug = data.get("activity_slug")
    practical_slug = data.get("practical_slug")
    if activity_slug and practical_slug:
        return error("Choose an activity or practical to attach the story draft to, not both.")
    activity = LearningActivity.objects.select_related("chapter__class_level", "chapter__subject").filter(
        slug=activity_slug
    ).first() if activity_slug else None
    practical = Practical.objects.select_related("chapter__class_level", "chapter__subject").filter(
        slug=practical_slug
    ).first() if practical_slug else None
    if activity_slug and activity is None:
        return error("Learning activity not found.", 404)
    if practical_slug and practical is None:
        return error("Practical not found.", 404)

    content = activity or practical
    try:
        class_number = int(data.get("class_number", content.chapter.class_level.number if content else 0))
    except (TypeError, ValueError):
        return error("class_number must be between 1 and 12.")
    subject = str(data.get("subject", content.chapter.subject.name if content else "")).strip()
    topic = str(data.get("topic", content.title if content else "")).strip()
    objective = str(data.get("objective", content.objective if content else "")).strip()
    steps = data.get(
        "steps",
        content.instructions if activity else [
            {"instruction": step.instruction, "action": step.action}
            for step in practical.steps.all()
        ] if practical else [],
    )
    required_objects = data.get(
        "required_objects",
        content.simulation.get("items", []) if activity else [
            item.name for step in practical.steps.all() for item in step.equipment.all()
        ] if practical else [],
    )
    if not isinstance(steps, list) or len(steps) > 20:
        return error("steps must be a list with no more than 20 entries.")
    if not isinstance(required_objects, list) or len(required_objects) > 50:
        return error("required_objects must be a list with no more than 50 entries.")
    if any(not isinstance(item, str) or len(item) > 100 for item in required_objects):
        return error("Each required object must be a string under 100 characters.")
    if any(
        not isinstance(step, dict)
        or not isinstance(step.get("instruction"), str)
        or len(step["instruction"]) > 300
        or not isinstance(step.get("action", ""), str)
        for step in steps
    ):
        return error("Each step needs an instruction and a supported action.")
    if any(not value or len(value) > limit for value, limit in (
        (subject, 100), (topic, 180), (objective, 2000)
    )):
        return error("subject, topic, and objective are required and must fit the story schema.")

    environment = (
        activity.simulation.get("scene", "classroom") if activity else "laboratory" if practical else "classroom"
    )
    try:
        blueprint, source = generate_story_blueprint(
            class_number=class_number,
            subject=subject,
            topic=topic,
            objective=objective,
            steps=steps,
            required_objects=required_objects,
            activity_kind=activity.activity_type if activity else "practical" if practical else "activity",
            environment=environment,
        )
        story = store_story(
            blueprint,
            source=source,
            status=ActivityStory.Status.DRAFT,
            activity=activity,
            practical=practical,
            teacher_prompt=str(data.get("teacher_prompt", ""))[:4000],
        )
    except StoryGenerationError as exc:
        return error(str(exc), 502)
    except ValueError as exc:
        return error(str(exc))
    return JsonResponse(story_payload(story), status=201)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAdminUser])
def publish_story(request, story_id):
    try:
        story = ActivityStory.objects.get(pk=story_id)
    except ActivityStory.DoesNotExist:
        return error("Story draft not found.", 404)
    if story.status != ActivityStory.Status.DRAFT:
        return error("Only draft stories can be approved and published.", 409)
    if not (story.activity_id or story.practical_id):
        return error("Assign this story to an activity or practical in the story editor before publishing.")
    try:
        validate_story_blueprint(stored_story_blueprint(story))
        story.status = ActivityStory.Status.PUBLISHED
        story.approved_at = timezone.now()
        story.save()
    except (StoryGenerationError, ValueError) as exc:
        return error(str(exc))
    return JsonResponse(story_payload(story))


def public_activity_step(step):
    return {key: value for key, value in step.items() if key not in {"value", "millilitres"}}


def advance_story_progress(progress, step_index, total_steps, completed=False):
    scenes = list(progress.story.scenes.all())
    if not scenes:
        return None
    target_index = len(scenes) - 1 if completed else min(
        len(scenes) - 2,
        4 + math.ceil(step_index / max(total_steps, 1) * 4),
    )
    target = scenes[target_index]
    progress.current_scene = target
    progress.completed_scenes = [scene.scene_id for scene in scenes[:target_index]]
    if completed:
        progress.status = PlayerStoryProgress.Status.COMPLETED
        progress.completed_scenes = [scene.scene_id for scene in scenes]
        progress.completed_at = timezone.now()
    progress.save(
        update_fields=["current_scene", "completed_scenes", "status", "completed_at", "updated_at"]
    )
    return target


def public_story_scene(scene):
    if not scene:
        return None
    return {
        "scene_id": scene.scene_id,
        "name": scene.name,
        "description": scene.description,
        "dialogues": [
            {
                "character": dialogue.character.name if dialogue.character else "Guide",
                "text": dialogue.text,
                "emotion": dialogue.emotion,
                "choices": dialogue.choices,
            }
            for dialogue in scene.dialogues.select_related("character").all()
        ],
        "animation_events": list(
            scene.animation_events.values("event_id", "trigger", "animation", "target", "configuration")
        ),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def room_detail(request, class_number, subject_slug):
    if class_number < 1 or class_number > 12:
        return error("class must be a number from 1 to 12.")
    if subject_slug == "library":
        subjects = []
        for subject in Subject.objects.filter(classes__number=class_number).distinct().prefetch_related("chapters"):
            chapter = subject.chapters.filter(class_level__number=class_number).first()
            subjects.append(
                {
                    "slug": subject.slug,
                    "name": subject.name,
                    "building": subject.building,
                    "syllabus_url": chapter.syllabus_url if chapter else "",
                    "activity_count": chapter.activities.count() if chapter else 0,
                }
            )
        return JsonResponse(
            {
                "class": class_number,
                "slug": "library",
                "name": "Campus Library",
                "room_type": "library",
                "subjects": subjects,
                "resources": [
                    {"title": "CBSE digital lessons · DIKSHA", "provider": "DIKSHA", "url": "https://diksha.gov.in/explore"},
                    {"title": "Free lessons · Khan Academy", "provider": "Khan Academy", "url": "https://www.khanacademy.org/"},
                    {"title": "CBSE syllabus directory", "provider": "StudiesToday", "url": "https://www.studiestoday.com/syllabus/67/cbse.html"},
                ],
            }
        )
    try:
        subject = Subject.objects.get(slug=subject_slug, classes__number=class_number)
    except Subject.DoesNotExist:
        return error("This learning room is not available in the selected class.", 404)
    chapters = list(
        Chapter.objects.filter(subject=subject, class_level__number=class_number).prefetch_related("activities")
    )
    return JsonResponse(
        {
            "class": class_number,
            "slug": subject.slug,
            "name": subject.name,
            "room_type": "laboratory" if subject.building.lower().endswith("laboratory") else "classroom",
            "building": subject.building,
            "chapters": [
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "syllabus_url": chapter.syllabus_url,
                    "activities": [
                        activity_summary(activity)
                        for activity in chapter.activities.all()
                    ],
                }
                for chapter in chapters
            ],
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def activities(request):
    class_number = request.GET.get("class", "10")
    query = LearningActivity.objects.select_related("chapter__class_level", "chapter__subject")
    query = query.filter(chapter__class_level__number=class_number)
    subject_slug = request.GET.get("subject")
    if subject_slug:
        query = query.filter(chapter__subject__slug=subject_slug)
    return JsonResponse({"activities": [activity_summary(activity) for activity in query]})


@api_view(["POST"])
@permission_classes([AllowAny])
def start_activity(request):
    try:
        data = read_json(request)
        learner_id = player_id_for(request, data)
    except ValueError as exc:
        return error(str(exc))
    except IdentityError as exc:
        return identity_error_response(exc)
    try:
        learner = Learner.objects.get(player_id=learner_id)
        activity = LearningActivity.objects.select_related("chapter__class_level").get(
            slug=data.get("activity_slug", "")
        )
    except Learner.DoesNotExist:
        return error("Create a student profile before starting an activity.", 404)
    except LearningActivity.DoesNotExist:
        return error("Learning activity not found.", 404)
    if learner.class_level_id != activity.chapter.class_level_id:
        return error("This activity is not available for the selected class.", 403)
    if not activity.instructions:
        return error("This learning activity has no configured steps.", 409)
    attempt = ActivityAttempt.objects.create(learner=learner, activity=activity)
    story = activity.stories.filter(status=ActivityStory.Status.PUBLISHED).order_by("-generated_at").first()
    if story:
        PlayerStoryProgress.objects.create(
            learner=learner,
            story=story,
            activity_attempt=attempt,
            current_scene=story.scenes.first(),
        )
    return JsonResponse(
        {
            "attempt_id": str(attempt.attempt_id),
            "activity": activity_summary(activity),
            "step_index": 0,
            "current_step": public_activity_step(activity.instructions[0]),
            "story": story_payload(story),
        },
        status=201,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def activity_action(request, attempt_id):
    try:
        data = read_json(request)
        learner_id = player_id_for(request, data)
    except ValueError as exc:
        return error(str(exc))
    except IdentityError as exc:
        return identity_error_response(exc)

    with transaction.atomic():
        try:
            attempt = ActivityAttempt.objects.select_for_update().select_related(
                "activity", "learner"
            ).get(attempt_id=attempt_id, learner_id=learner_id)
        except ActivityAttempt.DoesNotExist:
            return error("Learning activity attempt not found.", 404)
        if attempt.status != ActivityAttempt.Status.IN_PROGRESS:
            return error("This learning activity is no longer accepting actions.", 409)

        steps = attempt.activity.instructions
        if attempt.step_index >= len(steps):
            return error("The learning activity steps are already complete.", 409)
        step = steps[attempt.step_index]
        action = data.get("action")
        payload = data.get("payload", {})
        if action != step.get("action") or not isinstance(payload, dict):
            return error("Complete the current activity instruction before moving on.", 409)

        state = attempt.observations
        expected_item = step.get("item")
        if action == "pick":
            if payload.get("item") != expected_item:
                return error("Pick the item named in the current instruction.", 400)
            state.setdefault("picked", [])
            if expected_item not in state["picked"]:
                state["picked"].append(expected_item)
        elif action == "place":
            if expected_item not in state.get("picked", []):
                return error("Pick up the item before placing it on the workbench.", 409)
            state.setdefault("placed", [])
            if expected_item not in state["placed"]:
                state["placed"].append(expected_item)
        elif action == "pour":
            if expected_item not in state.get("picked", []) or payload.get("item") != expected_item:
                return error("Pick the virtual sample before pouring it.", 409)
            try:
                volume = int(payload.get("millilitres"))
            except (TypeError, ValueError):
                return error("Enter the virtual volume in millilitres.")
            if not 1 <= volume <= 50 or volume != step.get("millilitres"):
                return error(f"Measure exactly {step.get('millilitres')} mL for this simulation.")
            state["poured_ml"] = volume
        elif action == "mix":
            if not state.get("poured_ml"):
                return error("Pour the virtual sample before mixing it.", 409)
            if payload.get("method") != step.get("method"):
                return error("Use the mixing method shown in the instruction.")
            state["mixed"] = True
        elif action in {"measure", "weigh", "calculate"}:
            try:
                value = float(payload.get("value"))
            except (TypeError, ValueError):
                return error("Enter the value shown by the virtual activity.")
            if value != float(step.get("value")) or payload.get("unit", step.get("unit")) != step.get("unit"):
                return error("Check the virtual reading and try again.")
            state[action] = {"value": value, "unit": step.get("unit", "")}
        elif action in {"sort", "assemble", "read", "draw", "observe", "record"}:
            if expected_item and payload.get("item") != expected_item:
                return error("Complete the task described by the current instruction.")
            if payload.get("completed") is not True:
                return error("Confirm the current activity step when it is complete.")
            state.setdefault("completed_actions", []).append(action)
        else:
            return error("Unsupported learning activity action.", 400)

        attempt.observations = state
        attempt.step_index += 1
        is_complete = attempt.step_index == len(steps)
        response_data = {"step_index": attempt.step_index, "status": ActivityAttempt.Status.IN_PROGRESS}
        story_progress = getattr(attempt, "story_progress", None)
        if story_progress:
            scene = advance_story_progress(story_progress, attempt.step_index, len(steps))
            response_data["story_scene"] = public_story_scene(scene)
        if is_complete:
            attempt.status = ActivityAttempt.Status.QUIZ
            response_data["status"] = attempt.status
        else:
            response_data["current_step"] = public_activity_step(steps[attempt.step_index])
        attempt.save(update_fields=["observations", "step_index", "status", "completed_at"])
        return JsonResponse(response_data)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def activity_quiz(request, attempt_id):
    try:
        data = read_json(request) if request.method == "POST" else {}
        learner_id = player_id_for(request, data)
    except ValueError as exc:
        return error(str(exc))
    except IdentityError as exc:
        return identity_error_response(exc)

    with transaction.atomic():
        try:
            attempt = ActivityAttempt.objects.select_for_update().select_related(
                "activity", "learner"
            ).get(attempt_id=attempt_id, learner_id=learner_id)
        except ActivityAttempt.DoesNotExist:
            return error("Learning activity attempt not found.", 404)
        if attempt.status not in (ActivityAttempt.Status.QUIZ, ActivityAttempt.Status.COMPLETED):
            return error("Complete the activity steps before starting its quiz.", 409)

        questions = list(attempt.activity.questions.all())
        if not questions:
            return error("This activity does not have a configured quiz.", 409)
        if request.method == "GET":
            return JsonResponse(
                {
                    "questions": [
                        {
                            "id": question.id,
                            "difficulty": question.difficulty,
                            "prompt": question.prompt,
                            "options": question.options,
                        }
                        for question in questions
                    ]
                }
            )
        if attempt.status == ActivityAttempt.Status.COMPLETED:
            return error("This activity quiz has already been submitted.", 409)

        answers = data.get("answers")
        if not isinstance(answers, list) or len(answers) != len(questions):
            return error(f"Submit exactly {len(questions)} answers, one for each difficulty level.")

        results = []
        correct_count = 0
        for question, answer in zip(questions, answers):
            if not isinstance(answer, dict) or answer.get("question_id") != question.id:
                return error("Answers must match the quiz questions in order.")
            try:
                selected = int(answer.get("selected_option"))
            except (TypeError, ValueError):
                return error("Each answer must select one of the displayed options.")
            if selected < 0 or selected >= len(question.options):
                return error("The selected quiz option is out of range.")
            correct = selected == question.correct_option
            correct_count += int(correct)
            results.append(
                {
                    "question_id": question.id,
                    "difficulty": question.difficulty,
                    "correct": correct,
                    "correct_option": question.correct_option,
                    "explanation": question.explanation,
                }
            )

        score = math.floor(correct_count * 100 / len(questions))
        xp_awarded = 20 + (10 if score >= 80 else 0)
        coins_awarded = 3 + (2 if score == 100 else 0)
        attempt.status = ActivityAttempt.Status.COMPLETED
        attempt.quiz_answers = answers
        attempt.score = score
        attempt.xp_awarded = xp_awarded
        attempt.coins_awarded = coins_awarded
        attempt.completed_at = timezone.now()
        attempt.save(
            update_fields=[
                "status",
                "quiz_answers",
                "score",
                "xp_awarded",
                "coins_awarded",
                "completed_at",
            ]
        )
        learner = Learner.objects.select_for_update().get(player_id=learner_id)
        learner.xp += xp_awarded
        learner.coins += coins_awarded
        learner.save(update_fields=["xp", "coins", "updated_at"])
        story_ending = None
        story_progress = getattr(attempt, "story_progress", None)
        if story_progress:
            ending_scene = advance_story_progress(
                story_progress,
                len(attempt.activity.instructions),
                len(attempt.activity.instructions),
                completed=True,
            )
            story_ending = public_story_scene(ending_scene)

    return JsonResponse(
        {
            "score": score,
            "correct_count": correct_count,
            "total_questions": len(questions),
            "results": results,
            "reward": {"xp": xp_awarded, "coins": coins_awarded},
            "player": player_payload(learner),
            "story_ending": story_ending,
        }
    )


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def players(request):
    try:
        data = read_json(request) if request.method == "POST" else {}
        player_id = player_id_for(request, data)
    except ValueError as exc:
        return error(str(exc))
    except IdentityError as exc:
        return identity_error_response(exc)

    if request.method == "GET":
        try:
            learner = Learner.objects.select_related("class_level").get(player_id=player_id)
        except Learner.DoesNotExist:
            return error("Player profile not found.", 404)
        return JsonResponse(player_payload(learner))

    name = str(data.get("display_name", "Student")).strip()[:40]
    try:
        class_number = int(data.get("class", 10))
        class_level = ClassLevel.objects.get(number=class_number)
    except (TypeError, ValueError):
        return error("class must be a number from 1 to 12.")
    except ClassLevel.DoesNotExist:
        return error("class must be a number from 1 to 12.")
    if not name:
        return error("display_name cannot be empty.")

    learner, _ = Learner.objects.update_or_create(
        player_id=player_id,
        defaults={"display_name": name, "class_level": class_level},
    )
    return JsonResponse(player_payload(learner), status=201)


def player_payload(learner):
    return {
        "player_id": str(learner.player_id),
        "display_name": learner.display_name,
        "class": learner.class_level.number,
        "xp": learner.xp,
        "coins": learner.coins,
        "level": learner.xp // 100 + 1,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def practicals(request):
    class_number = request.GET.get("class", "10")
    query = Practical.objects.select_related("chapter__class_level", "chapter__subject")
    query = query.filter(chapter__class_level__number=class_number)
    subject_slug = request.GET.get("subject")
    if subject_slug:
        query = query.filter(chapter__subject__slug=subject_slug)
    return JsonResponse(
        {
            "practicals": [
                {
                    "slug": practical.slug,
                    "title": practical.title,
                    "chapter": practical.chapter.title,
                    "subject": practical.chapter.subject.name,
                    "difficulty": practical.difficulty,
                    "estimated_minutes": practical.estimated_minutes,
                }
                for practical in query.order_by("id")
            ]
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def practical_detail(request, slug):
    try:
        practical = Practical.objects.select_related("chapter__class_level", "chapter__subject").get(slug=slug)
    except Practical.DoesNotExist:
        return error("Practical not found.", 404)
    return JsonResponse(practical_payload(practical))


@api_view(["POST"])
@permission_classes([AllowAny])
def start_attempt(request):
    try:
        data = read_json(request)
        learner_id = player_id_for(request, data)
    except ValueError as exc:
        return error(str(exc))
    except IdentityError as exc:
        return identity_error_response(exc)

    slug = data.get("practical_slug", "test-ph-solutions")
    try:
        learner = Learner.objects.get(player_id=learner_id)
        practical = Practical.objects.select_related("chapter__class_level").get(slug=slug)
    except Learner.DoesNotExist:
        return error("Create a student profile before starting a practical.", 404)
    except Practical.DoesNotExist:
        return error("Practical not found.", 404)
    if learner.class_level_id != practical.chapter.class_level_id:
        return error("This practical is not available for the selected class.", 403)
    attempt = PracticalAttempt.objects.create(learner=learner, practical=practical)
    story = practical.stories.filter(status=ActivityStory.Status.PUBLISHED).order_by("-generated_at").first()
    if story:
        PlayerStoryProgress.objects.create(
            learner=learner,
            story=story,
            practical_attempt=attempt,
            current_scene=story.scenes.first(),
        )
    return JsonResponse(
        {
            "attempt_id": str(attempt.attempt_id),
            "status": attempt.status,
            "practical": practical_payload(practical),
            "story": story_payload(story),
        },
        status=201,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def attempt_action(request, attempt_id):
    try:
        data = read_json(request)
        learner_id = player_id_for(request, data)
    except ValueError as exc:
        return error(str(exc))
    except IdentityError as exc:
        return identity_error_response(exc)

    try:
        with transaction.atomic():
            attempt = owned_attempt(attempt_id, learner_id)
            if attempt is None:
                return error("Practical attempt not found.", 404)
            if attempt.status != PracticalAttempt.Status.IN_PROGRESS:
                return error("This practical is no longer accepting experiment actions.", 409)

            steps = list(attempt.practical.steps.prefetch_related("equipment").all())
            if attempt.step_index >= len(steps):
                return error("The practical steps are already complete.", 409)
            step = steps[attempt.step_index]
            action = data.get("action")
            payload = data.get("payload", {})
            if action != step.action or not isinstance(payload, dict):
                return error("That action does not match the current practical step.", 409)

            observation = attempt.observations
            response_data = {"message": "Step complete.", "step_index": attempt.step_index + 1}
            if action == "collect_equipment":
                required = set(step.equipment.values_list("slug", flat=True))
                supplied = payload.get("equipment", [])
                if not isinstance(supplied, list) or not required.issubset(set(supplied)):
                    return error("Collect all required virtual safety and experiment equipment first.", 400)
                observation["equipment_collected"] = sorted(required)
            elif action == "place_object":
                required = set(step.equipment.values_list("slug", flat=True))
                item = payload.get("item")
                if not required.issubset(set(observation.get("equipment_collected", []))):
                    return error("Pick up the required virtual equipment before placing it.", 409)
                if item not in required or payload.get("target") != "workbench":
                    return error("Place the requested instrument on the virtual workbench.", 400)
                observation.setdefault("placed", [])
                if item not in observation["placed"]:
                    observation["placed"].append(item)
            elif action == "choose_sample":
                sample_slug = payload.get("sample")
                sample = sample_by_slug(attempt.practical, sample_slug)
                if not sample:
                    return error("Choose a sample listed for this practical.", 400)
                observation["sample_slug"] = sample_slug
                observation.pop("test_result", None)
            elif action == "pour_liquid":
                sample = sample_by_slug(attempt.practical, observation.get("sample_slug"))
                required = set(step.equipment.values_list("slug", flat=True))
                if not sample or "test-tube" not in observation.get("placed", []):
                    return error("Place the test tube and select a virtual sample before pouring.", 409)
                if not required.issubset(set(observation.get("equipment_collected", []))):
                    return error("Pick up the dropper and beaker before pouring.", 409)
                try:
                    volume = int(payload.get("millilitres"))
                except (TypeError, ValueError):
                    return error("Enter the virtual volume in millilitres.")
                if volume != 10:
                    return error("Measure exactly 10 mL for this virtual test.")
                observation["poured_ml"] = volume
            elif action == "mix":
                required = set(step.equipment.values_list("slug", flat=True))
                if not observation.get("poured_ml"):
                    return error("Pour the virtual sample before mixing it.", 409)
                if not required.issubset(set(observation.get("equipment_collected", []))):
                    return error("Pick up the virtual glass rod before mixing.", 409)
                if payload.get("method") != "swirl":
                    return error("Gently swirl the virtual sample as instructed.")
                observation["mixed"] = True
            elif action == "test_indicator":
                sample = sample_by_slug(attempt.practical, observation.get("sample_slug"))
                if not sample or not observation.get("mixed"):
                    return error("Select, pour, and gently mix a virtual sample before testing it.", 409)
                if "indicator-paper" not in observation.get("equipment_collected", []):
                    return error("Pick up the virtual indicator paper before testing the sample.", 409)
                result = {
                    "ph": sample["ph"],
                    "category": sample["category"],
                    "color": sample["color"],
                }
                observation["test_result"] = result
                response_data["result"] = result
            elif action == "measure_ph":
                result = observation.get("test_result")
                if not result:
                    return error("Use the indicator before reading the pH chart.", 409)
                try:
                    measured_ph = int(payload.get("ph"))
                except (TypeError, ValueError):
                    return error("Enter the pH value shown by the virtual chart.")
                if measured_ph != result["ph"]:
                    return error("That pH reading does not match the virtual indicator chart.")
                observation["measured_ph"] = measured_ph
            elif action == "record_observation":
                result = observation.get("test_result")
                if not result or observation.get("measured_ph") is None:
                    return error("Test the sample and measure its pH before recording a result.", 409)
                try:
                    observed_ph = int(payload.get("ph"))
                except (TypeError, ValueError):
                    return error("Record the pH shown by the indicator chart.")
                if observed_ph != observation["measured_ph"] or observed_ph != result["ph"] or payload.get("category") != result["category"]:
                    return error("That observation does not match the indicator result. Review the chart and try again.")
                observation["recorded"] = {"ph": observed_ph, "category": result["category"]}
            else:
                return error("Unsupported practical action.", 400)

            attempt.observations = observation
            attempt.step_index += 1
            story_progress = getattr(attempt, "story_progress", None)
            if story_progress:
                scene = advance_story_progress(story_progress, attempt.step_index, len(steps))
                response_data["story_scene"] = public_story_scene(scene)
            if attempt.step_index == len(steps):
                attempt.status = PracticalAttempt.Status.QUIZ
                response_data["status"] = attempt.status
            attempt.save(update_fields=["observations", "step_index", "status"])
            return JsonResponse(response_data)
    except PracticalStep.DoesNotExist:
        return error("Practical steps are not configured.", 500)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def attempt_quiz(request, attempt_id):
    try:
        data = read_json(request) if request.method == "POST" else {}
        learner_id = player_id_for(request, data)
    except ValueError as exc:
        return error(str(exc))
    except IdentityError as exc:
        return identity_error_response(exc)

    attempt = owned_attempt(attempt_id, learner_id)
    if attempt is None:
        return error("Practical attempt not found.", 404)
    if attempt.status not in (PracticalAttempt.Status.QUIZ, PracticalAttempt.Status.COMPLETED):
        return error("Complete the experiment and record an observation before the quiz.", 409)

    questions = list(attempt.practical.questions.all())
    if request.method == "GET":
        return JsonResponse(
            {
                "questions": [
                    {
                        "id": question.id,
                        "difficulty": question.difficulty,
                        "prompt": question.prompt,
                        "options": question.options,
                    }
                    for question in questions
                ]
            }
        )
    if attempt.status == PracticalAttempt.Status.COMPLETED:
        return error("This quiz has already been submitted.", 409)

    answers = data.get("answers")
    if not isinstance(answers, list) or len(answers) != len(questions):
        return error(f"Submit exactly {len(questions)} answers, one for each difficulty level.")

    results = []
    correct_count = 0
    for index, (question, answer) in enumerate(zip(questions, answers)):
        if not isinstance(answer, dict) or answer.get("question_id") != question.id:
            return error("Answers must match the quiz questions in order.")
        try:
            selected = int(answer.get("selected_option"))
        except (TypeError, ValueError):
            return error("Each answer must select one of the displayed options.")
        if selected < 0 or selected >= len(question.options):
            return error("The selected quiz option is out of range.")
        correct = selected == question.correct_option
        correct_count += int(correct)
        results.append(
            {
                "question_id": question.id,
                "difficulty": question.difficulty,
                "correct": correct,
                "correct_option": question.correct_option,
                "explanation": question.explanation,
            }
        )

    score = math.floor(correct_count * 100 / len(questions)) if questions else 0
    base_xp = 70
    bonus_xp = 30 if score >= 80 else 0
    coins = 10 + (5 if score == 100 else 0)
    with transaction.atomic():
        attempt = PracticalAttempt.objects.select_for_update().get(attempt_id=attempt_id, learner_id=learner_id)
        if attempt.status == PracticalAttempt.Status.COMPLETED:
            return error("This quiz has already been submitted.", 409)
        attempt.status = PracticalAttempt.Status.COMPLETED
        attempt.quiz_answers = answers
        attempt.score = score
        attempt.xp_awarded = base_xp + bonus_xp
        attempt.coins_awarded = coins
        attempt.completed_at = timezone.now()
        attempt.save(
            update_fields=[
                "status",
                "quiz_answers",
                "score",
                "xp_awarded",
                "coins_awarded",
                "completed_at",
            ]
        )
        learner = Learner.objects.select_for_update().get(player_id=learner_id)
        learner.xp += attempt.xp_awarded
        learner.coins += attempt.coins_awarded
        learner.save(update_fields=["xp", "coins", "updated_at"])
        story_ending = None
        story_progress = getattr(attempt, "story_progress", None)
        if story_progress:
            ending_scene = advance_story_progress(
                story_progress,
                len(attempt.practical.steps.all()),
                len(attempt.practical.steps.all()),
                completed=True,
            )
            story_ending = public_story_scene(ending_scene)

    return JsonResponse(
        {
            "score": score,
            "correct_count": correct_count,
            "total_questions": len(questions),
            "results": results,
            "reward": {"xp": attempt.xp_awarded, "coins": attempt.coins_awarded},
            "player": player_payload(learner),
            "story_ending": story_ending,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def progress(request):
    try:
        learner_id = player_id_for(request)
    except IdentityError as exc:
        return identity_error_response(exc)
    try:
        learner = Learner.objects.select_related("class_level").get(player_id=learner_id)
    except Learner.DoesNotExist:
        return error("Player profile not found.", 404)

    completed = learner.attempts.filter(status=PracticalAttempt.Status.COMPLETED)
    attempts = [
        {
            "attempt_id": str(attempt.attempt_id),
            "practical": attempt.practical.title,
            "score": attempt.score,
            "xp": attempt.xp_awarded,
            "completed_at": attempt.completed_at,
        }
        for attempt in completed.select_related("practical")[:20]
    ]
    return JsonResponse(
        {
            "player": player_payload(learner),
            "completed_practicals": completed.count(),
            "attempts": attempts,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def assistant(request):
    try:
        data = read_json(request)
    except ValueError as exc:
        return error(str(exc))
    question = str(data.get("question", "")).strip()
    if not question:
        return error("Ask a question to get a learning hint.")
    text = question.lower()
    if "acid" in text or "base" in text or "ph" in text or "indicator" in text:
        answer = (
            "The pH scale helps compare how acidic or basic a solution is. "
            "Values below 7 are acidic, 7 is neutral, and values above 7 are basic. "
            "An indicator changes colour; use the chart to connect that colour to a pH reading."
        )
    else:
        answer = (
            "Try linking what you observed to the learning objective. "
            "For this virtual practical, use the indicator colour chart and record the result before the quiz."
        )
    return JsonResponse({"answer": answer, "mode": "offline-fallback"})

