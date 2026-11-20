import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class ClassLevel(models.Model):
    number = models.PositiveSmallIntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    board = models.CharField(max_length=32, default="CBSE")

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Class {self.number}"


class Subject(models.Model):
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100)
    classes = models.ManyToManyField(ClassLevel, related_name="subjects")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="chapters")
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=150)
    syllabus_url = models.URLField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order", "title"]
        constraints = [
            models.UniqueConstraint(fields=["subject", "class_level", "title"], name="unique_class_subject_chapter")
        ]

    def __str__(self):
        return self.title


class Practical(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="practicals")
    title = models.CharField(max_length=180)
    objective = models.TextField()
    introduction = models.TextField()
    safety_information = models.TextField()
    difficulty = models.CharField(max_length=24, default="beginner")
    estimated_minutes = models.PositiveSmallIntegerField(default=10)
    samples = models.JSONField(default=list)

    def __str__(self):
        return self.title


class Equipment(models.Model):
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, default="laboratory")

    def __str__(self):
        return self.name


class PracticalStep(models.Model):
    practical = models.ForeignKey(Practical, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField()
    instruction = models.CharField(max_length=300)
    action = models.CharField(max_length=40)
    equipment = models.ManyToManyField(Equipment, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["practical", "order"], name="unique_practical_step_order")
        ]


class LearningActivity(models.Model):
    class ActivityType(models.TextChoices):
        EXPERIMENT = "experiment", "Experiment"
        PRACTICE = "practice", "Practice"
        PROJECT = "project", "Project"
        CHALLENGE = "challenge", "Challenge"

    slug = models.SlugField(max_length=140, unique=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="activities")
    title = models.CharField(max_length=180)
    activity_type = models.CharField(max_length=16, choices=ActivityType.choices)
    objective = models.TextField()
    instructions = models.JSONField(default=list)
    resources = models.JSONField(default=list)
    simulation = models.JSONField(default=dict)
    estimated_minutes = models.PositiveSmallIntegerField(default=10)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class ActivityStory(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    activity = models.ForeignKey(
        LearningActivity, null=True, blank=True, on_delete=models.CASCADE, related_name="stories"
    )
    practical = models.ForeignKey(
        Practical, null=True, blank=True, on_delete=models.CASCADE, related_name="stories"
    )
    title = models.CharField(max_length=180)
    introduction = models.TextField()
    background = models.TextField()
    main_character = models.CharField(max_length=80, default="You")
    problem = models.TextField()
    educational_explanation = models.TextField()
    ending = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    generation_source = models.CharField(max_length=40, default="offline-template")
    teacher_prompt = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(activity__isnull=True)
                    | Q(practical__isnull=True)
                ),
                name="story_has_at_most_one_parent",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="draft")
                    | Q(activity__isnull=False, practical__isnull=True)
                    | Q(activity__isnull=True, practical__isnull=False)
                ),
                name="published_story_has_parent",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.activity_id and self.practical_id:
            raise ValidationError("A story can belong to an activity or a practical, not both.")
        if self.status == self.Status.PUBLISHED and not (self.activity_id or self.practical_id):
            raise ValidationError("Publish a story only after assigning it to an activity or practical.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class StoryCharacter(models.Model):
    story = models.ForeignKey(ActivityStory, on_delete=models.CASCADE, related_name="characters")
    character_id = models.SlugField(max_length=50)
    name = models.CharField(max_length=80)
    role = models.CharField(max_length=80)
    description = models.TextField()
    appearance = models.CharField(max_length=120, blank=True)
    dialogue_style = models.CharField(max_length=120, blank=True)
    is_player = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["story", "character_id"], name="unique_story_character_id"),
        ]

    def __str__(self):
        return self.name


class StoryScene(models.Model):
    story = models.ForeignKey(ActivityStory, on_delete=models.CASCADE, related_name="scenes")
    scene_id = models.SlugField(max_length=40)
    name = models.CharField(max_length=120)
    sequence = models.PositiveSmallIntegerField()
    environment = models.CharField(max_length=40, default="classroom")
    description = models.TextField()
    required_objects = models.JSONField(default=list)
    player_controls = models.JSONField(default=list)
    trigger_condition = models.JSONField(default=dict)
    completion_condition = models.JSONField(default=dict)
    next_scene_id = models.SlugField(max_length=40, blank=True)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["story", "scene_id"], name="unique_story_scene_id"),
            models.UniqueConstraint(fields=["story", "sequence"], name="unique_story_scene_sequence"),
        ]

    def __str__(self):
        return f"{self.story.title}: {self.name}"


class StoryDialogue(models.Model):
    scene = models.ForeignKey(StoryScene, on_delete=models.CASCADE, related_name="dialogues")
    character = models.ForeignKey(
        StoryCharacter, null=True, blank=True, on_delete=models.CASCADE, related_name="dialogues"
    )
    order = models.PositiveSmallIntegerField()
    text = models.CharField(max_length=500)
    emotion = models.CharField(max_length=24, default="friendly")
    choices = models.JSONField(default=list)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["scene", "order"], name="unique_scene_dialogue_order"),
        ]


class StoryMission(models.Model):
    story = models.OneToOneField(ActivityStory, on_delete=models.CASCADE, related_name="mission")
    title = models.CharField(max_length=180)
    problem = models.TextField()
    final_challenge = models.TextField()
    educational_explanation = models.TextField()

    def __str__(self):
        return self.title


class MissionObjective(models.Model):
    mission = models.ForeignKey(StoryMission, on_delete=models.CASCADE, related_name="objectives")
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    expected_action = models.CharField(max_length=40, blank=True)
    completion_condition = models.JSONField(default=dict)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["mission", "order"], name="unique_mission_objective_order"),
        ]


class SceneTransition(models.Model):
    story = models.ForeignKey(ActivityStory, on_delete=models.CASCADE, related_name="transitions")
    from_scene_id = models.SlugField(max_length=40)
    to_scene_id = models.SlugField(max_length=40)
    trigger_condition = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["story", "from_scene_id", "to_scene_id"], name="unique_story_transition"
            ),
        ]


class AnimationEvent(models.Model):
    class Animation(models.TextChoices):
        FADE_IN = "fade_in", "Fade in"
        CAMERA_PAN = "camera_pan", "Camera pan"
        WAVE = "wave", "Wave"
        POINT = "point", "Point"
        PICKUP = "pickup", "Pick up"
        PLACE = "place", "Place"
        WALK = "walk", "Walk"
        THINK = "think", "Think"
        CELEBRATE = "celebrate", "Celebrate"
        GLOW = "glow", "Glow"

    scene = models.ForeignKey(StoryScene, on_delete=models.CASCADE, related_name="animation_events")
    event_id = models.SlugField(max_length=60)
    trigger = models.CharField(max_length=32)
    animation = models.CharField(max_length=20, choices=Animation.choices)
    target = models.CharField(max_length=80, default="scene")
    configuration = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["scene", "event_id"], name="unique_scene_animation_event"),
        ]


class StoryBranch(models.Model):
    scene = models.ForeignKey(StoryScene, on_delete=models.CASCADE, related_name="branches")
    branch_id = models.SlugField(max_length=50)
    prompt = models.CharField(max_length=300)
    choices = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["scene", "branch_id"], name="unique_scene_branch_id"),
        ]


class StoryReward(models.Model):
    story = models.OneToOneField(ActivityStory, on_delete=models.CASCADE, related_name="reward")
    xp = models.PositiveIntegerField(default=20)
    coins = models.PositiveIntegerField(default=3)
    badge_name = models.CharField(max_length=80)
    unlocks_story_slug = models.SlugField(max_length=140, blank=True)


class Question(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    practical = models.ForeignKey(Practical, on_delete=models.CASCADE, related_name="questions")
    difficulty = models.CharField(max_length=12, choices=Difficulty.choices)
    prompt = models.CharField(max_length=300)
    options = models.JSONField(default=list)
    correct_option = models.PositiveSmallIntegerField()
    explanation = models.TextField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["practical", "order"], name="unique_practical_question_order")
        ]


class Learner(models.Model):
    player_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=40)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.PROTECT)
    xp = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name


class ActivityAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        QUIZ = "quiz", "Quiz ready"
        COMPLETED = "completed", "Completed"

    attempt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="activity_attempts")
    activity = models.ForeignKey(LearningActivity, on_delete=models.PROTECT, related_name="attempts")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)
    step_index = models.PositiveSmallIntegerField(default=0)
    observations = models.JSONField(default=dict)
    score = models.PositiveSmallIntegerField(default=0)
    quiz_answers = models.JSONField(default=list)
    xp_awarded = models.PositiveIntegerField(default=0)
    coins_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class ActivityQuestion(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    activity = models.ForeignKey(LearningActivity, on_delete=models.CASCADE, related_name="questions")
    difficulty = models.CharField(max_length=12, choices=Difficulty.choices)
    prompt = models.CharField(max_length=300)
    options = models.JSONField(default=list)
    correct_option = models.PositiveSmallIntegerField()
    explanation = models.TextField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["activity", "order"], name="unique_activity_question_order")
        ]


class PracticalAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        QUIZ = "quiz", "Quiz ready"
        COMPLETED = "completed", "Completed"

    attempt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="attempts")
    practical = models.ForeignKey(Practical, on_delete=models.PROTECT, related_name="attempts")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)
    step_index = models.PositiveSmallIntegerField(default=0)
    observations = models.JSONField(default=dict)
    score = models.PositiveSmallIntegerField(default=0)
    quiz_answers = models.JSONField(default=list)
    xp_awarded = models.PositiveIntegerField(default=0)
    coins_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class PlayerStoryProgress(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="story_progress")
    story = models.ForeignKey(ActivityStory, on_delete=models.PROTECT, related_name="player_progress")
    activity_attempt = models.OneToOneField(
        ActivityAttempt, null=True, blank=True, on_delete=models.CASCADE, related_name="story_progress"
    )
    practical_attempt = models.OneToOneField(
        PracticalAttempt, null=True, blank=True, on_delete=models.CASCADE, related_name="story_progress"
    )
    current_scene = models.ForeignKey(
        StoryScene, null=True, blank=True, on_delete=models.SET_NULL, related_name="player_progress"
    )
    completed_scenes = models.JSONField(default=list)
    state = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(activity_attempt__isnull=False, practical_attempt__isnull=True)
                    | Q(activity_attempt__isnull=True, practical_attempt__isnull=False)
                ),
                name="story_progress_has_one_attempt",
            ),
        ]

