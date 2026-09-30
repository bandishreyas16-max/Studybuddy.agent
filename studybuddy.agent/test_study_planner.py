from pathlib import Path

from document_processor import (
    load_pdf,
    extract_text
)

from study_planner import (
    generate_study_plan
)


# ------------------------------------------
# Find PDF
# ------------------------------------------

project_folder = Path(__file__).parent

pdf_path = (
    project_folder /
    "StudyBuddy_without_point_4.pdf"
)


# ------------------------------------------
# Load PDF
# ------------------------------------------

documents = load_pdf(
    str(pdf_path)
)

text = extract_text(
    documents
)


# ------------------------------------------
# For this test PDF:
#
# Transcript, syllabus and notes are
# contained in the same document.
# ------------------------------------------

# ------------------------------------------------
# Separate transcript, syllabus and notes
# ------------------------------------------------

def get_section(text, start_marker, end_marker=None):

    start = text.lower().find(
        start_marker.lower()
    )

    if start == -1:
        return ""

    start += len(start_marker)

    if end_marker:

        end = text.lower().find(
            end_marker.lower(),
            start
        )

        if end != -1:
            return text[start:end]

    return text[start:]


transcript_text = get_section(
    text,
    "1. STUDENT TRANSCRIPT",
    "2. SYLLABUS"
)

syllabus_text = get_section(
    text,
    "2. SYLLABUS",
    "3. COURSE NOTES AVAILABLE"
)

notes_text = get_section(
    text,
    "3. COURSE NOTES AVAILABLE"
)


# ------------------------------------------
# Generate plan
# ------------------------------------------

result = generate_study_plan(
    transcript_text,
    syllabus_text,
    notes_text
)


# ------------------------------------------
# Display grades
# ------------------------------------------

print("\n")
print("=" * 60)
print("GRADES")
print("=" * 60)

for subject, data in result["grades"].items():

    print(
        f"{subject}: "
        f"{data['grade']} "
        f"({data['marks']})"
    )


# ------------------------------------------
# Display weak subjects
# ------------------------------------------

print("\n")
print("=" * 60)
print("WEAK SUBJECTS")
print("=" * 60)

for subject in result["weak_subjects"]:

    print(
        f"{subject['subject']} | "
        f"Grade: {subject['grade']} | "
        f"Marks: {subject['marks']}"
    )


# ------------------------------------------
# Display missing topics
# ------------------------------------------

print("\n")
print("=" * 60)
print("MISSING TOPICS")
print("=" * 60)

for topic in result["missing_topics"]:

    print(
        f"{topic['course']} -> "
        f"{topic['topic']}"
    )


# ------------------------------------------
# Display prioritized plan
# ------------------------------------------

print("\n")
print("=" * 60)
print("PRIORITIZED STUDY PLAN")
print("=" * 60)

for item in result["prioritized_plan"]:

    print(
        f"{item['priority']}. "
        f"{item['topic']} | "
        f"{item['reason']} | "
        f"{item['suggested_time']}"
    )