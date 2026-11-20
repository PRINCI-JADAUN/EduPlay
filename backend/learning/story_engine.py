import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


ALLOWED_ACTIONS = {
    "pick",
    "place",
    "pour",
    "mix",
    "measure",
    "weigh",
    "calculate",
    "sort",
    "assemble",
    "read",
    "draw",
    "observe",
    "record",
    "continue",
    "interact",
    "choose",
    "collect_equipment",
    "place_object",
    "choose_sample",
    "pour_liquid",
    "test_indicator",
    "measure_ph",
    "record_observation",
}
ALLOWED_ANIMATIONS = {
    "fade_in",
    "camera_pan",
    "wave",
    "point",
    "pickup",
    "place",
    "walk",
    "think",
    "celebrate",
    "glow",
}
ALLOWED_ENVIRONMENTS = {
    "classroom",
    "laboratory",
    "garden",
    "forest",
    "space",
    "workshop",
    "library",
    "field",
    "market",
    "city",
    "digital_world",
}
SCENE_NAMES = [
    ("cinematic-intro", "A New Day Begins", "fade_in"),
    ("meet-the-guide", "Meet Your Guide", "wave"),
    ("discover-the-problem", "A Curious Problem", "think"),
    ("mission-briefing", "Mission Briefing", "point"),
    ("exploration", "Explore the World", "camera_pan"),
    ("object-collection", "Gather Your Tools", "pickup"),
    ("practical-execution", "Learn by Doing", "glow"),
    ("concept-challenge", "Put the Idea to Work", "think"),
    ("final-mission", "The Final Challenge", "celebrate"),
    ("story-resolution", "A Discovery to Remember", "celebrate"),
]


class StoryGenerationError(ValueError):
    pass


def _age_design(class_number, subject):
    if class_number <= 2:
        return (
            "The Wonder Garden",
            "Pip the talking compass",
            "a friendly animal guide",
            "Use short, cheerful sentences and a small, safe discovery.",
        )
    if class_number <= 5:
        return (
            "The Curiosity Trail",
            "Riya the young explorer",
            "a curious field naturalist",
            "Use an exploration mystery and a clear, hands-on clue.",
        )
    if class_number <= 8:
        return (
            "The Discovery Expedition",
            "Dr. Noor, a patient research mentor",
            "a fellow student investigator",
            "Use a realistic investigation or design challenge.",
        )
    if class_number <= 10:
        return (
            "The Evidence Mission",
            "Asha, a student research lead",
            "a laboratory or engineering mentor",
            "Use evidence-based reasoning and a realistic, safe scenario.",
        )
    return (
        f"The {subject} Research Initiative",
        "Dr. Sen, a senior research mentor",
        "a specialist collaborator",
        "Use an advanced research, engineering, or decision-making scenario.",
    )


def _make_template(context):
    class_number = context["class_number"]
    subject = context["subject"]
    topic = context["topic"]
    objective = context["objective"]
    steps = context["steps"]
    objects = context["required_objects"]
    setting, guide, supporting_role, style = _age_design(class_number, subject)
    title = f"{setting}: {topic}"
    is_young = class_number <= 2
    opening = (
        f"{guide} invites you to help with {topic}. "
        f"Your discovery will help the whole community."
        if is_young
        else f"You join {guide} at {setting.lower()}, where a new challenge depends on understanding {topic}."
    )
    problem = (
        f"The team has noticed a question about {topic}: {objective} "
        "They need a careful observation, not a guess."
    )
    scene_dialogue = [
        f"Welcome, explorer! Today we will discover {topic} together."
        if is_young
        else f"Welcome to the mission. We need evidence about {topic}, and your investigation will guide our next decision.",
        f"Our question is: {objective}",
        "Let's use the evidence from each step before we decide what it means.",
        f"Mission rule: {objective}",
        "Look around the scene and identify what could help answer the question.",
        f"Collect only the tools needed for this investigation: {', '.join(objects[:4]) or 'your observation tools'}.",
        f"Follow the procedure carefully. First: {steps[0] if steps else objective}",
        "Pause and explain which observation supports your idea.",
        f"Final challenge: {steps[-1] if steps else objective}",
        f"You completed the investigation. Remember: {objective}",
    ]
    scenes = []
    for index, (scene_id, name, animation) in enumerate(SCENE_NAMES):
        controls = ["continue"] if index < 5 or index > 8 else ["interact", *sorted(ALLOWED_ACTIONS.intersection(
            step.get("action", "") for step in context["steps_data"]
        ))]
        required = objects[:4] if index == 5 else []
        if index == 6:
            required = objects
        scenes.append(
            {
                "scene_id": scene_id,
                "name": name,
                "environment": context["environment"],
                "description": scene_dialogue[index],
                "required_objects": required,
                "player_controls": controls,
                "trigger_condition": {"event": "attempt_start" if index == 0 else "scene_complete", "scene_index": index},
                "completion_condition": {"event": "continue" if index in {0, 1, 2, 3, 4, 9} else "objective_progress"},
                "next_scene_id": SCENE_NAMES[index + 1][0] if index + 1 < len(SCENE_NAMES) else "",
                "dialogues": [
                    {
                        "character_id": "guide",
                        "text": scene_dialogue[index],
                        "emotion": "curious" if index in {2, 7} else "encouraging",
                        "choices": (
                            [
                                {"label": "Show me a hint", "reply": "Use the objective and current instruction to choose your next action."},
                                {"label": "I will investigate", "reply": "Great. Look closely, follow the procedure, and record what the evidence shows."},
                            ]
                            if index == 1
                            else []
                        ),
                    }
                ],
                "animation_events": [
                    {
                        "event_id": f"{scene_id}-enter",
                        "trigger": "scene_enter",
                        "animation": animation,
                        "target": "guide" if animation in {"wave", "point", "think", "celebrate"} else "camera",
                        "configuration": {"duration_ms": 650},
                    }
                ],
                "branches": (
                    [
                        {
                            "branch_id": "guide-hint",
                            "prompt": "How would you like to continue?",
                            "choices": [
                                {"label": "Show me a hint", "reply": "Use the objective and current instruction to choose your next action."},
                                {"label": "I will investigate", "reply": "Great. Look closely and use evidence."},
                            ],
                        }
                    ]
                    if index == 1
                    else []
                ),
            }
        )

    objectives = [
        {
            "title": step["instruction"],
            "expected_action": step.get("action", ""),
            "completion_condition": {"type": "validated_activity_step", "index": index},
        }
        for index, step in enumerate(context["steps_data"])
    ]
    return {
        "version": 1,
        "title": title,
        "introduction": opening,
        "background": (
            f"{setting} is preparing a student-led investigation about {topic}. "
            f"{style} The virtual world contains {', '.join(objects[:4]) or 'interactive learning objects'}."
        ),
        "main_character": "You, the student investigator",
        "characters": [
            {
                "character_id": "player",
                "name": "You",
                "role": "student investigator",
                "description": "The student is the mission leader and makes each learning decision.",
                "appearance": "student avatar",
                "dialogue_style": "curious and thoughtful",
                "is_player": True,
            },
            {
                "character_id": "guide",
                "name": guide,
                "role": supporting_role,
                "description": f"{guide} encourages careful observation and explains the concept without giving away answers.",
                "appearance": "friendly guide avatar",
                "dialogue_style": "supportive, age-appropriate",
                "is_player": False,
            },
        ],
        "problem": problem,
        "mission": {
            "title": f"Mission: {topic}",
            "problem": problem,
            "final_challenge": steps[-1] if steps else objective,
            "educational_explanation": objective,
            "objectives": objectives or [
                {
                    "title": objective,
                    "expected_action": "observe",
                    "completion_condition": {"type": "validated_activity_step", "index": 0},
                }
            ],
        },
        "scenes": scenes,
        "ending": f"The team celebrates your evidence-based discovery of {topic}. {objective}",
        "reward": {
            "xp": 20,
            "coins": 3,
            "badge_name": f"{subject} Mission Explorer",
            "unlocks_story_slug": "",
        },
    }


def validate_story_blueprint(story):
    required = {
        "version",
        "title",
        "introduction",
        "background",
        "main_character",
        "characters",
        "problem",
        "mission",
        "scenes",
        "ending",
        "reward",
    }
    if not isinstance(story, dict) or set(story) != required:
        raise StoryGenerationError("Story must match the complete version 1 story schema.")
    if story["version"] != 1:
        raise StoryGenerationError("Unsupported story schema version.")
    for field in ("title", "introduction", "background", "main_character", "problem", "ending"):
        if not isinstance(story[field], str) or not story[field].strip() or len(story[field]) > 2000:
            raise StoryGenerationError(f"Story field {field} must be a non-empty string under 2000 characters.")
    characters = story["characters"]
    if not isinstance(characters, list) or not 1 <= len(characters) <= 8:
        raise StoryGenerationError("Story must define between 1 and 8 characters.")
    character_ids = set()
    for character in characters:
        if not isinstance(character, dict) or set(character) != {
            "character_id", "name", "role", "description", "appearance", "dialogue_style", "is_player"
        }:
            raise StoryGenerationError("Each character must match the story character schema.")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", character["character_id"]):
            raise StoryGenerationError("Character IDs must be lowercase slugs.")
        character_ids.add(character["character_id"])
    mission = story["mission"]
    if not isinstance(mission, dict) or set(mission) != {
        "title", "problem", "final_challenge", "educational_explanation", "objectives"
    }:
        raise StoryGenerationError("Mission must match the story mission schema.")
    if not isinstance(mission["objectives"], list) or not 1 <= len(mission["objectives"]) <= 20:
        raise StoryGenerationError("Mission must contain between 1 and 20 objectives.")
    for objective in mission["objectives"]:
        if (
            not isinstance(objective, dict)
            or set(objective) != {"title", "expected_action", "completion_condition"}
            or objective["expected_action"] not in ALLOWED_ACTIONS
            or not isinstance(objective["completion_condition"], dict)
        ):
            raise StoryGenerationError("Mission objectives must use known game actions and conditions.")
    scenes = story["scenes"]
    if not isinstance(scenes, list) or not 3 <= len(scenes) <= 12:
        raise StoryGenerationError("Story must contain between 3 and 12 scenes.")
    scene_ids = {scene.get("scene_id") for scene in scenes if isinstance(scene, dict)}
    for scene in scenes:
        if not isinstance(scene, dict) or set(scene) != {
            "scene_id", "name", "environment", "description", "required_objects",
            "player_controls", "trigger_condition", "completion_condition", "next_scene_id",
            "dialogues", "animation_events", "branches",
        }:
            raise StoryGenerationError("Each scene must match the complete story scene schema.")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", scene["scene_id"]):
            raise StoryGenerationError("Scene IDs must be lowercase slugs.")
        if scene["environment"] not in ALLOWED_ENVIRONMENTS:
            raise StoryGenerationError("Scene environment is not supported.")
        if not isinstance(scene["player_controls"], list) or not set(scene["player_controls"]).issubset(ALLOWED_ACTIONS):
            raise StoryGenerationError("Scene controls must use supported game actions.")
        if not isinstance(scene["required_objects"], list) or not isinstance(scene["trigger_condition"], dict):
            raise StoryGenerationError("Scene objects and trigger conditions must be structured data.")
        if not isinstance(scene["completion_condition"], dict):
            raise StoryGenerationError("Scene completion conditions must be structured data.")
        if scene["next_scene_id"] and scene["next_scene_id"] not in scene_ids:
            raise StoryGenerationError("Scene transition points to an unknown scene.")
        if not isinstance(scene["dialogues"], list) or not isinstance(scene["animation_events"], list):
            raise StoryGenerationError("Scene dialogue and animation events must be lists.")
        for dialogue in scene["dialogues"]:
            if (
                not isinstance(dialogue, dict)
                or set(dialogue) != {"character_id", "text", "emotion", "choices"}
                or dialogue["character_id"] not in character_ids
                or not isinstance(dialogue["text"], str)
                or not isinstance(dialogue["choices"], list)
            ):
                raise StoryGenerationError("Dialogue must refer to a declared character and use the safe schema.")
            if any(
                not isinstance(choice, dict)
                or set(choice) != {"label", "reply"}
                or not all(isinstance(choice[key], str) for key in ("label", "reply"))
                for choice in dialogue["choices"]
            ):
                raise StoryGenerationError("Dialogue choices must contain only a label and reply.")
        for event in scene["animation_events"]:
            if (
                not isinstance(event, dict)
                or set(event) != {"event_id", "trigger", "animation", "target", "configuration"}
                or event["animation"] not in ALLOWED_ANIMATIONS
                or not isinstance(event["configuration"], dict)
            ):
                raise StoryGenerationError("Animation events must use predefined animations and structured settings.")
        if not isinstance(scene["branches"], list):
            raise StoryGenerationError("Scene branches must be a list.")
        for branch in scene["branches"]:
            if (
                not isinstance(branch, dict)
                or set(branch) != {"branch_id", "prompt", "choices"}
                or not isinstance(branch["choices"], list)
                or any(
                    not isinstance(choice, dict)
                    or set(choice) != {"label", "reply"}
                    or not all(isinstance(choice[key], str) for key in ("label", "reply"))
                    for choice in branch["choices"]
                )
            ):
                raise StoryGenerationError("Branch dialogue must contain only safe prompts and replies.")
    reward = story["reward"]
    if (
        not isinstance(reward, dict)
        or set(reward) != {"xp", "coins", "badge_name", "unlocks_story_slug"}
        or not isinstance(reward["xp"], int)
        or not isinstance(reward["coins"], int)
        or not isinstance(reward["badge_name"], str)
        or not isinstance(reward["unlocks_story_slug"], str)
    ):
        raise StoryGenerationError("Reward must match the supported story reward schema.")
    return story


def _generate_with_provider(context):
    prompt = (
        "Create a version 1 structured educational adventure from the supplied class, subject, topic, objective, "
        "procedure, and objects. Return JSON only, matching the required story schema. Include 8-10 connected scenes, "
        "age-appropriate dialogue, the actual learning objective, and only predefined controls and animations. "
        "Never include code, scripts, URLs, or executable instructions. The only valid controls are: "
        f"{', '.join(sorted(ALLOWED_ACTIONS))}. The only valid environments are: "
        f"{', '.join(sorted(ALLOWED_ENVIRONMENTS))}. The only valid animations are: "
        f"{', '.join(sorted(ALLOWED_ANIMATIONS))}. Context: {json.dumps(context, ensure_ascii=False)}"
    )
    request = Request(
        settings.STORY_AI_API_URL,
        data=json.dumps(
            {
                "model": settings.STORY_AI_MODEL,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You generate safe, age-appropriate educational game story JSON."},
                    {"role": "user", "content": prompt},
                ],
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.STORY_AI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise StoryGenerationError(f"Story AI provider returned HTTP {exc.code}.") from None
    except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError):
        raise StoryGenerationError("Could not get a valid response from the configured story AI provider.") from None
    try:
        content = payload["choices"][0]["message"]["content"]
        return validate_story_blueprint(json.loads(content))
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise StoryGenerationError("Story AI provider response did not contain valid story JSON.") from None


def generate_story_blueprint(
    *, class_number, subject, topic, objective, steps, required_objects, activity_kind="activity", environment="classroom"
):
    context = {
        "class_number": int(class_number),
        "subject": str(subject).strip(),
        "topic": str(topic).strip(),
        "objective": str(objective).strip(),
        "steps": [str(step) for step in steps],
        "steps_data": steps,
        "required_objects": [str(item) for item in required_objects],
        "activity_kind": str(activity_kind),
        "environment": environment if environment in ALLOWED_ENVIRONMENTS else "classroom",
    }
    if not 1 <= context["class_number"] <= 12:
        raise StoryGenerationError("class_number must be between 1 and 12.")
    if not context["subject"] or not context["topic"] or not context["objective"]:
        raise StoryGenerationError("subject, topic, and objective are required.")
    if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
        raise StoryGenerationError("steps must be a list of structured activity steps.")
    if settings.STORY_AI_API_URL and settings.STORY_AI_API_KEY and settings.STORY_AI_MODEL:
        return _generate_with_provider(context), "configured-ai"
    story = validate_story_blueprint(_make_template(context))
    return story, "offline-template"
