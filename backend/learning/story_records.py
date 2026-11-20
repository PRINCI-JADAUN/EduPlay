from django.utils import timezone

from .models import (
    ActivityStory,
    AnimationEvent,
    MissionObjective,
    SceneTransition,
    StoryBranch,
    StoryCharacter,
    StoryDialogue,
    StoryMission,
    StoryReward,
    StoryScene,
)
from .story_engine import generate_story_blueprint, validate_story_blueprint


def store_story(blueprint, *, source, status, activity=None, practical=None, teacher_prompt=""):
    validate_story_blueprint(blueprint)
    if activity and practical or not (activity or practical) and status != ActivityStory.Status.DRAFT:
        raise ValueError("A story must be attached to one activity or practical before it is published.")
    parent = activity or practical
    story = None
    if parent:
        parent_field = "activity" if activity else "practical"
        story = (
            ActivityStory.objects.filter(
                **{parent_field: parent, "generation_source": source, "status": status}
            )
            .order_by("-generated_at")
            .first()
        )
    story_fields = {
        "activity": activity,
        "practical": practical,
        "title": blueprint["title"],
        "introduction": blueprint["introduction"],
        "background": blueprint["background"],
        "main_character": blueprint["main_character"],
        "problem": blueprint["problem"],
        "educational_explanation": blueprint["mission"]["educational_explanation"],
        "ending": blueprint["ending"],
        "status": status,
        "generation_source": source,
        "teacher_prompt": teacher_prompt,
        "approved_at": timezone.now() if status == ActivityStory.Status.PUBLISHED else None,
    }
    if story is None:
        story = ActivityStory.objects.create(**story_fields)
    else:
        for field, value in story_fields.items():
            setattr(story, field, value)
        story.save()
        story.transitions.all().delete()
        story.scenes.all().delete()
        story.characters.all().delete()
        if hasattr(story, "mission"):
            story.mission.delete()
        if hasattr(story, "reward"):
            story.reward.delete()

    characters = {
        character["character_id"]: StoryCharacter.objects.create(
            story=story,
            character_id=character["character_id"],
            name=character["name"],
            role=character["role"],
            description=character["description"],
            appearance=character["appearance"],
            dialogue_style=character["dialogue_style"],
            is_player=character["is_player"],
            order=index + 1,
        )
        for index, character in enumerate(blueprint["characters"])
    }
    scenes = {}
    for sequence, scene in enumerate(blueprint["scenes"], start=1):
        scenes[scene["scene_id"]] = StoryScene.objects.create(
            story=story,
            scene_id=scene["scene_id"],
            name=scene["name"],
            sequence=sequence,
            environment=scene["environment"],
            description=scene["description"],
            required_objects=scene["required_objects"],
            player_controls=scene["player_controls"],
            trigger_condition=scene["trigger_condition"],
            completion_condition=scene["completion_condition"],
            next_scene_id=scene["next_scene_id"],
        )
    for scene_data in blueprint["scenes"]:
        scene = scenes[scene_data["scene_id"]]
        for order, dialogue in enumerate(scene_data["dialogues"], start=1):
            StoryDialogue.objects.create(
                scene=scene,
                character=characters[dialogue["character_id"]],
                order=order,
                text=dialogue["text"],
                emotion=dialogue["emotion"],
                choices=dialogue["choices"],
            )
        for event in scene_data["animation_events"]:
            AnimationEvent.objects.create(scene=scene, **event)
        if scene_data["next_scene_id"]:
            SceneTransition.objects.create(
                story=story,
                from_scene_id=scene.scene_id,
                to_scene_id=scene_data["next_scene_id"],
                trigger_condition=scene_data["completion_condition"],
            )
        for branch in scene_data["branches"]:
            StoryBranch.objects.get_or_create(scene=scene, branch_id=branch["branch_id"], defaults=branch)

    mission_data = blueprint["mission"]
    mission = StoryMission.objects.create(
        story=story,
        title=mission_data["title"],
        problem=mission_data["problem"],
        final_challenge=mission_data["final_challenge"],
        educational_explanation=mission_data["educational_explanation"],
    )
    for order, objective in enumerate(mission_data["objectives"], start=1):
        MissionObjective.objects.create(mission=mission, order=order, **objective)
    StoryReward.objects.create(story=story, **blueprint["reward"])
    return story


def create_activity_story(activity, *, status=ActivityStory.Status.PUBLISHED):
    class_number = activity.chapter.class_level.number
    subject = activity.chapter.subject.name
    steps = activity.instructions
    blueprint, source = generate_story_blueprint(
        class_number=class_number,
        subject=subject,
        topic=activity.title,
        objective=activity.objective,
        steps=steps,
        required_objects=activity.simulation.get("items", []),
        activity_kind=activity.activity_type,
        environment=activity.simulation.get("scene", "classroom"),
    )
    if source == "configured-ai" and status == ActivityStory.Status.PUBLISHED:
        status = ActivityStory.Status.DRAFT
    return store_story(blueprint, source=source, status=status, activity=activity)


def create_practical_story(practical, *, status=ActivityStory.Status.PUBLISHED):
    class_number = practical.chapter.class_level.number
    subject = practical.chapter.subject.name
    step_data = list(practical.steps.order_by("order"))
    steps = [{"instruction": step.instruction, "action": step.action} for step in step_data]
    equipment = sorted({item.name for step in step_data for item in step.equipment.all()})
    samples = [sample["name"] for sample in practical.samples]
    blueprint, source = generate_story_blueprint(
        class_number=class_number,
        subject=subject,
        topic=practical.title,
        objective=practical.objective,
        steps=steps,
        required_objects=equipment + samples,
        activity_kind="practical",
        environment="laboratory",
    )
    if source == "configured-ai" and status == ActivityStory.Status.PUBLISHED:
        status = ActivityStory.Status.DRAFT
    blueprint["reward"]["xp"] = 70
    blueprint["reward"]["coins"] = 10
    return store_story(blueprint, source=source, status=status, practical=practical)


def story_payload(story):
    if not story:
        return None
    scenes = []
    for scene in story.scenes.prefetch_related("dialogues__character", "animation_events", "branches").all():
        scenes.append(
            {
                "scene_id": scene.scene_id,
                "name": scene.name,
                "environment": scene.environment,
                "description": scene.description,
                "required_objects": scene.required_objects,
                "player_controls": scene.player_controls,
                "trigger_condition": scene.trigger_condition,
                "completion_condition": scene.completion_condition,
                "next_scene_id": scene.next_scene_id,
                "dialogues": [
                    {
                        "character_id": dialogue.character.character_id if dialogue.character else "",
                        "character": dialogue.character.name if dialogue.character else "Guide",
                        "text": dialogue.text,
                        "emotion": dialogue.emotion,
                        "choices": dialogue.choices,
                    }
                    for dialogue in scene.dialogues.all()
                ],
                "animation_events": [
                    {
                        "event_id": event.event_id,
                        "trigger": event.trigger,
                        "animation": event.animation,
                        "target": event.target,
                        "configuration": event.configuration,
                    }
                    for event in scene.animation_events.all()
                ],
                "branches": [
                    {"branch_id": branch.branch_id, "prompt": branch.prompt, "choices": branch.choices}
                    for branch in scene.branches.all()
                ],
            }
        )
    mission = story.mission
    reward = story.reward
    return {
        "id": story.id,
        "version": 1,
        "status": story.status,
        "generation_source": story.generation_source,
        "title": story.title,
        "introduction": story.introduction,
        "background": story.background,
        "main_character": story.main_character,
        "problem": story.problem,
        "ending": story.ending,
        "characters": [
            {
                "character_id": character.character_id,
                "name": character.name,
                "role": character.role,
                "description": character.description,
                "appearance": character.appearance,
                "dialogue_style": character.dialogue_style,
                "is_player": character.is_player,
            }
            for character in story.characters.all()
        ],
        "mission": {
            "title": mission.title,
            "problem": mission.problem,
            "final_challenge": mission.final_challenge,
            "educational_explanation": mission.educational_explanation,
            "objectives": [
                {
                    "title": objective.title,
                    "expected_action": objective.expected_action,
                    "completion_condition": objective.completion_condition,
                }
                for objective in mission.objectives.all()
            ],
        },
        "scenes": scenes,
        "reward": {
            "xp": reward.xp,
            "coins": reward.coins,
            "badge_name": reward.badge_name,
            "unlocks_story_slug": reward.unlocks_story_slug,
        },
    }


def story_context_for_activity(activity):
    return {
        "class_number": activity.chapter.class_level.number,
        "subject": activity.chapter.subject.name,
        "topic": activity.title,
        "objective": activity.objective,
        "steps": activity.instructions,
        "required_objects": activity.simulation.get("items", []),
        "activity_kind": activity.activity_type,
        "environment": activity.simulation.get("scene", "classroom"),
    }


def stored_story_blueprint(story):
    payload = story_payload(story)
    if payload is None or not story.scenes.exists() or not story.characters.exists():
        raise ValueError("A story needs characters and scenes before it can be approved.")
    if not hasattr(story, "mission") or not hasattr(story, "reward"):
        raise ValueError("A story needs a mission and reward before it can be approved.")
    scenes = payload["scenes"]
    for scene in scenes:
        scene["dialogues"] = [
            {
                key: dialogue[key]
                for key in ("character_id", "text", "emotion", "choices")
            }
            for dialogue in scene["dialogues"]
        ]
    return {
        "version": payload["version"],
        "title": payload["title"],
        "introduction": payload["introduction"],
        "background": payload["background"],
        "main_character": payload["main_character"],
        "characters": payload["characters"],
        "problem": payload["problem"],
        "mission": payload["mission"],
        "scenes": scenes,
        "ending": payload["ending"],
        "reward": payload["reward"],
    }
