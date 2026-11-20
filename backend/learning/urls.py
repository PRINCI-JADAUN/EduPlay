from django.urls import path

from . import views


urlpatterns = [
    path("health/", views.health, name="health"),
    path("curriculum/", views.curriculum, name="curriculum"),
    path("rooms/<int:class_number>/<slug:subject_slug>/", views.room_detail, name="room-detail"),
    path("activities/", views.activities, name="activities"),
    path("activities/start/", views.start_activity, name="start-activity"),
    path("activity-attempts/<uuid:attempt_id>/action/", views.activity_action, name="activity-action"),
    path("activity-attempts/<uuid:attempt_id>/quiz/", views.activity_quiz, name="activity-quiz"),
    path("stories/generate/", views.generate_story_draft, name="generate-story-draft"),
    path("stories/<int:story_id>/publish/", views.publish_story, name="publish-story"),
    path("players/", views.players, name="players"),
    path("practicals/", views.practicals, name="practicals"),
    path("practicals/<slug:slug>/", views.practical_detail, name="practical-detail"),
    path("attempts/", views.start_attempt, name="start-attempt"),
    path("attempts/<uuid:attempt_id>/action/", views.attempt_action, name="attempt-action"),
    path("attempts/<uuid:attempt_id>/quiz/", views.attempt_quiz, name="attempt-quiz"),
    path("progress/", views.progress, name="progress"),
    path("assistant/", views.assistant, name="assistant"),
]

