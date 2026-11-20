from django.contrib import admin, messages
from django.utils import timezone

from .models import (
    ActivityStory,
    ActivityAttempt,
    AnimationEvent,
    Chapter,
    ClassLevel,
    Equipment,
    LearningActivity,
    Learner,
    MissionObjective,
    PlayerStoryProgress,
    Practical,
    PracticalAttempt,
    PracticalStep,
    Question,
    SceneTransition,
    StoryBranch,
    StoryCharacter,
    StoryDialogue,
    StoryMission,
    StoryReward,
    StoryScene,
    Subject,
)
from .story_engine import StoryGenerationError, validate_story_blueprint
from .story_records import stored_story_blueprint


class StoryDialogueInline(admin.TabularInline):
    model = StoryDialogue
    extra = 0


class AnimationEventInline(admin.TabularInline):
    model = AnimationEvent
    extra = 0


class StoryBranchInline(admin.TabularInline):
    model = StoryBranch
    extra = 0


class StorySceneInline(admin.StackedInline):
    model = StoryScene
    extra = 0
    show_change_link = True
    fields = (
        "scene_id",
        "sequence",
        "name",
        "environment",
        "description",
        "required_objects",
        "player_controls",
        "trigger_condition",
        "completion_condition",
        "next_scene_id",
    )


class MissionObjectiveInline(admin.TabularInline):
    model = MissionObjective
    extra = 0


@admin.register(ActivityStory)
class ActivityStoryAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "generation_source", "activity", "practical", "updated_at")
    list_filter = ("status", "generation_source")
    search_fields = ("title", "activity__title", "practical__title", "teacher_prompt")
    readonly_fields = ("generated_at", "updated_at", "approved_at")
    inlines = [StorySceneInline]
    actions = ["approve_and_publish"]
    fieldsets = (
        (
            "Story",
            {
                "fields": (
                    "activity",
                    "practical",
                    "title",
                    "introduction",
                    "background",
                    "main_character",
                    "problem",
                    "educational_explanation",
                    "ending",
                    "status",
                )
            },
        ),
        ("Generation", {"fields": ("generation_source", "teacher_prompt", "generated_at", "updated_at", "approved_at")}),
    )

    @admin.action(description="Validate, approve, and publish selected stories")
    def approve_and_publish(self, request, queryset):
        published = 0
        errors = []
        for story in queryset:
            try:
                if not (story.activity_id or story.practical_id):
                    raise ValueError("Assign the story to an activity or practical first.")
                validate_story_blueprint(stored_story_blueprint(story))
                story.status = ActivityStory.Status.PUBLISHED
                story.approved_at = timezone.now()
                story.save()
                published += 1
            except (StoryGenerationError, ValueError) as exc:
                errors.append(f"{story.title}: {exc}")
        if published:
            self.message_user(request, f"Published {published} validated story or stories.", messages.SUCCESS)
        if errors:
            self.message_user(request, "Could not publish: " + " ".join(errors), messages.ERROR)


@admin.register(StoryScene)
class StorySceneAdmin(admin.ModelAdmin):
    list_display = ("name", "story", "sequence", "environment")
    list_filter = ("environment",)
    search_fields = ("name", "description", "story__title")
    inlines = [StoryDialogueInline, AnimationEventInline, StoryBranchInline]


@admin.register(StoryMission)
class StoryMissionAdmin(admin.ModelAdmin):
    list_display = ("title", "story")
    inlines = [MissionObjectiveInline]


for model in (
    ClassLevel,
    Subject,
    Chapter,
    Practical,
    Equipment,
    PracticalStep,
    Question,
    Learner,
    PracticalAttempt,
    LearningActivity,
    ActivityAttempt,
    StoryCharacter,
    StoryDialogue,
    MissionObjective,
    SceneTransition,
    AnimationEvent,
    StoryBranch,
    StoryReward,
    PlayerStoryProgress,
):
    admin.site.register(model)

