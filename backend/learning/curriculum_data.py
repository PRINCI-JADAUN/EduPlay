SOURCE = "https://www.studiestoday.com"

SUBJECTS_BY_CLASS = {
    1: [
        ("Mathematics", "549/mathematics"),
        ("Computers", "544/computers"),
    ],
    2: [
        ("Computer", "552/computer"),
        ("Mathematics", "557/mathematics"),
    ],
    3: [
        ("Computers", "560/computers"),
        ("Hindi", "564/hindi"),
        ("Environmental Studies", "568/environmental-studies"),
        ("English", "562/english"),
        ("Mathematics", "565/mathematics"),
    ],
    4: [
        ("English", "571/english"),
        ("Mathematics", "574/mathematics"),
        ("Hindi", "573/hindi"),
        ("Environmental Studies", "578/environmental-studies"),
        ("Computers", "569/computers"),
    ],
    5: [
        ("English", "583/english"),
        ("Environmental Studies", "590/environmental-studies"),
        ("Mathematics", "586/mathematics"),
        ("Hindi", "585/hindi"),
        ("Computers", "581/computers"),
    ],
    6: [
        ("English", "70/english"),
        ("Hindi", "71/hindi"),
        ("Mathematics", "69/mathematics"),
        ("Science", "311/science"),
        ("Social Science", "502/social-science"),
    ],
    7: [
        ("English", "86/english"),
        ("Hindi", "87/hindi"),
        ("Mathematics", "88/mathematics"),
        ("Social Science", "322/social-science"),
        ("Science", "410/science"),
    ],
    8: [
        ("English", "152/english"),
        ("Hindi", "51/hindi"),
        ("Mathematics", "46/mathematics"),
        ("Science", "323/science"),
        ("Social Science", "411/social-science"),
    ],
    9: [
        ("Computer Science", "294/computer-science"),
        ("English", "36/english"),
        ("Hindi", "37/hindi"),
        ("Languages", "537/languages"),
        ("Mathematics", "38/mathematics"),
        ("Science", "408/science"),
        ("Social Science", "513/social-science"),
        ("Sanskrit", "409/sanskrit"),
        ("Other Subjects", "538/other-subjects"),
    ],
    10: [
        ("Social Science", "30/social-science"),
        ("Science", "27/science"),
        ("Sanskrit", "471/sanskrit"),
        ("Other Subjects", "623/other-subjects"),
        ("Computers", "622/computers"),
        ("English", "29/english"),
        ("French", "95/french"),
        ("Hindi", "28/hindi"),
        ("Languages", "536/languages"),
        ("Mathematics", "93/mathematics"),
    ],
    11: [
        ("Accountancy", "440/accountancy"),
        ("Biology", "104/biology"),
        ("Business Studies", "441/business-studies"),
        ("Chemistry", "103/chemistry"),
        ("Computer Science", "102/computer-science"),
        ("English", "101/english"),
        ("Physical Education", "22668/physical-education"),
        ("Economics", "439/economics"),
        ("Sanskrit", "1068/sanskrit"),
        ("Urdu", "1069/urdu"),
        ("Geography", "499/geography"),
        ("History", "498/history"),
        ("Hindi", "500/hindi"),
        ("Home Science", "437/home-science"),
        ("Informatics Practices", "497/informatics-practices"),
        ("Languages", "670/languages"),
        ("Mathematics", "100/mathematics"),
        ("Other Subjects", "624/other-subjects"),
        ("Psychology", "628/psychology"),
        ("Sociology", "631/sociology"),
        ("Political Science", "438/political-science"),
        ("Physics", "99/physics"),
    ],
    12: [
        ("Accountancy", "442/accountancy"),
        ("Biology", "446/biology"),
        ("Bio Technology", "516/bio-technology"),
        ("Business Studies", "443/business-studies"),
        ("Chemistry", "447/chemistry"),
        ("Computer Science", "448/computer-science"),
        ("Economics", "444/economics"),
        ("Engineering Drawing", "654/engineering-drawing"),
        ("Entrepreneurship", "22669/entrepreneurship"),
        ("Physical Education", "16527/physical-education"),
        ("English", "121/english"),
        ("Graphics Design", "625/graphics-design"),
        ("Geography", "309/geography"),
        ("Hindi", "308/hindi"),
        ("Home Science", "120/home-science"),
        ("History", "307/history"),
        ("Informatics Practices", "505/informatics-practices"),
        ("Languages", "517/languages"),
        ("Mathematics", "310/mathematics"),
        ("Other Subjects", "534/other-subjects"),
        ("Physics", "449/physics"),
        ("Political Science", "119/political-science"),
        ("Psychology", "506/psychology"),
        ("Sanskrit", "507/sanskrit"),
        ("Sociology", "627/sociology"),
        ("Urdu", "508/urdu"),
    ],
}

COMPUTER_SUBJECTS = {"Computers", "Computer", "Computer Science", "Informatics Practices"}
SCIENCE_LAB_SUBJECTS = {
    "Biology",
    "Bio Technology",
    "Chemistry",
    "Physics",
    "Science",
}
LAB_SUBJECTS = COMPUTER_SUBJECTS | SCIENCE_LAB_SUBJECTS

MATH_SUBJECTS = {"Mathematics", "Accountancy", "Economics", "Business Studies", "Entrepreneurship"}
LANGUAGE_SUBJECTS = {"English", "French", "Hindi", "Languages", "Sanskrit", "Urdu"}
SOCIAL_SUBJECTS = {"Geography", "History", "Political Science", "Social Science"}
CREATIVE_SUBJECTS = {"Art & Design", "Engineering Drawing", "Graphics Design", "Home Science"}

CLASS_10_SCIENCE_EXPERIMENTS = [
    "Find the pH of virtual samples using an indicator chart",
    "Compare indicator results for acidic and basic virtual samples",
    "Classify simulated chemical reaction types from their observations",
    "Compare virtual metal-displacement observations",
    "Explore the potential-difference and current relationship in a circuit",
    "Compare virtual resistor combinations in series and parallel",
    "Explore a magnified model of leaf stomata",
    "Observe a safe animation of carbon dioxide release during respiration",
    "Compare virtual ethanoic-acid observations",
    "Compare soap-cleaning simulations in soft and hard water",
    "Estimate focal length with a virtual concave mirror and convex lens",
    "Trace a simulated light ray through a rectangular glass slab",
    "Compare virtual models of binary fission and budding",
    "Trace simulated light rays through a prism",
    "Explore and label a virtual dicot seed embryo",
]

OLD_DEMO_SUBJECT_SLUGS = (
    "science",
    "mathematics",
    "english",
    "social-science",
    "computer-science",
    "art",
    "music",
)


def syllabus_url(path):
    return f"{SOURCE}/syllabus/{path}.html"


def room_name(subject_name):
    if subject_name in {"Science", "Physics", "Chemistry", "Biology", "Bio Technology"}:
        return f"{subject_name} Laboratory"
    if subject_name in {"Computers", "Computer", "Computer Science", "Informatics Practices"}:
        return "Computer Laboratory"
    if subject_name == "Mathematics":
        return "Mathematics Classroom"
    if subject_name in LANGUAGE_SUBJECTS:
        return f"{subject_name} Language Room"
    return f"{subject_name} Learning Room"


def activity_for(class_number, subject_name):
    subject_slug = subject_name.lower().replace(" ", "-")
    slug = f"class-{class_number}-{subject_slug}-studio"
    kit = {
        "science": ["safety-goggles", "beaker", "dropper", "virtual-sample"],
        "computers": ["virtual-computer", "input-device", "logic-cards"],
        "math": ["number-cards", "ruler", "virtual-workspace"],
        "language": ["word-cards", "story-cards", "notebook"],
        "social": ["map-cards", "timeline-cards", "notebook"],
        "creative": ["design-cards", "virtual-canvas", "notebook"],
        "general": ["topic-cards", "sorting-mat", "notebook"],
    }

    if subject_name in SCIENCE_LAB_SUBJECTS:
        activity_type = "experiment"
        title = f"Virtual {subject_name} Discovery Lab"
        objective = f"Explore a {subject_name.lower()} idea through a guided, safe, interactive simulation."
        items = kit["science"]
        steps = [
            {"instruction": "Pick up the virtual beaker from the lab kit.", "action": "pick", "item": "beaker"},
            {"instruction": "Put the beaker on the digital workbench.", "action": "place", "item": "beaker", "target": "workbench"},
            {"instruction": "Pick up a virtual sample.", "action": "pick", "item": "virtual-sample"},
            {"instruction": "Pour 10 mL of the virtual sample into the beaker.", "action": "pour", "item": "virtual-sample", "millilitres": 10},
            {"instruction": "Mix the virtual sample gently.", "action": "mix", "method": "swirl"},
            {"instruction": "Measure the sample using the virtual instrument.", "action": "measure", "value": 10, "unit": "mL"},
            {"instruction": "Weigh the virtual sample and compare the reading.", "action": "weigh", "value": 10, "unit": "g"},
            {"instruction": "Record what you observed in your notebook.", "action": "record", "item": "observation"},
        ]
    elif subject_name in COMPUTER_SUBJECTS:
        activity_type = "practice"
        title = f"{subject_name} Digital Problem-Solving Lab"
        objective = "Build a simple program plan by arranging input, logic, and output in the right order."
        items = kit["computers"]
        steps = [
            {"instruction": "Pick up the virtual computer for your coding task.", "action": "pick", "item": items[0]},
            {"instruction": "Place the computer on your digital workstation.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Pick up the logic cards for your algorithm.", "action": "pick", "item": items[2]},
            {"instruction": "Place the logic cards beside the computer.", "action": "place", "item": items[2], "target": "workbench"},
            {"instruction": "Arrange the logic cards into an input-process-output sequence.", "action": "sort", "item": items[2]},
            {"instruction": "Assemble the steps into a simple algorithm.", "action": "assemble", "item": "algorithm"},
            {"instruction": "Record what the program should output.", "action": "record", "item": "output"},
        ]
    elif subject_name in MATH_SUBJECTS:
        activity_type = "challenge"
        title = f"{subject_name} Measure & Solve Challenge"
        objective = f"Build a model, measure it, and solve a {subject_name.lower()} problem."
        items = kit["math"]
        steps = [
            {"instruction": "Pick up the number cards for your workspace.", "action": "pick", "item": items[0]},
            {"instruction": "Place the number cards on the virtual workbench.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Pick up the ruler.", "action": "pick", "item": "ruler"},
            {"instruction": "Put the ruler beside the number cards.", "action": "place", "item": "ruler", "target": "workbench"},
            {"instruction": "Measure the model length.", "action": "measure", "value": 12, "unit": "cm"},
            {"instruction": "Calculate the total for 3 groups of 4 units.", "action": "calculate", "value": 12},
            {"instruction": "Record your answer and compare it with the model.", "action": "record", "item": "answer"},
        ]
    elif subject_name in LANGUAGE_SUBJECTS:
        activity_type = "practice"
        title = f"{subject_name} Story Studio"
        objective = "Collect story cards, arrange them into a clear sequence, and record a short response."
        items = kit["language"]
        steps = [
            {"instruction": "Pick up three story cards.", "action": "pick", "item": items[0]},
            {"instruction": "Sort the cards into beginning, middle, and end.", "action": "sort", "item": "story-sequence"},
            {"instruction": "Put the story cards together in order.", "action": "assemble", "item": items[1]},
            {"instruction": "Read the story aloud or silently.", "action": "read", "item": "story"},
            {"instruction": "Record one sentence about the story.", "action": "record", "item": "response"},
        ]
    elif subject_name == "Psychology":
        activity_type = "project"
        title = "Mind & Behaviour Observation Studio"
        objective = "Use fictional scenarios to distinguish an observation from an interpretation."
        items = ["scenario-cards", "attention-chart", "observation-notes"]
        steps = [
            {"instruction": "Pick up the fictional scenario cards.", "action": "pick", "item": items[0]},
            {"instruction": "Place the scenario cards on the study workspace.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Observe the example attention pattern without diagnosing a person.", "action": "observe", "item": "attention-pattern"},
            {"instruction": "Sort the cards into observations and interpretations.", "action": "sort", "item": items[0]},
            {"instruction": "Record one evidence-based observation in your notes.", "action": "record", "item": "observation-notes"},
        ]
    elif subject_name == "Sociology":
        activity_type = "project"
        title = "Community Data Studio"
        objective = "Group fictional survey responses into themes and explain a pattern using evidence."
        items = ["survey-cards", "community-chart", "field-notes"]
        steps = [
            {"instruction": "Pick up the fictional community survey cards.", "action": "pick", "item": items[0]},
            {"instruction": "Place the survey cards on the data workspace.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Sort the responses into shared themes.", "action": "sort", "item": items[0]},
            {"instruction": "Observe the community chart for a visible pattern.", "action": "observe", "item": items[1]},
            {"instruction": "Record one pattern and the evidence supporting it.", "action": "record", "item": items[2]},
        ]
    elif subject_name == "Political Science":
        activity_type = "project"
        title = "Constitution & Citizenship Studio"
        objective = "Connect civic principles to institutions, rights, and responsibilities."
        items = ["constitution-cards", "institution-chart", "civic-notes"]
        steps = [
            {"instruction": "Pick up the constitution and institution cards.", "action": "pick", "item": items[0]},
            {"instruction": "Place the cards on the civic workspace.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Sort the examples into rights, responsibilities, and institutions.", "action": "sort", "item": items[0]},
            {"instruction": "Assemble a simple institution-and-responsibility chart.", "action": "assemble", "item": items[1]},
            {"instruction": "Record one evidence-based civic connection.", "action": "record", "item": items[2]},
        ]
    elif subject_name == "History":
        activity_type = "project"
        title = "History Timeline Investigation"
        objective = "Arrange evidence cards chronologically and explain how an event connects to its context."
        items = ["timeline-cards", "artifact-cards", "notebook"]
        steps = [
            {"instruction": "Pick up the timeline cards.", "action": "pick", "item": items[0]},
            {"instruction": "Place the timeline cards on the history workspace.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Sort the event cards into chronological order.", "action": "sort", "item": items[0]},
            {"instruction": "Observe the artifact cards for a clue about their context.", "action": "observe", "item": items[1]},
            {"instruction": "Record one claim supported by the evidence.", "action": "record", "item": "historical-claim"},
        ]
    elif subject_name == "Geography":
        activity_type = "project"
        title = "Map Reading & Fieldwork Studio"
        objective = "Interpret map symbols, connect features to location, and record a spatial observation."
        items = ["map-cards", "compass", "field-notes"]
        steps = [
            {"instruction": "Pick up the map cards.", "action": "pick", "item": items[0]},
            {"instruction": "Place the map cards on the geography workspace.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Sort map symbols into physical and human features.", "action": "sort", "item": items[0]},
            {"instruction": "Observe the compass direction shown on the map.", "action": "observe", "item": items[1]},
            {"instruction": "Record one spatial pattern you notice.", "action": "record", "item": items[2]},
        ]
    elif subject_name in SOCIAL_SUBJECTS:
        activity_type = "project"
        title = f"{subject_name} Map & Timeline Studio"
        objective = "Arrange map and timeline clues to explore how places and events connect."
        items = kit["social"]
        steps = [
            {"instruction": "Pick up the map and timeline cards.", "action": "pick", "item": items[0]},
            {"instruction": "Place the map cards on your classroom workbench.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Sort the timeline cards into a sensible order.", "action": "sort", "item": items[1]},
            {"instruction": "Measure the distance between two places on the map.", "action": "measure", "value": 5, "unit": "km"},
            {"instruction": "Record one observation about the map or timeline.", "action": "record", "item": "observation"},
        ]
    elif subject_name in CREATIVE_SUBJECTS:
        activity_type = "project"
        title = f"{subject_name} Design Studio"
        objective = "Arrange design materials and create a small, original classroom project."
        items = kit["creative"]
        steps = [
            {"instruction": "Pick up the design cards.", "action": "pick", "item": items[0]},
            {"instruction": "Put the design cards on your workspace.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Pick up the virtual canvas.", "action": "pick", "item": items[1]},
            {"instruction": "Place the virtual canvas on your workspace.", "action": "place", "item": items[1], "target": "workbench"},
            {"instruction": "Assemble the materials into a design.", "action": "assemble", "item": "design"},
            {"instruction": "Make a mark on the virtual canvas.", "action": "draw", "item": "canvas"},
            {"instruction": "Record a short note describing your design.", "action": "record", "item": "reflection"},
        ]
    elif subject_name in {"Physical Education"}:
        activity_type = "practice"
        title = "Movement & Measurement Challenge"
        objective = "Explore a simple virtual movement activity and record a non-medical observation."
        items = kit["general"]
        steps = [
            {"instruction": "Pick up the activity cards.", "action": "pick", "item": items[0]},
            {"instruction": "Place the activity cards on your workspace.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Measure the distance shown in the virtual activity.", "action": "measure", "value": 5, "unit": "m"},
            {"instruction": "Sort the activity steps in order.", "action": "sort", "item": "movement-steps"},
            {"instruction": "Record one observation about the movement.", "action": "record", "item": "observation"},
        ]
    else:
        activity_type = "challenge"
        title = f"{subject_name} Discovery Challenge"
        objective = f"Explore a {subject_name.lower()} topic using sorting, observation, and a short response."
        items = kit["general"]
        steps = [
            {"instruction": "Pick up the topic cards.", "action": "pick", "item": items[0]},
            {"instruction": "Place the topic cards on the virtual workspace.", "action": "place", "item": items[0], "target": "workbench"},
            {"instruction": "Sort the cards into meaningful groups.", "action": "sort", "item": "topic-cards"},
            {"instruction": "Observe the examples and choose a connection.", "action": "observe", "item": "connection"},
            {"instruction": "Record one thing you learned.", "action": "record", "item": "reflection"},
        ]

    search_terms = f"CBSE Class {class_number} {subject_name} hands-on learning".replace(" ", "+")
    if subject_name in COMPUTER_SUBJECTS:
        khan_path = "computing"
    elif subject_name in MATH_SUBJECTS:
        khan_path = "math"
    elif subject_name in LANGUAGE_SUBJECTS:
        khan_path = "humanities/grammar"
    elif subject_name in SOCIAL_SUBJECTS:
        khan_path = "humanities"
    else:
        khan_path = "science"
    resources = [
        {
            "title": f"Fun {subject_name} videos · YouTube",
            "provider": "YouTube",
            "kind": "video_search",
            "url": f"https://www.youtube.com/results?search_query={search_terms}",
        },
        {
            "title": f"{subject_name} lessons · Khan Academy",
            "provider": "Khan Academy",
            "kind": "learning_platform",
            "url": f"https://www.khanacademy.org/{khan_path}",
        },
        {
            "title": "CBSE digital lessons · DIKSHA",
            "provider": "DIKSHA",
            "kind": "learning_platform",
            "url": "https://diksha.gov.in/explore",
        },
    ]
    if subject_name in SCIENCE_LAB_SUBJECTS:
        resources[1]["url"] = "https://www.khanacademy.org/science"

    return {
        "slug": slug,
        "title": title,
        "activity_type": activity_type,
        "objective": objective,
        "instructions": steps,
        "resources": resources,
        "simulation": {"scene": "laboratory" if activity_type == "experiment" else "classroom", "items": items},
    }


def activity_questions_for(activity):
    instructions = activity["instructions"]
    first_step = instructions[0]["instruction"]
    last_step = instructions[-1]["instruction"]
    middle_step = instructions[-2]["instruction"] if len(instructions) > 1 else first_step
    title = activity["title"]
    objective = activity["objective"]

    return [
        (
            "easy",
            f"What is the main learning goal of {title}?",
            [objective, "To skip the guided steps", "To collect materials without learning the topic"],
            0,
            f"The activity objective is: {objective}",
        ),
        (
            "medium",
            "What should you do first in this activity?",
            [first_step, last_step, middle_step],
            0,
            f"Start by following this instruction: {first_step}",
        ),
        (
            "hard",
            "Which instruction completes the activity?",
            [last_step, first_step, middle_step],
            0,
            f"The final guided instruction is: {last_step}",
        ),
    ]
