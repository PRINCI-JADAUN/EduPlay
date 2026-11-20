from django.core.management.base import BaseCommand

from learning.curriculum_data import (
    CLASS_10_SCIENCE_EXPERIMENTS,
    OLD_DEMO_SUBJECT_SLUGS,
    SUBJECTS_BY_CLASS,
    activity_for,
    activity_questions_for,
    room_name,
    syllabus_url,
)
from learning.models import (
    ActivityQuestion,
    Chapter,
    ClassLevel,
    Equipment,
    LearningActivity,
    Practical,
    PracticalStep,
    Question,
    Subject,
)
from learning.story_records import create_activity_story, create_practical_story

PRACTICALS = [
    {
        "slug": "test-ph-solutions",
        "title": "Testing the pH of Different Solutions",
        "objective": "Use a universal indicator to identify acidic, neutral, and basic virtual solutions.",
        "introduction": "Indicators change colour in different pH conditions. Compare the observed colour with a pH chart.",
        "difficulty": "beginner",
        "minutes": 8,
        "samples": [
            {"slug": "dilute-hydrochloric-acid", "name": "Dilute hydrochloric acid (virtual)", "ph": 1, "category": "acidic", "color": "#e86b51"},
            {"slug": "dilute-naoh", "name": "Dilute sodium hydroxide (virtual)", "ph": 13, "category": "basic", "color": "#7868c6"},
            {"slug": "ethanoic-acid", "name": "Dilute ethanoic acid (virtual)", "ph": 3, "category": "acidic", "color": "#ed9a50"},
            {"slug": "lemon-juice", "name": "Lemon juice (virtual)", "ph": 2, "category": "acidic", "color": "#f27b42"},
            {"slug": "water", "name": "Distilled water (virtual)", "ph": 7, "category": "neutral", "color": "#4cae89"},
            {"slug": "sodium-hydrogen-carbonate", "name": "Dilute sodium hydrogen carbonate (virtual)", "ph": 8, "category": "basic", "color": "#5d9bd0"},
            {"slug": "soap-solution", "name": "Soap solution (virtual)", "ph": 10, "category": "basic", "color": "#7d71cf"},
        ],
        "questions": [
            ("easy", "What does a universal indicator help estimate?", ["The pH of a solution", "The mass of a beaker", "The temperature of a room"], 0, "A universal indicator gives a colour that can be compared with a pH chart."),
            ("medium", "A sample has pH 7. How is it classified?", ["Acidic", "Neutral", "Basic"], 1, "A pH of 7 is neutral."),
            ("hard", "A blue-violet indicator colour is matched near pH 10. What conclusion fits the chart?", ["The sample is basic", "The sample is neutral", "The sample is acidic"], 0, "A pH above 7 is basic."),
        ],
    },
    {
        "slug": "compare-indicator-colors",
        "title": "Comparing Indicator Colours",
        "objective": "Compare virtual indicator colours and classify sample solutions using the pH scale.",
        "introduction": "The same indicator can show different colours in acidic, neutral, and basic samples.",
        "difficulty": "beginner",
        "minutes": 7,
        "samples": [
            {"slug": "orange-juice", "name": "Orange juice (virtual)", "ph": 3, "category": "acidic", "color": "#ef984a"},
            {"slug": "water", "name": "Distilled water (virtual)", "ph": 7, "category": "neutral", "color": "#4cae89"},
            {"slug": "baking-soda", "name": "Baking soda solution (virtual)", "ph": 8, "category": "basic", "color": "#5d9bd0"},
        ],
        "questions": [
            ("easy", "Which pH value is neutral?", ["2", "7", "12"], 1, "A pH of 7 is neutral."),
            ("medium", "What does a colour change tell you in this simulation?", ["The indicator is responding to the sample", "The sample has evaporated", "The test tube is heavier"], 0, "Indicators respond to the acidic or basic nature of a solution."),
            ("hard", "Which sample is more basic: pH 8 or pH 3?", ["pH 8", "pH 3", "They are equally basic"], 0, "Higher pH values above 7 indicate more basic solutions."),
        ],
    },
    {
        "slug": "classify-household-solutions",
        "title": "Classifying Common Solutions",
        "objective": "Use virtual pH readings to group familiar solutions as acidic, neutral, or basic.",
        "introduction": "A pH reading provides evidence that can be used to classify a solution.",
        "difficulty": "beginner",
        "minutes": 8,
        "samples": [
            {"slug": "vinegar", "name": "Vinegar (virtual)", "ph": 3, "category": "acidic", "color": "#ef984a"},
            {"slug": "water", "name": "Distilled water (virtual)", "ph": 7, "category": "neutral", "color": "#4cae89"},
            {"slug": "soap-solution", "name": "Soap solution (virtual)", "ph": 10, "category": "basic", "color": "#7d71cf"},
        ],
        "questions": [
            ("easy", "Which pH range is acidic?", ["Below 7", "Exactly 7", "Above 7"], 0, "Acidic solutions have a pH below 7."),
            ("medium", "A sample has pH 10. How should it be grouped?", ["Acidic", "Neutral", "Basic"], 2, "A pH above 7 is basic."),
            ("hard", "Why should you compare the colour with a chart?", ["To estimate and record a pH result", "To change the sample", "To clean the equipment"], 0, "The chart connects an indicator colour to an estimated pH."),
        ],
    },
]

EQUIPMENT = [
    ("safety-goggles", "Safety goggles"),
    ("test-tube", "Test tube"),
    ("dropper", "Dropper"),
    ("indicator-paper", "Universal indicator paper"),
    ("beaker", "Beaker"),
    ("glass-rod", "Glass stirring rod"),
    ("ph-chart", "pH colour chart"),
]

STEP_DEFINITIONS = [
    ("Collect the safety goggles, test tube, dropper, and indicator paper.", "collect_equipment", [slug for slug, _ in EQUIPMENT]),
    ("Place the test tube on the virtual workbench.", "place_object", ["test-tube"]),
    ("Choose one virtual solution sample to test.", "choose_sample", []),
    ("Use the dropper to pour 10 mL of the virtual sample into the test tube.", "pour_liquid", ["dropper", "beaker"]),
    ("Mix the virtual sample gently with the glass rod.", "mix", ["glass-rod"]),
    ("Dip the indicator paper into the virtual sample and compare its colour.", "test_indicator", []),
    ("Read the colour chart and measure the matching pH.", "measure_ph", ["ph-chart"]),
    ("Record the pH and classification shown by the pH chart.", "record_observation", []),
]


class Command(BaseCommand):
    help = "Create the sample Classes 1–12 curriculum and Class 10 chemistry practicals."

    def handle(self, *args, **options):
        class_levels = {
            number: ClassLevel.objects.update_or_create(number=number, defaults={"board": "CBSE"})[0]
            for number in range(1, 13)
        }
        for subject in Subject.objects.filter(slug__in=OLD_DEMO_SUBJECT_SLUGS):
            subject.classes.clear()

        for class_number, curriculum_subjects in SUBJECTS_BY_CLASS.items():
            for name, source_path in curriculum_subjects:
                slug = name.lower().replace(" ", "-")
                subject, _ = Subject.objects.update_or_create(
                    slug=slug,
                    defaults={"name": name, "building": room_name(name)},
                )
                subject.classes.add(class_levels[class_number])
                title = "Acids, Bases and Salts" if name == "Science" and class_number == 10 else f"Class {class_number} {name} learning studio"
                chapter, _ = Chapter.objects.update_or_create(
                    subject=subject,
                    class_level=class_levels[class_number],
                    title=title,
                    defaults={"order": 1, "syllabus_url": syllabus_url(source_path)},
                )
                activity_data = activity_for(class_number, name)
                activity, _ = LearningActivity.objects.update_or_create(
                    slug=activity_data["slug"],
                    defaults={
                        "chapter": chapter,
                        "title": activity_data["title"],
                        "activity_type": activity_data["activity_type"],
                        "objective": activity_data["objective"],
                        "instructions": activity_data["instructions"],
                        "resources": activity_data["resources"],
                        "simulation": activity_data["simulation"],
                        "estimated_minutes": 10,
                    },
                )
                for order, (difficulty, prompt, options_list, correct, explanation) in enumerate(
                    activity_questions_for(activity_data), start=1
                ):
                    ActivityQuestion.objects.update_or_create(
                        activity=activity,
                        order=order,
                        defaults={
                            "difficulty": difficulty,
                            "prompt": prompt,
                            "options": options_list,
                            "correct_option": correct,
                            "explanation": explanation,
                        },
                    )
                create_activity_story(activity)
                if class_number == 10 and name == "Science":
                    experiment_template = activity_for(class_number, name)
                    for index, title in enumerate(CLASS_10_SCIENCE_EXPERIMENTS, start=1):
                        experiment_slug = f"class-10-science-cbse-practical-{index:02d}"
                        instructions = [
                            {"instruction": "Pick the virtual model for this investigation.", "action": "pick", "item": "virtual-model"},
                            {"instruction": "Place the model on the laboratory workbench.", "action": "place", "item": "virtual-model", "target": "workbench"},
                            {"instruction": "Read the virtual instrument or model measurement.", "action": "measure", "value": 10, "unit": "reading"},
                            {"instruction": "Observe the virtual model and compare it with the learning reference.", "action": "observe", "item": "virtual-result"},
                            {"instruction": "Record an observation for discussion with your teacher.", "action": "record", "item": "observation"},
                        ]
                        experiment_activity, _ = LearningActivity.objects.update_or_create(
                            slug=experiment_slug,
                            defaults={
                                "chapter": chapter,
                                "title": title,
                                "activity_type": "experiment",
                                "objective": "Explore a syllabus-listed practical through a virtual model. This guided template does not replace a teacher-reviewed procedure or predict unconfigured experiment outcomes.",
                                "instructions": instructions,
                                "resources": experiment_template["resources"],
                                "simulation": {
                                    "scene": "laboratory",
                                    "items": ["virtual-model"],
                                    "virtual_only": True,
                                    "template_only": True,
                                },
                                "estimated_minutes": 8,
                            },
                        )
                        experiment_questions = {
                            "title": title,
                            "objective": experiment_activity.objective,
                            "instructions": instructions,
                        }
                        for order, (difficulty, prompt, options_list, correct, explanation) in enumerate(
                            activity_questions_for(experiment_questions), start=1
                        ):
                            ActivityQuestion.objects.update_or_create(
                                activity=experiment_activity,
                                order=order,
                                defaults={
                                    "difficulty": difficulty,
                                    "prompt": prompt,
                                    "options": options_list,
                                    "correct_option": correct,
                                    "explanation": explanation,
                                },
                            )
                        create_activity_story(experiment_activity)

        Chapter.objects.filter(
            subject__slug__in=OLD_DEMO_SUBJECT_SLUGS,
            title__endswith="Foundations",
        ).delete()
        science = Subject.objects.get(slug="science")
        chapter = Chapter.objects.get(
            subject=science, class_level=class_levels[10], title="Acids, Bases and Salts"
        )
        equipment = {
            slug: Equipment.objects.update_or_create(
                slug=slug, defaults={"name": name, "category": "safety" if slug == "safety-goggles" else "instrument"}
            )[0]
            for slug, name in EQUIPMENT
        }

        for practical_data in PRACTICALS:
            practical, _ = Practical.objects.update_or_create(
                slug=practical_data["slug"],
                defaults={
                    "chapter":                     ActivityQuestion,
                    "chapter": chapter,
                    "title": practical_data["title"],
                    "objective": practical_data["objective"],
                    "introduction": practical_data["introduction"],
                    "safety_information": "This activity is a virtual simulation only. Do not handle real chemicals or perform this experiment outside the game.",
                    "difficulty": practical_data["difficulty"],
                    "estimated_minutes": practical_data["minutes"],
                    "samples": practical_data["samples"],
                },
            )
            for order, (instruction, action, required_slugs) in enumerate(STEP_DEFINITIONS, start=1):
                step, _ = PracticalStep.objects.update_or_create(
                    practical=practical,
                    order=order,
                    defaults={"instruction": instruction, "action": action},
                )
                step.equipment.set(equipment[slug] for slug in required_slugs)

            for order, (difficulty, prompt, options_list, correct, explanation) in enumerate(
                practical_data["questions"], start=1
            ):
                Question.objects.update_or_create(
                    practical=practical,
                    order=order,
                    defaults={
                        "difficulty": difficulty,
                        "prompt": prompt,
                        "options": options_list,
                        "correct_option": correct,
                        "explanation": explanation,
                    },
                )
            create_practical_story(practical)

        self.stdout.write(
            self.style.SUCCESS("Seeded class-specific CBSE subject directories, learning activities, resources, and chemistry practicals.")
        )

