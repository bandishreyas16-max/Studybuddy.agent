import re
from langchain.tools import tool


# ---------------------------------------------------------
# Grade thresholds
# ---------------------------------------------------------

GRADE_VALUES = {
    "A+": 95,
    "A": 85,
    "A-": 80,
    "B+": 75,
    "B": 65,
    "B-": 60,
    "C+": 55,
    "C": 50,
    "D": 40,
    "F": 0
}


# ---------------------------------------------------------
# Course names we expect in academic documents
# ---------------------------------------------------------

COURSES = [
    "Python Programming",
    "Data Structures",
    "Database Management Systems",
    "Operating Systems",
    "Computer Networks",
    "Web Technologies"
]


# ---------------------------------------------------------
# Extract grades from transcript
# ---------------------------------------------------------

def extract_grades(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    grades = {}

    for i, line in enumerate(lines):

        # Check whether this line is a course name
        course = None

        for possible_course in COURSES:

            if possible_course.lower() == line.lower():

                course = possible_course
                break

        if not course:
            continue

        grade = None
        marks = None

        # Look at the next few lines
        # because PDF extraction may place
        # grade and marks on separate lines.

        for next_line in lines[i + 1:i + 4]:

            # Grade
            if re.fullmatch(
                r"A\+|A-|A|B\+|B-|B|C\+|C-|C|D|F",
                next_line,
                re.IGNORECASE
            ):

                grade = next_line.upper()

            # Marks
            if re.fullmatch(
                r"\d{1,3}",
                next_line
            ):

                value = int(next_line)

                if 0 <= value <= 100:
                    marks = value

        if grade:

            grades[course] = {
                "grade": grade,
                "marks": marks
            }

    return grades


# ---------------------------------------------------------
# Extract course sections
# ---------------------------------------------------------

def extract_course_sections(text, section_name):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    sections = {}

    try:
        start = next(
            i for i, line in enumerate(lines)
            if section_name.lower() in line.lower()
        )
    except StopIteration:

        return sections

    current_course = None

    for line in lines[start + 1:]:

        # Stop when another numbered major section begins
        if re.match(r"^\d+\.", line):
            break

        # Check for course heading
        for course in COURSES:

            if course.lower() == line.lower():

                current_course = course
                sections[current_course] = []
                break

        else:

            if current_course:

                # Ignore empty/unwanted lines
                if line not in sections[current_course]:

                    sections[current_course].append(line)

    return sections


# ---------------------------------------------------------
# Normalize topic text
# ---------------------------------------------------------

def normalize_topic(topic):

    topic = topic.strip()

    topic = topic.replace("•", "")
    topic = topic.replace("-", "")

    topic = re.sub(
        r"\s+",
        " ",
        topic
    )

    return topic.strip().lower()


# ---------------------------------------------------------
# Extract topics from a course section
# ---------------------------------------------------------

def extract_topics(section_lines):

    topics = []

    # Common academic topic names.
    # This makes extraction reliable even when
    # PDF text extraction puts multiple topics
    # on the same line.

    known_topics = [
        "ER Model",
        "Relational Model",
        "SQL and Queries",
        "Normalization",
        "Joins",
        "Indexing",
        "Transactions",
        "ACID Properties",

        "Processes and Threads",
        "CPU Scheduling",
        "Deadlocks",
        "Memory Management",
        "File Systems",

        "OSI Model",
        "TCP/IP",
        "Transport Layer",
        "DNS",
        "DHCP",

        "HTML",
        "CSS",
        "JavaScript",
        "REST APIs",
        "Authentication",

        "Variables and Data Types",
        "Functions",
        "Lists and Dictionaries",
        "Object-Oriented Programming",
        "File Handling"
    ]

    combined_text = " ".join(section_lines)

    for topic in known_topics:

        if topic.lower() in combined_text.lower():

            topics.append(topic)

    return topics


# ---------------------------------------------------------
# Find missing topics
# ---------------------------------------------------------

def find_missing_topics(syllabus_text, notes_text):

    # Topics expected in the syllabus
    syllabus_topics = {
        "Database Management Systems": [
            "ER Model",
            "Relational Model",
            "SQL and Queries",
            "Normalization",
            "Joins",
            "Indexing",
            "Transactions",
            "ACID Properties"
        ],

        "Operating Systems": [
            "Processes and Threads",
            "CPU Scheduling",
            "Deadlocks",
            "Memory Management",
            "File Systems"
        ],

        "Computer Networks": [
            "OSI Model",
            "TCP/IP",
            "Transport Layer",
            "DNS",
            "DHCP"
        ],

        "Web Technologies": [
            "HTML",
            "CSS",
            "JavaScript",
            "REST APIs",
            "Authentication"
        ],

        "Python Programming": [
            "Variables and Data Types",
            "Functions",
            "Lists and Dictionaries",
            "Object-Oriented Programming",
            "File Handling"
        ]
    }

    missing = []

    syllabus_lower = syllabus_text.lower()
    notes_lower = notes_text.lower()

    for course, topics in syllabus_topics.items():

        # Only process a course if it exists in the syllabus
        if course.lower() not in syllabus_lower:
            continue

        for topic in topics:

            # Topic exists in syllabus but not in notes
            if topic.lower() not in notes_lower:

                missing.append({
                    "course": course,
                    "topic": topic
                })

    return missing

    syllabus_sections = extract_course_sections(
        syllabus_text,
        "2. SYLLABUS"
    )

    notes_sections = extract_course_sections(
        notes_text,
        "3. COURSE NOTES AVAILABLE"
    )

    missing = []

    for course, syllabus_lines in syllabus_sections.items():

        syllabus_topics = extract_topics(
            syllabus_lines
        )

        notes_topics = extract_topics(
            notes_sections.get(
                course,
                []
            )
        )

        normalized_notes = {
            normalize_topic(topic)
            for topic in notes_topics
        }

        for topic in syllabus_topics:

            if normalize_topic(topic) not in normalized_notes:

                missing.append({
                    "course": course,
                    "topic": topic
                })

    return missing


# ---------------------------------------------------------
# Generate prioritized plan
# ---------------------------------------------------------

def generate_study_plan(
    transcript_text,
    syllabus_text,
    notes_text
):

    grades = extract_grades(
        transcript_text
    )

    weak_subjects = []

    # ---------------------------------------------
    # Weak subject detection
    # ---------------------------------------------

    for subject, information in grades.items():

        grade = information["grade"]
        marks = information["marks"]

        grade_value = GRADE_VALUES.get(
            grade,
            100
        )

        is_weak = False

        # Deterministic rules
        if marks is not None and marks < 75:
            is_weak = True

        elif grade_value < 75:
            is_weak = True

        if is_weak:

            weak_subjects.append({
                "subject": subject,
                "grade": grade,
                "marks": marks,
                "reason": "Lower academic performance"
            })

    # ---------------------------------------------
    # Missing topic detection
    # ---------------------------------------------

    missing_topics = find_missing_topics(
        syllabus_text,
        notes_text
    )

    # ---------------------------------------------
    # Priority generation
    # ---------------------------------------------

    plan = []

    priority = 1

    # Weak subjects first
    for subject in weak_subjects:

        plan.append({
            "priority": priority,
            "topic": subject["subject"],
            "reason": (
                f"Low performance: "
                f"{subject['grade']}"
            ),
            "suggested_time": "2-3 days"
        })

        priority += 1

    # Then missing syllabus topics
    for item in missing_topics:

        plan.append({
            "priority": priority,
            "topic": (
                f"{item['course']} - "
                f"{item['topic']}"
            ),
            "reason": (
                "Present in syllabus "
                "but missing from notes"
            ),
            "suggested_time": "1 day"
        })

        priority += 1

    # Keep the plan short
    plan = plan[:7]

    return {
        "grades": grades,
        "weak_subjects": weak_subjects,
        "missing_topics": missing_topics,
        "prioritized_plan": plan
    }


# ---------------------------------------------------------
# LangChain Tool
# ---------------------------------------------------------

@tool
def study_plan_generator(
    transcript_text: str,
    syllabus_text: str,
    notes_text: str
):
    """
    Automatically generate a prioritized study plan
    from the student's transcript, syllabus and notes.

    The tool uses deterministic logic to identify:
    1. Subjects with low grades or marks.
    2. Syllabus topics that are absent from the notes.

    It does not require the student to provide a topic
    or ask for a study plan.
    """

    return generate_study_plan(
        transcript_text,
        syllabus_text,
        notes_text
    )
    