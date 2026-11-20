import json

import jwt
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from .curriculum_data import activity_for
from .models import ActivityStory, Learner, LearningActivity, PracticalAttempt, PlayerStoryProgress
from .story_engine import StoryGenerationError, generate_story_blueprint, validate_story_blueprint


class LearningWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        response = self.client.post(
            "/api/players/",
            data=json.dumps(
                {"player_id": "c1b503b3-d9ce-4a43-8736-58f8ef4ab529", "display_name": "Ari", "class": 10}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.player_id = "c1b503b3-d9ce-4a43-8736-58f8ef4ab529"

    def post_json(self, path, payload):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json")

    def start_attempt(self):
        response = self.post_json(
            "/api/attempts/",
            {"player_id": self.player_id, "practical_slug": "test-ph-solutions"},
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["story"]["status"], ActivityStory.Status.PUBLISHED)
        self.assertEqual(len(response.json()["story"]["scenes"]), 10)
        return response.json()["attempt_id"]

    def test_curriculum_lists_all_classes_and_sample_subjects(self):
        response = self.client.get("/api/curriculum/?class=10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["classes"]), 12)
        self.assertIn("Science", [subject["name"] for subject in response.json()["subjects"]])
        science = next(subject for subject in response.json()["subjects"] if subject["name"] == "Science")
        self.assertTrue(science["chapters"][0]["syllabus_url"].endswith("/syllabus/27/science.html"))
        self.assertGreaterEqual(science["chapters"][0]["activities_count"], 16)
        class_one = self.client.get("/api/curriculum/?class=1").json()
        self.assertEqual([subject["name"] for subject in class_one["subjects"]], ["Computers", "Mathematics"])
        class_twelve = self.client.get("/api/curriculum/?class=12").json()
        self.assertIn("Bio Technology", [subject["name"] for subject in class_twelve["subjects"]])
        for class_number in range(1, 13):
            class_data = self.client.get(f"/api/curriculum/?class={class_number}").json()
            self.assertTrue(class_data["subjects"], f"Class {class_number} should have catalog subjects.")
            self.assertTrue(
                all(subject["chapters"][0]["activities_count"] >= 1 for subject in class_data["subjects"]),
                f"Every Class {class_number} subject should have an interactive activity.",
            )

    def test_room_and_learning_activity_are_available_for_selected_class(self):
        room = self.client.get("/api/rooms/5/environmental-studies/")
        self.assertEqual(room.status_code, 200)
        self.assertEqual(room.json()["name"], "Environmental Studies")
        activity = room.json()["chapters"][0]["activities"][0]
        self.assertEqual(len(activity["resources"]), 3)
        self.assertEqual(activity["resources"][0]["provider"], "YouTube")

        library = self.client.get("/api/rooms/5/library/")
        self.assertEqual(library.status_code, 200)
        self.assertEqual(len(library.json()["subjects"]), 5)

        bio_technology = self.client.get("/api/rooms/12/bio-technology/")
        self.assertEqual(bio_technology.status_code, 200)
        self.assertEqual(bio_technology.json()["room_type"], "laboratory")

        informatics_room = self.client.get("/api/rooms/11/informatics-practices/")
        self.assertEqual(informatics_room.status_code, 200)
        informatics_activity = informatics_room.json()["chapters"][0]["activities"][0]
        self.assertEqual(informatics_activity["activity_type"], "practice")
        self.assertIn("virtual-computer", informatics_activity["simulation"]["items"])

        started = self.post_json(
            "/api/activities/start/",
            {"player_id": self.player_id, "activity_slug": "class-10-other-subjects-studio"},
        )
        self.assertEqual(started.status_code, 201)
        self.assertEqual(len(started.json()["story"]["scenes"]), 10)
        self.assertEqual(started.json()["story"]["status"], ActivityStory.Status.PUBLISHED)
        story_progress = PlayerStoryProgress.objects.get(activity_attempt_id=started.json()["attempt_id"])
        self.assertEqual(story_progress.current_scene.scene_id, "cinematic-intro")
        next_step = self.post_json(
            f"/api/activity-attempts/{started.json()['attempt_id']}/action/",
            {"player_id": self.player_id, "action": "pick", "payload": {"item": "topic-cards"}},
        )
        self.assertEqual(next_step.status_code, 200)
        self.assertEqual(next_step.json()["current_step"]["action"], "place")
        self.assertEqual(next_step.json()["current_step"]["item"], "topic-cards")

    def test_seeded_activities_only_place_items_after_pickup(self):
        for activity in LearningActivity.objects.select_related("chapter__class_level", "chapter__subject"):
            self.assertEqual(activity.questions.count(), 3, f"{activity.slug} should have a three-question quiz.")
            story = activity.stories.filter(status=ActivityStory.Status.PUBLISHED).first()
            self.assertIsNotNone(story, f"{activity.slug} should have a published story.")
            self.assertEqual(story.scenes.count(), 10, f"{activity.slug} should have ten story scenes.")
            self.assertTrue(story.characters.filter(is_player=True).exists())
            picked_items = set()
            for step in activity.instructions:
                if step["action"] == "pick":
                    picked_items.add(step["item"])
                elif step["action"] == "place":
                    self.assertIn(
                        step["item"],
                        picked_items,
                        f"{activity.slug} places {step['item']} before it is picked up.",
                    )

    def test_computer_subjects_use_coding_materials_not_chemistry_equipment(self):
        for subject in ("Computer", "Computer Science", "Informatics Practices"):
            activity = activity_for(11, subject)
            self.assertEqual(activity["simulation"]["items"][0], "virtual-computer")
            self.assertNotIn("beaker", activity["simulation"]["items"])
            self.assertEqual(activity["instructions"][0]["item"], "virtual-computer")
        psychology = activity_for(11, "Psychology")
        self.assertIn("fictional", psychology["objective"])
        self.assertEqual(psychology["simulation"]["items"][0], "scenario-cards")

    def test_learning_activity_actions_unlock_one_step_at_a_time(self):
        started = self.post_json(
            "/api/activities/start/",
            {"player_id": self.player_id, "activity_slug": "class-10-science-studio"},
        )
        self.assertEqual(started.status_code, 201, started.content)
        attempt_id = started.json()["attempt_id"]
        action_url = f"/api/activity-attempts/{attempt_id}/action/"

        blocked = self.post_json(
            action_url,
            {"player_id": self.player_id, "action": "place", "payload": {"item": "beaker"}},
        )
        self.assertEqual(blocked.status_code, 409)

        actions = [
            ("pick", {"item": "beaker"}),
            ("place", {"item": "beaker"}),
            ("pick", {"item": "virtual-sample"}),
            ("pour", {"item": "virtual-sample", "millilitres": 10}),
            ("mix", {"method": "swirl"}),
            ("measure", {"value": 10, "unit": "mL"}),
            ("weigh", {"value": 10, "unit": "g"}),
            ("record", {"item": "observation", "completed": True}),
        ]
        for index, (action, payload) in enumerate(actions):
            response = self.post_json(
                action_url,
                {"player_id": self.player_id, "action": action, "payload": payload},
            )
            self.assertEqual(response.status_code, 200, response.content)
            if index < len(actions) - 1:
                self.assertIn("current_step", response.json())
                self.assertEqual(response.json()["current_step"]["action"], actions[index + 1][0])
                self.assertNotIn("value", response.json()["current_step"])
            else:
                self.assertEqual(response.json()["status"], "quiz")

        quiz_response = self.client.get(f"/api/activity-attempts/{attempt_id}/quiz/?player_id={self.player_id}")
        questions = quiz_response.json()["questions"]
        self.assertEqual(len(questions), 3)
        self.assertIn("Virtual Science Discovery Lab", questions[0]["prompt"])
        perfect_answers = [
            {"question_id": question["id"], "selected_option": 0}
            for question in questions
        ]
        submitted = self.post_json(
            f"/api/activity-attempts/{attempt_id}/quiz/",
            {"player_id": self.player_id, "answers": perfect_answers},
        )
        self.assertEqual(submitted.status_code, 200, submitted.content)
        self.assertEqual(submitted.json()["score"], 100)
        self.assertEqual(submitted.json()["reward"], {"xp": 30, "coins": 5})
        self.assertEqual(submitted.json()["story_ending"]["scene_id"], "story-resolution")

        learner = Learner.objects.get(player_id=self.player_id)
        self.assertEqual((learner.xp, learner.coins), (30, 5))
        story_progress = PlayerStoryProgress.objects.get(activity_attempt_id=attempt_id)
        self.assertEqual(story_progress.status, PlayerStoryProgress.Status.COMPLETED)
        self.assertEqual(story_progress.current_scene.scene_id, "story-resolution")

        duplicate = self.post_json(
            f"/api/activity-attempts/{attempt_id}/quiz/",
            {"player_id": self.player_id, "answers": perfect_answers},
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_server_validates_steps_observation_quiz_and_rewards(self):
        attempt_id = self.start_attempt()
        action_url = f"/api/attempts/{attempt_id}/action/"

        invalid_equipment = self.post_json(
            action_url,
            {"player_id": self.player_id, "action": "collect_equipment", "payload": {"equipment": ["dropper"]}},
        )
        self.assertEqual(invalid_equipment.status_code, 400)

        steps = [
            (
                "collect_equipment",
                {"equipment": ["safety-goggles", "test-tube", "dropper", "indicator-paper", "beaker", "glass-rod", "ph-chart"]},
            ),
            ("place_object", {"item": "test-tube", "target": "workbench"}),
            ("choose_sample", {"sample": "lemon-juice"}),
            ("pour_liquid", {"millilitres": 10}),
            ("mix", {"method": "swirl"}),
        ]
        for action, payload in steps:
            response = self.post_json(
                action_url, {"player_id": self.player_id, "action": action, "payload": payload}
            )
            self.assertEqual(response.status_code, 200, response.content)

        tested = self.post_json(
            action_url, {"player_id": self.player_id, "action": "test_indicator", "payload": {}}
        )
        self.assertEqual(tested.status_code, 200)
        self.assertEqual(tested.json()["result"]["ph"], 2)

        wrong_measurement = self.post_json(
            action_url, {"player_id": self.player_id, "action": "measure_ph", "payload": {"ph": 7}}
        )
        self.assertEqual(wrong_measurement.status_code, 400)
        measured = self.post_json(
            action_url, {"player_id": self.player_id, "action": "measure_ph", "payload": {"ph": 2}}
        )
        self.assertEqual(measured.status_code, 200)

        wrong_observation = self.post_json(
            action_url,
            {
                "player_id": self.player_id,
                "action": "record_observation",
                "payload": {"ph": 7, "category": "neutral"},
            },
        )
        self.assertEqual(wrong_observation.status_code, 400)

        recorded = self.post_json(
            action_url,
            {
                "player_id": self.player_id,
                "action": "record_observation",
                "payload": {"ph": 2, "category": "acidic"},
            },
        )
        self.assertEqual(recorded.status_code, 200)
        self.assertEqual(recorded.json()["status"], PracticalAttempt.Status.QUIZ)

        quiz_response = self.client.get(f"/api/attempts/{attempt_id}/quiz/?player_id={self.player_id}")
        questions = quiz_response.json()["questions"]
        perfect_answers = [
            {"question_id": question["id"], "selected_option": [0, 1, 0][index]}
            for index, question in enumerate(questions)
        ]
        submitted = self.post_json(
            f"/api/attempts/{attempt_id}/quiz/",
            {"player_id": self.player_id, "answers": perfect_answers},
        )
        self.assertEqual(submitted.status_code, 200, submitted.content)
        self.assertEqual(submitted.json()["score"], 100)
        self.assertEqual(submitted.json()["reward"], {"xp": 100, "coins": 15})

        learner = Learner.objects.get(player_id=self.player_id)
        self.assertEqual((learner.xp, learner.coins), (100, 15))

        duplicate = self.post_json(
            f"/api/attempts/{attempt_id}/quiz/",
            {"player_id": self.player_id, "answers": perfect_answers},
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_practical_is_restricted_to_class_ten(self):
        response = self.post_json(
            "/api/players/",
            {"player_id": "0fa0cc59-1ce7-4401-b2ca-4126d41545d5", "display_name": "Sam", "class": 9},
        )
        self.assertEqual(response.status_code, 201)
        denied = self.post_json(
            "/api/attempts/",
            {"player_id": "0fa0cc59-1ce7-4401-b2ca-4126d41545d5", "practical_slug": "test-ph-solutions"},
        )
        self.assertEqual(denied.status_code, 403)

    def test_story_drafts_are_staff_generated_and_require_approval(self):
        activity = LearningActivity.objects.get(slug="class-10-science-studio")
        denied = self.post_json("/api/stories/generate/", {"activity_slug": activity.slug})
        self.assertEqual(denied.status_code, 403)

        teacher = get_user_model().objects.create_user(
            username="story-editor",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(teacher)
        generated = self.post_json(
            "/api/stories/generate/",
            {"activity_slug": activity.slug, "teacher_prompt": "Make the lab story curious and supportive."},
        )
        self.assertEqual(generated.status_code, 201, generated.content)
        self.assertEqual(generated.json()["status"], ActivityStory.Status.DRAFT)
        self.assertEqual(len(generated.json()["scenes"]), 10)

        published = self.post_json(f"/api/stories/{generated.json()['id']}/publish/", {})
        self.assertEqual(published.status_code, 200, published.content)
        self.assertEqual(published.json()["status"], ActivityStory.Status.PUBLISHED)
        self.assertTrue(activity.stories.filter(status=ActivityStory.Status.PUBLISHED).exists())

    @override_settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_JWT_SECRET="test-signing-secret-for-eduplay-auth-tests",
        LOCAL_DEMO_MODE=True,
    )
    def test_configured_supabase_auth_requires_a_valid_signed_token(self):
        guest_bypass = self.post_json(
            "/api/players/",
            {"player_id": self.player_id, "display_name": "Guest", "class": 10},
        )
        self.assertEqual(guest_bypass.status_code, 401)

        subject = "801b9ecc-9644-4a63-8f10-7126e22b0845"
        token = jwt.encode(
            {"sub": subject, "aud": "authenticated"},
            "test-signing-secret-for-eduplay-auth-tests",
            algorithm="HS256",
        )
        authenticated = self.client.post(
            "/api/players/",
            data=json.dumps({"display_name": "Signed in", "class": 10}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(authenticated.status_code, 201, authenticated.content)
        self.assertEqual(authenticated.json()["player_id"], subject)


class StorySchemaTests(SimpleTestCase):
    def test_generated_story_uses_age_appropriate_structure_and_safe_actions(self):
        activity = activity_for(2, "Mathematics")
        story, source = generate_story_blueprint(
            class_number=2,
            subject="Mathematics",
            topic=activity["title"],
            objective=activity["objective"],
            steps=activity["instructions"],
            required_objects=activity["simulation"]["items"],
        )
        self.assertEqual(source, "offline-template")
        self.assertIn("Wonder Garden", story["title"])
        self.assertEqual(len(story["scenes"]), 10)
        self.assertIn("Pip", story["characters"][1]["name"])
        story["scenes"][0]["animation_events"][0]["animation"] = "run-python"
        with self.assertRaises(StoryGenerationError):
            validate_story_blueprint(story)
