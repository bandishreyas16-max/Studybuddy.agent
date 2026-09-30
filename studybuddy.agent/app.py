import streamlit as st
from recall_engine import (
    generate_explanation,
    check_recall,
    extract_recall_score,
)
from pathlib import Path
import hashlib
import re
import json


# ============================================================
# BACKEND IMPORTS
# ============================================================

from document_processor import (
    load_pdf,
    extract_text,
    split_documents,
    create_vector_store,
    get_retriever,
)

from study_planner import generate_study_plan
from agent import ask_question
from job_search import search_jobs_from_transcript
from daily_scheduler import create_daily_schedule


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="StudyBuddy",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "page": "🏠 Dashboard",
    "uploaded_file_name": None,
    "processed_file_name": None,
    "processed_file_hash": None,
    "transcript_text": "",
    "syllabus_text": "",
    "notes_text": "",
    "full_text": "",
    "documents": None,
    "retriever": None,
    "study_plan": [],
    "weak_subjects": [],
    "strong_subjects": [],
    "missing_topics": [],
    "daily_schedule": [],
    "study_days": 7,
    "plan_version": None,
    "jobs": [],
    "matched_skills": [],
    "job_location": "India",

    # Test Me
    "quiz_questions": [],
    "quiz_answers": {},
    "quiz_submitted": False,
    "quiz_score": 0,
    "quiz_generated": False,
    "quiz_weak_topics": [],
    "bookmarked_topics": [],
    "fresher_readiness": None,
    "skill_gap_analysis": None,

    # Explain → Hide → Recall
    "recall_topic": "",
    "recall_context": "",
    "recall_explanation": "",
    "recall_hidden": False,
    "recall_result": "",
    "recall_score": 0,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_filename(filename):
    """Return a safe local filename for uploaded files."""
    name = Path(str(filename or "study_material.pdf")).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name or "study_material.pdf"


def get_file_hash(file_bytes):
    if not file_bytes:
        return ""
    return hashlib.sha256(file_bytes).hexdigest()


def make_plan_version(text):
    if not text:
        return "empty"

    return hashlib.md5(
        text.encode("utf-8", errors="ignore")
    ).hexdigest()


def reset_progress():
    keys_to_delete = []

    for key in list(st.session_state.keys()):
        if str(key).startswith("progress_"):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]


def reset_quiz():
    st.session_state.quiz_questions = []
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_score = 0
    st.session_state.quiz_generated = False
    st.session_state.quiz_weak_topics = []


# ============================================================
# PDF SECTION EXTRACTION
# ============================================================

def extract_sections(full_text):
    if not full_text:
        return "", "", ""

    text = full_text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lower_text = text.lower()

    transcript_start = lower_text.find("student transcript")
    syllabus_start = lower_text.find("syllabus")
    notes_start = lower_text.find("course notes")

    transcript_text = ""

    if transcript_start != -1:
        start = transcript_start

        if syllabus_start != -1 and syllabus_start > start:
            end = syllabus_start
        else:
            end = len(text)

        transcript_text = text[start:end].strip()

    syllabus_text = ""

    if syllabus_start != -1:
        start = syllabus_start

        if notes_start != -1 and notes_start > start:
            end = notes_start
        else:
            end = len(text)

        syllabus_text = text[start:end].strip()

    notes_text = ""

    if notes_start != -1:
        notes_text = text[notes_start:].strip()

    if not transcript_text:
        transcript_text = text

    if not syllabus_text:
        syllabus_text = text

    if not notes_text:
        notes_text = text

    return transcript_text, syllabus_text, notes_text


# ============================================================
# STUDY PLAN HELPERS
# ============================================================

def normalize_study_plan(result):
    if result is None:
        return []

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        for key in [
            "plan",
            "study_plan",
            "prioritized_plan",
            "priorities",
        ]:
            value = result.get(key)

            if isinstance(value, list):
                return value

    return []


def safe_get_topic(item):
    if not isinstance(item, dict):
        return "Study Topic"

    return item.get(
        "topic",
        item.get(
            "subject",
            item.get("name", "Study Topic")
        )
    )


def safe_get_reason(item):
    if not isinstance(item, dict):
        return "Needs attention"

    return item.get("reason", "Needs attention")


def safe_get_priority(item):
    if not isinstance(item, dict):
        return 3

    try:
        return int(item.get("priority", 3))
    except Exception:
        return 3


# ============================================================
# SUBJECT PERFORMANCE
# ============================================================

def analyze_subject_performance(transcript_text, study_plan):
    weak_subjects = []
    strong_subjects = []

    def add_subject(
        target,
        subject,
        grade=None,
        marks=None,
        reason=""
    ):
        if not subject:
            return

        subject = str(subject).strip()
        subject = subject.strip(" :-|–—")

        if len(subject) < 2:
            return

        existing = {
            str(item.get("subject", "")).strip().lower()
            for item in target
            if isinstance(item, dict)
        }

        if subject.lower() in existing:
            return

        target.append({
            "subject": subject,
            "grade": grade or "N/A",
            "marks": marks or "",
            "reason": reason or "Needs improvement",
        })

    if transcript_text:
        text = transcript_text.replace("\r", "\n")
        lower_text = text.lower()

        transcript_start = lower_text.find("student transcript")
        syllabus_start = lower_text.find("syllabus")

        if transcript_start != -1:
            if syllabus_start != -1 and syllabus_start > transcript_start:
                transcript_section = text[transcript_start:syllabus_start]
            else:
                transcript_section = text[transcript_start:]
        else:
            transcript_section = text

        # Handles rows such as:
        # Python Programming A 88
        # Database Management Systems B+ 76
        pattern = re.compile(
            r"(?im)^\s*"
            r"(.+?)"
            r"\s+"
            r"(A\+|A-|A|B\+|B-|B|C\+|C-|C|D|F)"
            r"\s+"
            r"(\d+(?:\.\d+)?)"
            r"\s*$"
        )

        matches = pattern.findall(transcript_section)

        for subject, grade, marks in matches:
            subject = subject.strip()
            grade = grade.strip().upper()
            marks = marks.strip()

            if subject.lower() in {
                "course",
                "subject",
                "course grade marks",
                "grade",
                "marks",
            }:
                continue

            if grade in {"A", "A+"}:
                add_subject(
                    strong_subjects,
                    subject,
                    grade,
                    marks,
                    "Strong academic performance",
                )
            else:
                add_subject(
                    weak_subjects,
                    subject,
                    grade,
                    marks,
                    "Needs improvement",
                )

    # Use high-priority study-plan information as an additional signal.
    for item in study_plan:
        if not isinstance(item, dict):
            continue

        subject = item.get(
            "subject",
            item.get("topic", item.get("name", ""))
        )

        reason = str(item.get("reason", ""))
        priority = safe_get_priority(item)
        grade = item.get("grade")

        if not grade:
            match = re.search(
                r"\b(A\+|A-|A|B\+|B-|B|C\+|C-|C|D|F)\b",
                reason.upper(),
            )
            if match:
                grade = match.group(1)

        if priority == 1 and subject:
            found = False

            for existing in weak_subjects:
                if (
                    str(existing.get("subject", "")).strip().lower()
                    == str(subject).strip().lower()
                ):
                    found = True

                    if reason:
                        existing["reason"] = reason

                    break

            if not found:
                add_subject(
                    weak_subjects,
                    subject,
                    grade=grade,
                    reason=reason or "High priority area",
                )

    strong_names = {
        str(item.get("subject", "")).strip().lower()
        for item in strong_subjects
    }

    weak_subjects = [
        item
        for item in weak_subjects
        if str(item.get("subject", "")).strip().lower()
        not in strong_names
    ]

    return weak_subjects, strong_subjects


# ============================================================
# MISSING TOPICS
# ============================================================

def find_missing_topics(syllabus_text, notes_text):
    if not syllabus_text:
        return []

    syllabus_lower = syllabus_text.lower()
    notes_lower = notes_text.lower() if notes_text else ""

    known_topics = [
        "transactions",
        "acid properties",
        "deadlocks",
        "memory management",
        "transport layer",
        "dhcp",
        "rest apis",
        "authentication",
        "er model",
        "relational model",
        "sql and queries",
        "normalization",
        "joins",
        "indexing",
        "processes and threads",
        "cpu scheduling",
        "file systems",
        "osi model",
        "tcp/ip",
        "dns",
        "html",
        "css",
        "javascript",
        "variables and data types",
        "functions",
        "lists and dictionaries",
        "object-oriented programming",
        "file handling",
    ]

    display_names = {
        "acid properties": "ACID Properties",
        "sql and queries": "SQL and Queries",
        "tcp/ip": "TCP/IP",
        "rest apis": "REST APIs",
        "er model": "ER Model",
    }

    missing = []

    for topic in known_topics:
        if topic in syllabus_lower and topic not in notes_lower:
            missing.append(
                display_names.get(topic, topic.title())
            )

    return list(dict.fromkeys(missing))


# ============================================================
# SCHEDULE
# ============================================================

def create_schedule_from_plan(study_plan, days=7):
    if not study_plan:
        return []

    try:
        days = max(1, int(days))
    except Exception:
        days = 7

    try:
        schedule = create_daily_schedule(
            study_plan,
            days=days
        )

        if schedule:
            return schedule
    except Exception:
        pass

    schedule = []
    total_topics = len(study_plan)

    for day in range(1, days + 1):
        item = study_plan[(day - 1) % total_topics]

        topic = safe_get_topic(item)
        reason = safe_get_reason(item)
        priority = safe_get_priority(item)

        if priority == 1:
            activity = "Deep Study"
            task_1, task_1_time = "Concept learning", 45
            task_2, task_2_time = "Practice questions", 30
            task_3, task_3_time = "Quick revision", 15

        elif priority == 2:
            activity = "Focused Study"
            task_1, task_1_time = "Concept learning", 40
            task_2, task_2_time = "Practice", 35
            task_3, task_3_time = "Quick revision", 15

        else:
            activity = "Revision"
            task_1, task_1_time = "Revision", 35
            task_2, task_2_time = "Practice questions", 40
            task_3, task_3_time = "Self-test", 15

        schedule.append({
            "day": day,
            "topic": topic,
            "activity": activity,
            "reason": reason,
            "time": "90 minutes",
            "total_minutes": 90,
            "task_1": task_1,
            "task_1_time": task_1_time,
            "task_2": task_2,
            "task_2_time": task_2_time,
            "task_3": task_3,
            "task_3_time": task_3_time,
        })

    return schedule


# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

def display_subject_performance(weak_subjects, strong_subjects):
    st.subheader("📊 Subject Performance")

    weak_col, strong_col = st.columns(2)

    with weak_col:
        st.markdown("### 📉 Weak Subjects")

        if weak_subjects:
            for item in weak_subjects:
                subject = item.get("subject", "Unknown Subject")
                grade = item.get("grade", "N/A")
                marks = item.get("marks", "")
                reason = item.get("reason", "Needs improvement")

                with st.container(border=True):
                    st.markdown(f"### {subject}")

                    if marks:
                        st.write(
                            f"📊 Grade: **{grade}** | "
                            f"Marks: **{marks}**"
                        )
                    else:
                        st.write(f"📊 Grade: **{grade}**")

                    st.write(f"⚠️ {reason}")
        else:
            st.success("No weak subjects detected.")

    with strong_col:
        st.markdown("### 💪 Studying Well")

        if strong_subjects:
            for item in strong_subjects:
                subject = item.get("subject", "Unknown Subject")
                grade = item.get("grade", "N/A")
                marks = item.get("marks", "")

                with st.container(border=True):
                    st.markdown(f"### {subject}")

                    if marks:
                        st.write(
                            f"📊 Grade: **{grade}** | "
                            f"Marks: **{marks}**"
                        )
                    else:
                        st.write(f"📊 Grade: **{grade}**")

                    st.write("✅ Strong academic performance")
        else:
            st.info("No strong subjects were detected.")


def display_missing_topics(missing_topics):
    st.subheader("📚 Missing Topics")

    if missing_topics:
        st.write(
            "These syllabus topics were not found "
            "in the available course notes:"
        )

        for topic in missing_topics:
            st.markdown(f"- ⚠️ **{topic}**")
    else:
        st.success("No missing syllabus topics detected.")


def display_study_plan(study_plan):
    if not study_plan:
        st.info("No study plan is available yet.")
        return

    for index, item in enumerate(study_plan, start=1):
        topic = safe_get_topic(item)
        reason = safe_get_reason(item)
        priority = safe_get_priority(item)

        if isinstance(item, dict):
            suggested_time = item.get(
                "suggested_time",
                item.get("time", "1 day")
            )
        else:
            suggested_time = "1 day"

        if priority == 1:
            priority_label = "🔴 High Priority"
        elif priority == 2:
            priority_label = "🟠 Medium Priority"
        else:
            priority_label = "🟢 Normal Priority"

        with st.container(border=True):
            st.markdown(f"### {index}. {topic}")

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Priority:** {priority_label}")

            with col2:
                st.write(
                    f"**Suggested time:** {suggested_time}"
                )

            st.write(f"💡 **Why:** {reason}")


def show_progress_tracker(schedule):
    st.subheader("📊 Study Progress")

    if not schedule:
        st.info("Generate a study plan first.")
        return

    total_days = len(schedule)
    completed_days = 0

    st.markdown("### 📅 Daily Progress")

    plan_version = st.session_state.get(
        "plan_version",
        "current"
    )

    for index, item in enumerate(schedule, start=1):
        if not isinstance(item, dict):
            item = {"day": index, "topic": str(item)}

        day_number = item.get("day", index)
        topic = item.get("topic", "Study Topic")

        checkbox_key = (
            f"progress_{plan_version}_day_{day_number}"
        )

        completed = st.checkbox(
            f"Day {day_number} — {topic}",
            key=checkbox_key
        )

        if completed:
            completed_days += 1

    percentage = (
        int((completed_days / total_days) * 100)
        if total_days > 0
        else 0
    )

    remaining_days = total_days - completed_days

    st.divider()

    st.progress(
        percentage / 100,
        text=f"Progress: {percentage}%"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Completed", completed_days)

    with col2:
        st.metric("Remaining", remaining_days)

    with col3:
        st.metric("Progress", f"{percentage}%")

    st.divider()

    if percentage == 100:
        st.success(
            "🎉 Amazing! You completed your entire study plan!"
        )
    elif percentage >= 70:
        st.success("🔥 Great progress! Keep going.")
    elif percentage >= 40:
        st.info("💪 Good progress. Stay consistent.")
    else:
        st.warning("📚 Start completing your study days.")


# ============================================================
# TEST ME
# ============================================================

def extract_json_from_text(text):
    if not isinstance(text, str):
        return None

    cleaned = text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned
    )

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Try to locate a JSON object in surrounding text.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end > start:
        try:
            return json.loads(
                cleaned[start:end + 1]
            )
        except Exception:
            pass

    # Try JSON array.
    start = cleaned.find("[")
    end = cleaned.rfind("]")

    if start != -1 and end > start:
        try:
            return json.loads(
                cleaned[start:end + 1]
            )
        except Exception:
            pass

    return None


def normalize_quiz(result):
    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        for key in [
            "questions",
            "quiz",
            "items",
            "data",
        ]:
            value = result.get(key)

            if isinstance(value, list):
                return value

    if isinstance(result, str):
        parsed = extract_json_from_text(result)

        if isinstance(parsed, list):
            return parsed

        if isinstance(parsed, dict):
            for key in [
                "questions",
                "quiz",
                "items",
                "data",
            ]:
                value = parsed.get(key)

                if isinstance(value, list):
                    return value

    return []


def clean_quiz_question(question):
    if not isinstance(question, dict):
        return None

    question_text = question.get(
        "question",
        question.get("question_text", "")
    )

    if not question_text:
        return None

    options = question.get("options", {})
    cleaned_options = {}

    if isinstance(options, dict):
        for letter in ["A", "B", "C", "D"]:
            value = options.get(
                letter,
                options.get(letter.lower(), "")
            )

            if isinstance(value, dict):
                value = value.get(
                    "text",
                    value.get("label", "")
                )

            if value:
                cleaned_options[letter] = str(value)

    elif isinstance(options, list):
        for index, option in enumerate(options[:4]):
            letter = ["A", "B", "C", "D"][index]

            if isinstance(option, dict):
                value = option.get(
                    "text",
                    option.get("label", "")
                )
            else:
                value = str(option)

            if value:
                cleaned_options[letter] = value

    if set(cleaned_options.keys()) != {"A", "B", "C", "D"}:
        return None

    answer = question.get(
        "answer",
        question.get(
            "correct_answer",
            question.get("correct", "")
        )
    )

    if isinstance(answer, str):
        answer = answer.strip().upper()
        answer = answer.replace(".", "")

        if answer and answer[0] in "ABCD":
            answer = answer[0]

    if answer not in {"A", "B", "C", "D"}:
        return None

    topic = question.get(
        "topic",
        question.get(
            "subject",
            "General"
        )
    )

    explanation = question.get(
        "explanation",
        question.get(
            "reason",
            "Review this concept in your academic material."
        )
    )

    return {
        "question": str(question_text),
        "options": cleaned_options,
        "answer": answer,
        "topic": str(topic),
        "explanation": str(explanation),
    }


def generate_quiz_from_material():
    retriever = st.session_state.retriever

    if not retriever:
        return []

    quiz_prompt = """
You are the Test Me module inside StudyBuddy.

Use ONLY the student's uploaded academic material.

Create exactly 10 multiple-choice questions.

Requirements:
- Exactly 10 questions.
- Each question has exactly four options A, B, C, D.
- Exactly one option is correct.
- Use information supported by the uploaded material.
- Cover different subjects/topics where possible.
- Prioritize weak subjects, missing topics, syllabus topics,
  and course notes.
- Include a topic for every question.
- Include a short explanation for every answer.
- Do not invent source-specific facts.
- Do not include markdown fences.

Return ONLY this JSON structure:

{
  "questions": [
    {
      "question": "Question text",
      "options": {
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      },
      "answer": "A",
      "topic": "Operating Systems",
      "explanation": "Short explanation."
    }
  ]
}
"""

    last_error = None

    for attempt in range(3):
        try:
            attempt_prompt = quiz_prompt
            if attempt > 0:
                attempt_prompt += (
                    "\nIMPORTANT: Your previous response could not be parsed. "
                    "Return ONLY valid JSON with exactly 10 complete questions."
                )

            result = ask_question(
                attempt_prompt,
                retriever
            )

            raw_questions = normalize_quiz(result)
            cleaned_questions = []
            seen = set()

            for question in raw_questions:
                cleaned = clean_quiz_question(question)
                if not cleaned:
                    continue

                key = cleaned["question"].strip().lower()
                if key in seen:
                    continue

                seen.add(key)
                cleaned_questions.append(cleaned)

                if len(cleaned_questions) == 10:
                    return cleaned_questions

        except Exception as error:
            last_error = error

    if last_error is not None:
        st.error("Could not generate the quiz from the uploaded material. Please try again.")
        st.caption(f"Quiz detail: {type(last_error).__name__}")

    return []


def calculate_quiz_result():
    questions = st.session_state.quiz_questions
    answers = st.session_state.quiz_answers

    score = 0
    weak_topics = {}

    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            continue

        correct_answer = question.get("answer")
        selected_answer = answers.get(index)
        topic = question.get("topic", "General")

        if selected_answer == correct_answer:
            score += 1
        else:
            weak_topics[topic] = (
                weak_topics.get(topic, 0) + 1
            )

    st.session_state.quiz_score = score

    st.session_state.quiz_weak_topics = sorted(
        weak_topics.items(),
        key=lambda x: x[1],
        reverse=True
    )

    st.session_state.quiz_submitted = True


def display_quiz_result():
    questions = st.session_state.quiz_questions
    score = st.session_state.quiz_score
    total = len(questions)

    if total == 0:
        return

    percentage = int(
        (score / total) * 100
    )

    st.divider()

    st.subheader("🏆 Your Test Result")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Score",
            f"{score}/{total}"
        )

    with col2:
        st.metric(
            "Percentage",
            f"{percentage}%"
        )

    with col3:
        if percentage >= 80:
            status = "Excellent"
        elif percentage >= 60:
            status = "Good"
        elif percentage >= 40:
            status = "Needs Practice"
        else:
            status = "Needs Revision"

        st.metric(
            "Performance",
            status
        )

    st.progress(
        percentage / 100,
        text=f"Test Score: {percentage}%"
    )

    weak_topics = st.session_state.quiz_weak_topics

    if weak_topics:
        st.subheader("📉 Topics to Revise")

        for topic, mistakes in weak_topics:
            st.warning(
                f"**{topic}** — "
                f"{mistakes} question(s) incorrect"
            )
    else:
        st.success(
            "🎉 Excellent! You answered every "
            "question correctly."
        )

    st.subheader("📝 Answer Review")

    for index, question in enumerate(
        questions,
        start=1
    ):
        selected = st.session_state.quiz_answers.get(
            index - 1
        )

        correct = question.get("answer")

        if selected == correct:
            st.success(
                f"Question {index}: Correct ✓"
            )
        else:
            st.error(
                f"Question {index}: Incorrect ✗"
            )

            st.write(
                f"Your answer: "
                f"{selected or 'Not answered'}"
            )

            st.write(
                f"Correct answer: {correct}"
            )

        st.caption(
            question.get("explanation", "")
        )


# ============================================================
# FRESHER READINESS SCORE
# ============================================================

def calculate_fresher_readiness(transcript_text, syllabus_text, notes_text, study_plan, weak_subjects, strong_subjects, missing_topics):
    """Calculate a transparent readiness estimate from uploaded academic material.

    This is intentionally rule-based so the feature remains available even when
    an AI response is unavailable. It does not claim to be an employer assessment.
    """
    combined = "\n".join([transcript_text or "", syllabus_text or "", notes_text or ""]).lower()

    # Academic strength: based on subjects explicitly extracted from the transcript.
    total_subjects = len(weak_subjects) + len(strong_subjects)
    if total_subjects:
        academic = round((len(strong_subjects) / total_subjects) * 25)
    else:
        academic = 12

    # Core knowledge: study-plan coverage and missing-topic count.
    plan_count = len(study_plan)
    missing_count = len(missing_topics)
    if plan_count == 0 and missing_count == 0:
        knowledge = 12
    else:
        knowledge = 25
        if missing_count:
            knowledge -= min(12, missing_count * 2)
        if plan_count == 0:
            knowledge -= 4
        knowledge = max(0, min(25, knowledge))

    # Technical skills: look for evidence in the uploaded material.
    skill_keywords = {
        "python": "Python", "java": "Java", "sql": "SQL",
        "mysql": "MySQL", "mongodb": "MongoDB", "pandas": "Pandas",
        "numpy": "NumPy", "power bi": "Power BI", "excel": "Excel",
        "html": "HTML", "css": "CSS", "javascript": "JavaScript",
        "data science": "Data Science", "machine learning": "Machine Learning",
        "statistics": "Statistics", "data structures": "Data Structures",
        "database": "Databases", "git": "Git"
    }
    detected_skills = sorted({label for key, label in skill_keywords.items() if key in combined})
    technical = min(20, round(len(detected_skills) / 8 * 20))

    # Project readiness: only award points when the uploaded material contains
    # explicit project/practical evidence.
    project_terms = ["project", "mini project", "capstone", "internship", "practical", "github"]
    project_evidence = sum(1 for term in project_terms if term in combined)
    project = min(15, project_evidence * 3)

    # Job readiness: evidence of career-oriented preparation in the material.
    career_terms = ["resume", "cv", "job", "internship", "placement", "interview", "skills"]
    career_evidence = sum(1 for term in career_terms if term in combined)
    career = min(15, 3 + career_evidence * 2)

    total = max(0, min(100, academic + knowledge + technical + project + career))

    if total >= 80:
        level = "Strong foundation"
    elif total >= 60:
        level = "Developing"
    elif total >= 40:
        level = "Needs focused preparation"
    else:
        level = "Early preparation stage"

    gaps = []
    if weak_subjects:
        gaps.append("Strengthen weak subjects")
    if missing_topics:
        gaps.append("Complete missing syllabus topics")
    if technical < 12:
        gaps.append("Build more practical technical skills")
    if project < 9:
        gaps.append("Build or document a project")
    if career < 9:
        gaps.append("Prepare resume and interview skills")

    return {
        "score": total,
        "level": level,
        "academic": academic,
        "knowledge": knowledge,
        "technical": technical,
        "project": project,
        "career": career,
        "skills": detected_skills,
        "gaps": gaps[:5],
    }


def display_fresher_readiness(data):
    if not data:
        st.info("Upload your academic material to calculate your Fresher Readiness Score.")
        return

    score = int(data.get("score", 0))
    level = data.get("level", "Not available")

    st.subheader("🚀 Fresher Readiness Score")
    st.caption("An academic-material-based estimate, not an employer assessment.")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.metric("Readiness", f"{score}/100")
    with c2:
        st.metric("Level", level)
    with c3:
        st.progress(score / 100)
        st.caption(f"Current readiness estimate: {score}%")

    st.markdown("### 📊 Readiness Breakdown")
    b1, b2, b3, b4, b5 = st.columns(5)
    metrics = [
        (b1, "📚 Academic", data.get("academic", 0), 25),
        (b2, "🧠 Knowledge", data.get("knowledge", 0), 25),
        (b3, "💻 Technical", data.get("technical", 0), 20),
        (b4, "🛠️ Project", data.get("project", 0), 15),
        (b5, "💼 Career", data.get("career", 0), 15),
    ]
    for col, label, value, maximum in metrics:
        with col:
            st.metric(label, f"{value}/{maximum}")

    if data.get("skills"):
        st.markdown("### 💻 Skills Found in Your Material")
        st.write(" • ".join(data["skills"]))

    if data.get("gaps"):
        st.markdown("### 🎯 Recommended Next Steps")
        for gap in data["gaps"]:
            st.write(f"• {gap}")


# ============================================================
# SKILL GAP ANALYZER
# ============================================================

ROLE_SKILLS = {
    "Data Analyst": [
        "Python", "SQL", "Pandas", "NumPy", "Statistics",
        "Excel", "Power BI", "Data Visualization", "Git"
    ],
    "Data Scientist": [
        "Python", "SQL", "Pandas", "NumPy", "Statistics",
        "Machine Learning", "Data Visualization", "Git"
    ],
    "Python Developer": [
        "Python", "OOP", "Data Structures", "SQL", "Git",
        "APIs", "Testing"
    ],
    "Software Developer": [
        "Java", "Python", "Data Structures", "OOP", "SQL",
        "Git", "APIs", "Testing"
    ],
    "Web Developer": [
        "HTML", "CSS", "JavaScript", "SQL", "APIs",
        "Git", "Authentication"
    ],
    "Business Intelligence Analyst": [
        "SQL", "Excel", "Power BI", "Statistics", "Data Visualization",
        "Python", "Data Modeling"
    ],
}

SKILL_ALIASES = {
    "python": "Python", "java": "Java", "sql": "SQL", "mysql": "MySQL",
    "mongodb": "MongoDB", "pandas": "Pandas", "numpy": "NumPy",
    "power bi": "Power BI", "excel": "Excel", "html": "HTML", "css": "CSS",
    "javascript": "JavaScript", "data science": "Data Science",
    "machine learning": "Machine Learning", "statistics": "Statistics",
    "data structures": "Data Structures", "database": "Databases",
    "git": "Git", "github": "Git", "oop": "OOP", "object oriented": "OOP",
    "api": "APIs", "rest api": "APIs", "rest apis": "APIs",
    "authentication": "Authentication", "testing": "Testing",
    "data visualization": "Data Visualization", "data modelling": "Data Modeling",
    "data modeling": "Data Modeling", "visualization": "Data Visualization",
}


def detect_material_skills(text):
    combined = (text or "").lower()
    found = set()
    for key, label in SKILL_ALIASES.items():
        if re.search(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])", combined):
            found.add(label)
    return sorted(found)


def calculate_skill_gap_analysis(full_text, weak_subjects, strong_subjects, missing_topics, target_role):
    """Create a transparent skill-gap comparison from uploaded material."""
    required = ROLE_SKILLS.get(target_role, [])
    found = detect_material_skills(full_text)
    found_lower = {x.lower() for x in found}

    learned = []
    partial = []
    missing = []

    for skill in required:
        sl = skill.lower()
        if sl in found_lower:
            learned.append(skill)
        elif any(sl in topic.lower() for topic in (missing_topics or [])):
            partial.append(skill)
        else:
            partial_signals = {
                "Data Visualization": ["power bi", "excel", "visualization", "matplotlib"],
                "APIs": ["api", "rest"],
                "Authentication": ["authentication", "login", "security"],
                "Testing": ["testing", "test cases", "unit test"],
                "Data Modeling": ["database", "data model", "modeling"],
                "OOP": ["object oriented", "class", "inheritance", "polymorphism"],
            }
            signals = partial_signals.get(skill, [])
            if any(signal in (full_text or "").lower() for signal in signals):
                partial.append(skill)
            else:
                missing.append(skill)

    priority = []
    for skill in missing:
        if skill not in priority:
            priority.append(skill)
    for skill in partial:
        if skill not in priority:
            priority.append(skill)

    if missing_topics:
        for topic in missing_topics:
            if topic and topic not in priority:
                priority.append(topic)

    total_required = len(required)
    readiness = round((len(learned) + 0.5 * len(partial)) / total_required * 100) if total_required else 0
    readiness = max(0, min(100, readiness))

    return {
        "role": target_role,
        "required": required,
        "learned": learned,
        "partial": partial,
        "missing": missing,
        "priority": priority[:8],
        "coverage": readiness,
        "material_skills": found,
        "weak_subjects": weak_subjects or [],
        "strong_subjects": strong_subjects or [],
    }


def display_skill_gap_analysis(data):
    if not data:
        st.info("Upload your academic material to analyze your skill gap.")
        return

    role = data.get("role", "Target role")
    coverage = int(data.get("coverage", 0))

    st.subheader(f"🔍 Skill Gap Analyzer — {role}")
    st.caption("The comparison is based on skills evidenced in your uploaded material and the selected role's predefined skill set.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Skill Coverage", f"{coverage}%")
    with c2:
        st.metric("Skills Learned", len(data.get("learned", [])))
    with c3:
        st.metric("Skills Missing", len(data.get("missing", [])))

    st.progress(coverage / 100)

    left, middle, right = st.columns(3)
    with left:
        st.markdown("### ✅ Learned")
        if data.get("learned"):
            for skill in data["learned"]:
                st.success(skill)
        else:
            st.info("No required skills were clearly detected yet.")

    with middle:
        st.markdown("### 🟡 Needs Practice")
        if data.get("partial"):
            for skill in data["partial"]:
                st.warning(skill)
        else:
            st.info("No partial skills detected.")

    with right:
        st.markdown("### ❌ Missing")
        if data.get("missing"):
            for skill in data["missing"]:
                st.error(skill)
        else:
            st.success("No missing required skills detected.")

    st.divider()
    st.markdown("### 🔥 Priority Learning List")
    if data.get("priority"):
        for number, item in enumerate(data["priority"], 1):
            st.write(f"**{number}.** {item}")
    else:
        st.success("Your selected role has no immediate skill-gap items from the available evidence.")

    if data.get("material_skills"):
        st.markdown("### 📚 Skills Detected in Your Material")
        st.write(" • ".join(data["material_skills"]))



# ============================================================
# TOPIC BOOKMARKS
# ============================================================

def add_bookmark(topic, subject="", note=""):
    """Add a topic to the bookmark list if it is not already saved."""
    topic = str(topic or "").strip()
    subject = str(subject or "").strip()
    note = str(note or "").strip()

    if not topic:
        return False, "Topic cannot be empty."

    bookmarks = st.session_state.get("bookmarked_topics", [])

    for bookmark in bookmarks:
        if str(bookmark.get("topic", "")).strip().lower() == topic.lower():
            return False, "This topic is already bookmarked."

    from datetime import datetime

    bookmarks.append(
        {
            "topic": topic,
            "subject": subject,
            "note": note,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    )

    st.session_state.bookmarked_topics = bookmarks
    return True, "Topic bookmarked successfully."


def remove_bookmark(index):
    """Remove a bookmark by its current list index."""
    bookmarks = st.session_state.get("bookmarked_topics", [])

    if 0 <= index < len(bookmarks):
        bookmarks.pop(index)
        st.session_state.bookmarked_topics = bookmarks
        return True

    return False


def toggle_bookmark_complete(index):
    """Toggle a bookmark between incomplete and completed."""
    bookmarks = st.session_state.get("bookmarked_topics", [])

    if 0 <= index < len(bookmarks):
        current = bool(bookmarks[index].get("completed", False))
        bookmarks[index]["completed"] = not current
        st.session_state.bookmarked_topics = bookmarks
        return True

    return False


def display_bookmarks_page():
    """Render the Topic Bookmarks page safely."""
    st.header("🔖 Bookmarked Topics")
    st.write(
        "Save important topics and return to them whenever you need revision."
    )

    bookmarks = st.session_state.get("bookmarked_topics", [])

    # Add a new bookmark.
    st.subheader("➕ Add a Bookmark")

    with st.form("add_bookmark_form", clear_on_submit=True):
        topic = st.text_input(
            "Topic",
            placeholder="Example: Database Transactions",
        )

        subject = st.text_input(
            "Subject",
            placeholder="Example: DBMS",
        )

        note = st.text_area(
            "Revision Note (optional)",
            placeholder="Example: Revise ACID properties and examples.",
        )

        submitted = st.form_submit_button(
            "🔖 Save Topic",
            use_container_width=True,
        )

        if submitted:
            success, message = add_bookmark(
                topic,
                subject,
                note,
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.warning(message)

    st.divider()

    bookmarks = st.session_state.get("bookmarked_topics", [])

    total = len(bookmarks)
    completed = sum(
        1 for item in bookmarks
        if bool(item.get("completed", False))
    )
    incomplete = total - completed

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric("📚 Total", total)

    with metric2:
        st.metric("⏳ To Revise", incomplete)

    with metric3:
        st.metric("✅ Completed", completed)

    if not bookmarks:
        st.info(
            "No bookmarked topics yet. Add an important topic above "
            "to build your revision list."
        )
        return

    st.divider()
    st.subheader("📌 Your Bookmarks")

    search_text = st.text_input(
        "🔎 Search bookmarks",
        placeholder="Search by topic, subject, or note...",
    ).strip().lower()

    filter_option = st.selectbox(
        "Filter",
        ["All", "Incomplete", "Completed"],
    )

    visible_bookmarks = []

    for index, bookmark in enumerate(bookmarks):
        topic_text = str(bookmark.get("topic", ""))
        subject_text = str(bookmark.get("subject", ""))
        note_text = str(bookmark.get("note", ""))
        is_completed = bool(bookmark.get("completed", False))

        if filter_option == "Incomplete" and is_completed:
            continue

        if filter_option == "Completed" and not is_completed:
            continue

        combined_text = (
            f"{topic_text} {subject_text} {note_text}"
        ).lower()

        if search_text and search_text not in combined_text:
            continue

        visible_bookmarks.append((index, bookmark))

    if not visible_bookmarks:
        st.info("No bookmarks match your current search/filter.")
        return

    for index, bookmark in visible_bookmarks:
        topic_text = str(bookmark.get("topic", "Untitled Topic"))
        subject_text = str(bookmark.get("subject", ""))
        note_text = str(bookmark.get("note", ""))
        created_at = str(bookmark.get("created_at", ""))
        is_completed = bool(bookmark.get("completed", False))

        with st.container(border=True):
            title_prefix = "✅" if is_completed else "📌"
            st.markdown(f"### {title_prefix} {topic_text}")

            if subject_text:
                st.write(f"📚 **Subject:** {subject_text}")

            if note_text:
                st.write(f"📝 **Note:** {note_text}")

            if created_at:
                st.caption(f"Saved: {created_at}")

            action1, action2 = st.columns(2)

            with action1:
                button_label = (
                    "↩️ Mark Incomplete"
                    if is_completed
                    else "✅ Mark Complete"
                )

                if st.button(
                    button_label,
                    key=f"bookmark_toggle_{index}",
                    use_container_width=True,
                ):
                    toggle_bookmark_complete(index)
                    st.rerun()

            with action2:
                if st.button(
                    "🗑️ Remove",
                    key=f"bookmark_remove_{index}",
                    use_container_width=True,
                ):
                    remove_bookmark(index)
                    st.rerun()


# ============================================================
# EXPLAIN LIKE I'M A BEGINNER
# ============================================================

def generate_beginner_explanation(topic, style, extra_instruction=""):
    """Generate a beginner-friendly explanation using the uploaded material."""
    retriever = st.session_state.get("retriever")

    if not retriever:
        return None, "Please upload your academic material first."

    topic = str(topic or "").strip()
    if not topic:
        return None, "Please enter a topic to explain."

    style_instructions = {
        "🟢 Simple Explanation": (
            "Use very simple words. Assume the student is seeing the topic for the first time."
        ),
        "🧒 Explain Like I'm 10": (
            "Explain it as if you are teaching a 10-year-old. Use a simple analogy and avoid unnecessary technical words."
        ),
        "🌍 Real-Life Example": (
            "Start with a real-life example or analogy, then connect that example to the academic concept."
        ),
        "📝 Exam Preparation": (
            "Explain simply first, then give exam-ready key points and a short answer the student can remember."
        ),
        "🎯 Interview Preparation": (
            "Explain the concept simply, then give the important points a fresher should know for an interview."
        ),
    }

    style_instruction = style_instructions.get(
        style,
        style_instructions["🟢 Simple Explanation"],
    )

    prompt = f"""
You are StudyBuddy's Explain Like I'm a Beginner teacher.

The student wants to understand this topic:
{topic}

Explanation style:
{style_instruction}

IMPORTANT SOURCE RULE:
Use ONLY information supported by the student's uploaded academic material.
Do not invent course-specific facts. If the uploaded material does not contain
information needed to answer the topic, clearly say that the material does not
provide enough information instead of pretending it does.

Write the response in beginner-friendly English.
Avoid unnecessarily complicated vocabulary.
Use short paragraphs and clear headings.

Return the explanation in this structure:

## 📌 Simple Definition
Give a short definition based on the uploaded material.

## 💡 Easy Explanation
Explain the idea step by step in simple language.

## 🌍 Simple Example
Give an example or analogy only when it is supported by, or safely illustrates,
the concept without adding unsupported course-specific facts.

## 🧠 Key Points to Remember
Give 3 to 6 important points.

## 📝 Quick Revision
Give a 2 to 4 sentence revision summary.

If the selected style is Exam Preparation, also add:
## ✍️ Exam Answer
Give a concise exam-ready answer based only on the material.

If the selected style is Interview Preparation, also add:
## 🎤 Interview Points
Give the most important beginner-level interview points supported by the material.

Extra student instruction:
{extra_instruction or "None"}
"""

    try:
        answer = ask_question(prompt, retriever)

        if answer is None or not str(answer).strip():
            return None, "StudyBuddy could not generate an explanation. Please try again."

        return str(answer).strip(), None

    except Exception as error:
        return None, f"Could not generate the explanation ({type(error).__name__}). Please try again."


def display_beginner_explanation_page():
    """Render the Explain Like I'm a Beginner feature."""
    st.header("🧑‍🏫 Explain Like I'm a Beginner")
    st.write(
        "Enter a difficult topic and StudyBuddy will explain it in simple language "
        "using your uploaded academic material."
    )

    if not st.session_state.get("retriever"):
        st.info(
            "📚 Please upload your academic PDF from the Dashboard first."
        )
        return

    st.success("✅ Your academic material is ready for beginner-friendly explanations.")

    topic = st.text_area(
        "📚 What topic do you want to understand?",
        placeholder=(
            "Example: What is normalization in DBMS?\n"
            "Example: Explain deadlocks in Operating Systems."
        ),
        height=120,
        key="beginner_topic_input",
    )

    style = st.selectbox(
        "🎨 How should I explain it?",
        [
            "🟢 Simple Explanation",
            "🧒 Explain Like I'm 10",
            "🌍 Real-Life Example",
            "📝 Exam Preparation",
            "🎯 Interview Preparation",
        ],
        key="beginner_explanation_style",
    )

    extra_instruction = st.text_input(
        "➕ Optional instruction",
        placeholder="Example: Keep it very short and easy to remember.",
        key="beginner_extra_instruction",
    )

    if st.button(
        "🧑‍🏫 Explain This Topic",
        type="primary",
        use_container_width=True,
    ):
        if not topic.strip():
            st.warning("Please enter a topic first.")
        else:
            with st.spinner("Preparing a simple explanation from your material..."):
                answer, error_message = generate_beginner_explanation(
                    topic,
                    style,
                    extra_instruction,
                )

            if error_message:
                st.error(error_message)
            else:
                st.divider()
                st.subheader("💬 StudyBuddy's Explanation")
                st.markdown(answer)
                st.caption(
                    "📚 This explanation is grounded in your uploaded academic material."
                )

# ============================================================
# SIDEBAR — Card-style navigation
# ============================================================

# Inject global CSS for the sidebar cards and brand
st.markdown(
    """
    <style>
    /* ---- Brand section ---- */
    .sb-brand {
        text-align: center;
        padding: 18px 8px 10px 8px;
    }
    .sb-brand-title {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0;
        line-height: 1.2;
    }
    .sb-brand-study { color: #ffffff; }
    .sb-brand-buddy { color: #4da6ff; }
    .sb-brand-subtitle {
        font-size: 0.78rem;
        color: #8ab4d8;
        margin-top: 4px;
        display: block;
    }

    /* ---- Section label ---- */
    .sb-nav-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #5a80a0;
        padding: 4px 4px 6px 4px;
        margin-top: 6px;
    }

    /* ---- Nav card buttons ---- */
    div[data-testid="stSidebar"] button.sb-nav-btn {
        display: block;
        width: 100%;
        background: #0d1b2a;
        color: #e8f0f7;
        border: 1.5px solid #1e3a5f;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 7px;
        font-size: 0.88rem;
        font-weight: 500;
        text-align: left;
        cursor: pointer;
        transition: border-color 0.18s, box-shadow 0.18s, transform 0.12s;
    }
    div[data-testid="stSidebar"] button.sb-nav-btn:hover {
        border-color: #4da6ff;
        box-shadow: 0 0 8px rgba(77, 166, 255, 0.35);
        transform: translateY(-1px);
        color: #ffffff;
    }
    div[data-testid="stSidebar"] button.sb-nav-btn-active {
        border-color: #4da6ff;
        background: #0f2035;
        color: #4da6ff;
        font-weight: 700;
        box-shadow: 0 0 10px rgba(77, 166, 255, 0.25);
    }

    /* Streamlit overrides for sidebar buttons */
    div[data-testid="stSidebar"] .stButton > button {
        background: #0d1b2a;
        color: #e8f0f7;
        border: 1.5px solid #1e3a5f;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 4px;
        font-size: 0.88rem;
        font-weight: 500;
        text-align: left;
        width: 100%;
        transition: border-color 0.18s, box-shadow 0.18s, transform 0.12s;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #4da6ff !important;
        box-shadow: 0 0 8px rgba(77, 166, 255, 0.35) !important;
        transform: translateY(-1px);
        color: #ffffff !important;
    }

    /* ---- Info card at bottom ---- */
    .sb-info-card {
        background: #0a2240;
        border: 1.5px solid #1e5080;
        border-radius: 10px;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 0.8rem;
        color: #8ab4d8;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

_NAV_PAGES = [
    ("🏠", "Dashboard",              "🏠 Dashboard"),
    ("🎯", "Study Plan",             "🎯 Study Plan"),
    ("📊", "Progress Tracker",       "📊 Progress Tracker"),
    ("🚀", "Fresher Readiness",      "🚀 Fresher Readiness"),
    ("🔍", "Skill Gap Analyzer",     "🔍 Skill Gap Analyzer"),
    ("📚", "Explain Like I'm a Beginner", "📚 Explain Like I'm a Beginner"),
    ("🧠", "Explain → Hide → Recall", "🧠 Explain → Hide → Recall"),
    ("🧪", "Test Me",                "🧪 Test Me"),
    ("🤖", "Ask AI",                 "🤖 Ask AI"),
    ("💼", "Jobs & Internships",     "💼 Jobs & Internships"),
    ("🔖", "Bookmarked Topics",      "🔖 Bookmarked Topics"),
    ("📁", "My Files",              "📁 My Files"),
]

with st.sidebar:
    # ---- Brand ----
    st.markdown(
        """
        <div class="sb-brand">
            <p class="sb-brand-title">
                🎓&nbsp;<span class="sb-brand-study">Study</span><span class="sb-brand-buddy">Buddy</span>
            </p>
            <span class="sb-brand-subtitle">Your Academic + Career Copilot</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ---- Navigation label ----
    st.markdown(
        '<div class="sb-nav-label">Navigation</div>',
        unsafe_allow_html=True,
    )

    # ---- Nav buttons ----
    for _icon, _label, _key in _NAV_PAGES:
        _is_active = (st.session_state.page == _key)
        _btn_label = f"{_icon}  {_label}"
        if st.button(
            _btn_label,
            key=f"nav_btn_{_key}",
            use_container_width=True,
        ):
            st.session_state.page = _key
            st.rerun()

    # ---- Info card ----
    st.markdown(
        """
        <div class="sb-info-card">
            💡 Upload your academic material to begin.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Resolve active page
# ============================================================

page = st.session_state.get("page", "🏠 Dashboard")


# ============================================================
# HEADER — shown only on Dashboard
# ============================================================

if page == "🏠 Dashboard":
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <h1 style="margin-bottom:0;font-size:2.2rem;font-weight:800;">
                🎓 <span style="color:#ffffff;">Study</span><span style="color:#4da6ff;">Buddy</span>
            </h1>
            <p style="color:#8ab4d8;margin-top:2px;font-size:1rem;">
                Academic + Career Copilot
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        "Upload your academic material and StudyBuddy will identify "
        "weak areas, find missing topics, create a personalized study "
        "plan, test your knowledge, and connect your learning with "
        "career opportunities."
    )

    # Feature badges
    _b1, _b2, _b3, _b4 = st.columns(4)
    with _b1:
        st.markdown(
            '<div style="background:#0d1b2a;border:1.5px solid #1e3a5f;border-radius:10px;'
            'padding:10px;text-align:center;font-size:0.85rem;color:#8ab4d8;">'
            '📘 Smart Study Plan</div>',
            unsafe_allow_html=True,
        )
    with _b2:
        st.markdown(
            '<div style="background:#0d1b2a;border:1.5px solid #1e3a5f;border-radius:10px;'
            'padding:10px;text-align:center;font-size:0.85rem;color:#8ab4d8;">'
            '📊 Track Progress</div>',
            unsafe_allow_html=True,
        )
    with _b3:
        st.markdown(
            '<div style="background:#0d1b2a;border:1.5px solid #1e3a5f;border-radius:10px;'
            'padding:10px;text-align:center;font-size:0.85rem;color:#8ab4d8;">'
            '💡 AI Explanations</div>',
            unsafe_allow_html=True,
        )
    with _b4:
        st.markdown(
            '<div style="background:#0d1b2a;border:1.5px solid #1e3a5f;border-radius:10px;'
            'padding:10px;text-align:center;font-size:0.85rem;color:#8ab4d8;">'
            '💼 Career Guidance</div>',
            unsafe_allow_html=True,
        )

    st.divider()


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.header("🏠 Dashboard")

    st.subheader(
        "Upload your academic material"
    )

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        help=(
            "Upload your transcript, syllabus, "
            "or course notes."
        ),
    )

    if uploaded_file is not None:

        current_file_name = safe_filename(uploaded_file.name)
        file_bytes = uploaded_file.getvalue()
        current_file_hash = get_file_hash(file_bytes)

        previous_file_name = st.session_state.uploaded_file_name
        previous_file_hash = st.session_state.processed_file_hash

        is_new_file = (
            current_file_hash != previous_file_hash
            or current_file_name != previous_file_name
        )

        if is_new_file:

            with st.spinner(
                "Processing your academic material..."
            ):

                try:

                    data_directory = (
                        Path(__file__).parent / "data"
                    )

                    data_directory.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    file_path = (
                        data_directory / current_file_name
                    )

                    with open(
                        file_path,
                        "wb"
                    ) as file:
                        file.write(file_bytes)

                    loaded_documents = load_pdf(
                        str(file_path)
                    )

                    full_text = extract_text(
                        loaded_documents
                    )

                    if not full_text:
                        st.error(
                            "No readable text was found in this PDF."
                        )
                        st.stop()

                    chunks = split_documents(
                        loaded_documents
                    )

                    vector_store = create_vector_store(
                        chunks
                    )

                    retriever = get_retriever(
                        vector_store
                    )

                    (
                        transcript_text,
                        syllabus_text,
                        notes_text,
                    ) = extract_sections(
                        full_text
                    )

                    study_result = generate_study_plan(
                        transcript_text,
                        syllabus_text,
                        notes_text
                    )

                    study_plan = normalize_study_plan(
                        study_result
                    )

                    (
                        weak_subjects,
                        strong_subjects,
                    ) = analyze_subject_performance(
                        transcript_text,
                        study_plan
                    )

                    missing_topics = find_missing_topics(
                        syllabus_text,
                        notes_text
                    )

                    readiness = calculate_fresher_readiness(
                        transcript_text,
                        syllabus_text,
                        notes_text,
                        study_plan,
                        weak_subjects,
                        strong_subjects,
                        missing_topics,
                    )

                    st.session_state.uploaded_file_name = (
                        current_file_name
                    )

                    st.session_state.processed_file_name = (
                        current_file_name
                    )
                    st.session_state.processed_file_hash = (
                        current_file_hash
                    )

                    st.session_state.full_text = full_text
                    st.session_state.transcript_text = (
                        transcript_text
                    )
                    st.session_state.syllabus_text = (
                        syllabus_text
                    )
                    st.session_state.notes_text = notes_text
                    st.session_state.documents = (
                        loaded_documents
                    )
                    st.session_state.retriever = retriever
                    st.session_state.study_plan = study_plan
                    st.session_state.weak_subjects = weak_subjects
                    st.session_state.strong_subjects = strong_subjects
                    st.session_state.missing_topics = missing_topics
                    st.session_state.fresher_readiness = readiness
                    st.session_state.skill_gap_analysis = None

                    st.session_state.plan_version = (
                        make_plan_version(full_text)
                    )

                    reset_progress()
                    reset_quiz()

                    st.session_state.study_days = 7

                    st.session_state.daily_schedule = (
                        create_schedule_from_plan(
                            study_plan,
                            days=7
                        )
                    )

                    st.session_state.jobs = []
                    st.session_state.matched_skills = []

                    st.success(
                        "✅ Your academic material has "
                        "been processed successfully!"
                    )

                    if study_plan:
                        st.success(
                            "🎯 Your personalized study plan "
                            "has been generated automatically."
                        )
                    else:
                        st.warning(
                            "The PDF was processed, but "
                            "a study plan could not be generated."
                        )

                except Exception as error:

                    st.error(
                        "❌ Could not process this PDF. Please check that it is a readable PDF and try again."
                    )
                    st.caption(f"Processing detail: {type(error).__name__}")

        else:

            st.info(
                f"📄 {current_file_name} is already loaded."
            )

    if st.session_state.processed_file_name:

        st.divider()

        st.subheader(
            "📌 Academic Material Status"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Document", "Loaded")

        with col2:
            st.metric(
                "Study Plan",
                (
                    "Ready"
                    if st.session_state.study_plan
                    else "Not Ready"
                )
            )

        with col3:
            st.metric(
                "Study Days",
                len(
                    st.session_state.daily_schedule
                )
            )

        with col4:
            st.metric(
                "Q&A",
                (
                    "Ready"
                    if st.session_state.retriever
                    else "Not Ready"
                )
            )

        st.divider()

        display_subject_performance(
            st.session_state.weak_subjects,
            st.session_state.strong_subjects
        )

        st.divider()

        display_missing_topics(
            st.session_state.missing_topics
        )

        st.divider()

        display_fresher_readiness(
            st.session_state.fresher_readiness
        )

        st.divider()

        if st.session_state.study_plan:

            st.subheader(
                "🎯 Your Priority Study Plan"
            )

            display_study_plan(
                st.session_state.study_plan
            )


# ============================================================
# STUDY PLAN
# ============================================================

elif page == "🎯 Study Plan":

    st.header(
        "🎯 Personalized Study Plan"
    )

    if not st.session_state.study_plan:

        st.info(
            "Please upload your academic PDF "
            "from the Dashboard first."
        )

    else:

        display_subject_performance(
            st.session_state.weak_subjects,
            st.session_state.strong_subjects
        )

        st.divider()

        display_missing_topics(
            st.session_state.missing_topics
        )

        st.divider()

        st.subheader(
            "🎯 Priority Study Plan"
        )

        display_study_plan(
            st.session_state.study_plan
        )

        st.divider()

        st.subheader(
            "📅 Smart Daily Study Schedule"
        )

        number_of_days = st.slider(
            "How many days do you want to study?",
            min_value=3,
            max_value=14,
            value=st.session_state.study_days,
            step=1,
        )

        if number_of_days != st.session_state.study_days:

            st.session_state.study_days = number_of_days

            reset_progress()

            st.session_state.daily_schedule = (
                create_schedule_from_plan(
                    st.session_state.study_plan,
                    days=number_of_days
                )
            )

        schedule = st.session_state.daily_schedule

        if not schedule:

            st.warning(
                "No daily schedule could be generated."
            )

        else:

            for day in schedule:

                day_number = day.get("day", "?")
                topic = day.get("topic", "Study Topic")
                activity = day.get("activity", "Study")
                reason = day.get("reason", "Needs attention")
                total_minutes = day.get(
                    "total_minutes",
                    90
                )

                with st.container(border=True):

                    st.markdown(
                        f"## 📚 Day {day_number} — {topic}"
                    )

                    st.write(
                        f"🎯 **Activity:** {activity}"
                    )

                    st.write(
                        f"⏱️ **Total study time:** "
                        f"{total_minutes} minutes"
                    )

                    st.write(
                        f"💡 **Why this topic:** {reason}"
                    )

                    st.divider()

                    task_1 = day.get(
                        "task_1",
                        "Concept learning"
                    )
                    task_1_time = day.get(
                        "task_1_time",
                        45
                    )

                    task_2 = day.get(
                        "task_2",
                        "Practice"
                    )
                    task_2_time = day.get(
                        "task_2_time",
                        30
                    )

                    task_3 = day.get(
                        "task_3",
                        "Revision"
                    )
                    task_3_time = day.get(
                        "task_3_time",
                        15
                    )

                    st.write(
                        f"1️⃣ **{task_1}** — "
                        f"{task_1_time} minutes"
                    )

                    st.write(
                        f"2️⃣ **{task_2}** — "
                        f"{task_2_time} minutes"
                    )

                    st.write(
                        f"3️⃣ **{task_3}** — "
                        f"{task_3_time} minutes"
                    )


# ============================================================
# PROGRESS TRACKER
# ============================================================

elif page == "📊 Progress Tracker":

    st.header(
        "📊 Study Progress"
    )

    if not st.session_state.daily_schedule:

        st.info(
            "Please upload your academic PDF "
            "and generate a study plan first."
        )

    else:

        show_progress_tracker(
            st.session_state.daily_schedule
        )


# ============================================================
# SKILL GAP ANALYZER PAGE
# ============================================================

elif page == "🔍 Skill Gap Analyzer":

    st.header("🔍 Skill Gap Analyzer")
    st.write("Compare the skills shown in your academic material with the skills commonly needed for a selected fresher role.")

    if not st.session_state.processed_file_name:
        st.info("Please upload your academic material from the Dashboard first.")
    else:
        target_role = st.selectbox(
            "🎯 Select your target role",
            list(ROLE_SKILLS.keys()),
            key="skill_gap_target_role",
        )

        if st.button("🔎 Analyze Skill Gap", type="primary", use_container_width=True):
            with st.spinner("Analyzing your skills..."):
                try:
                    st.session_state.skill_gap_analysis = calculate_skill_gap_analysis(
                        st.session_state.full_text,
                        st.session_state.weak_subjects,
                        st.session_state.strong_subjects,
                        st.session_state.missing_topics,
                        target_role,
                    )
                except Exception as exc:
                    st.session_state.skill_gap_analysis = None
                    st.error("Skill gap analysis could not be completed. Please try again.")
                    st.caption(f"Details: {exc}")

        if st.session_state.skill_gap_analysis:
            # Recalculate automatically when the selected role changes.
            if st.session_state.skill_gap_analysis.get("role") != target_role:
                st.session_state.skill_gap_analysis = calculate_skill_gap_analysis(
                    st.session_state.full_text,
                    st.session_state.weak_subjects,
                    st.session_state.strong_subjects,
                    st.session_state.missing_topics,
                    target_role,
                )
            display_skill_gap_analysis(st.session_state.skill_gap_analysis)
        else:
            st.info("Select a target role and click **Analyze Skill Gap**.")



# ============================================================
# FRESHER READINESS
# ============================================================

elif page == "🚀 Fresher Readiness":

    st.header("🚀 Fresher Readiness Score")

    if not st.session_state.processed_file_name:
        st.info("Please upload your academic material from the Dashboard first.")
    else:
        if st.session_state.fresher_readiness is None:
            st.session_state.fresher_readiness = calculate_fresher_readiness(
                st.session_state.transcript_text,
                st.session_state.syllabus_text,
                st.session_state.notes_text,
                st.session_state.study_plan,
                st.session_state.weak_subjects,
                st.session_state.strong_subjects,
                st.session_state.missing_topics,
            )

        display_fresher_readiness(
            st.session_state.fresher_readiness
        )

        st.divider()
        st.info(
            "This score is calculated only from evidence found in your uploaded academic material. "
            "It is intended to guide your preparation, not predict hiring outcomes."
        )


# ============================================================
# EXPLAIN LIKE I'M A BEGINNER PAGE
# ============================================================

elif page == "📚 Explain Like I'm a Beginner":

    display_beginner_explanation_page()


# ============================================================
# EXPLAIN → HIDE → RECALL
# ============================================================

elif page == "🧠 Explain → Hide → Recall":

    st.header("🧠 Explain → Hide → Recall")
    st.write(
        "Learn a topic from your uploaded material, hide the explanation, "
        "then explain it from memory and get AI feedback."
    )

    if not st.session_state.get("retriever"):
        st.info(
            "📚 Please upload your academic PDF from the Dashboard first."
        )
    else:
        recall_defaults = {
            "recall_topic": "",
            "recall_context": "",
            "recall_explanation": "",
            "recall_hidden": False,
            "recall_result": "",
            "recall_score": 0,
        }

        for _key, _value in recall_defaults.items():
            if _key not in st.session_state:
                st.session_state[_key] = _value

        st.subheader("📚 Step 1 — Choose a Topic")

        recall_topic_input = st.text_input(
            "Topic to practice",
            placeholder="Example: Normalization",
            key="recall_topic_input",
        )

        if st.button(
            "🧠 Explain Topic",
            type="primary",
            use_container_width=True,
        ):
            topic_value = str(
                recall_topic_input or ""
            ).strip()

            if not topic_value:
                st.warning("Please enter a topic first.")
            else:
                with st.spinner(
                    "🔎 Finding the topic in your uploaded material..."
                ):
                    try:
                        recall_documents = (
                            st.session_state.retriever.invoke(
                                topic_value
                            )
                        )
                    except Exception as error:
                        recall_documents = []
                        st.error(
                            "Could not search your uploaded material."
                        )
                        st.caption(
                            f"Recall search detail: {type(error).__name__}"
                        )

                if recall_documents:
                    recall_context = "\n\n".join(
                        str(document.page_content)
                        for document in recall_documents
                        if getattr(document, "page_content", None)
                    )

                    if not recall_context.strip():
                        st.warning(
                            "The topic was found, but no readable context was returned."
                        )
                    else:
                        with st.spinner(
                            "🧠 Creating a beginner-friendly explanation..."
                        ):
                            try:
                                explanation = generate_explanation(
                                    topic_value,
                                    recall_context,
                                )
                            except Exception as error:
                                explanation = ""
                                st.error(
                                    "Could not generate the explanation. "
                                    "Please make sure Ollama is running."
                                )
                                st.caption(
                                    f"Explanation detail: {type(error).__name__}"
                                )

                        if explanation and str(explanation).strip():
                            st.session_state.recall_topic = topic_value
                            st.session_state.recall_context = recall_context
                            st.session_state.recall_explanation = str(
                                explanation
                            ).strip()
                            st.session_state.recall_hidden = False
                            st.session_state.recall_result = ""
                            st.session_state.recall_score = 0
                            st.rerun()
                        else:
                            st.warning(
                                "StudyBuddy could not generate an explanation. "
                                "Please try again."
                            )
                else:
                    st.warning(
                        "I couldn't find relevant information about this topic "
                        "in your uploaded material."
                    )

        if (
            st.session_state.get("recall_explanation")
            and not st.session_state.get("recall_hidden", False)
        ):
            st.divider()
            st.subheader("📖 Step 2 — Simple Explanation")

            st.info(
                st.session_state.recall_explanation
            )

            if st.button(
                "🙈 Hide Explanation & Start Recall",
                use_container_width=True,
            ):
                st.session_state.recall_hidden = True
                st.session_state.recall_result = ""
                st.session_state.recall_score = 0
                st.rerun()

        if (
            st.session_state.get("recall_hidden", False)
            and st.session_state.get("recall_explanation")
        ):
            st.divider()
            st.subheader("🙈 Step 3 — Recall From Memory")

            st.success(
                f"Explain **{st.session_state.recall_topic}** "
                "in your own words without looking at the explanation."
            )

            recall_answer = st.text_area(
                "✍️ Your Recall",
                height=220,
                placeholder=(
                    "Write everything you remember about this topic..."
                ),
                key="recall_answer_input",
            )

            if st.button(
                "🎯 Check My Recall",
                type="primary",
                use_container_width=True,
            ):
                if not recall_answer.strip():
                    st.warning(
                        "Please write your answer before checking."
                    )
                else:
                    with st.spinner(
                        "🤖 Checking your understanding..."
                    ):
                        try:
                            result = check_recall(
                                st.session_state.recall_topic,
                                st.session_state.recall_context,
                                recall_answer,
                            )
                            score = extract_recall_score(result)

                            st.session_state.recall_result = str(
                                result
                            )
                            st.session_state.recall_score = int(
                                score
                            )
                        except Exception as error:
                            st.session_state.recall_result = ""
                            st.session_state.recall_score = 0
                            st.error(
                                "Could not check your recall. "
                                "Please make sure Ollama is running and try again."
                            )
                            st.caption(
                                f"Recall check detail: {type(error).__name__}"
                            )

                    if st.session_state.recall_result:
                        st.rerun()

        if st.session_state.get("recall_result"):
            st.divider()
            st.subheader("🎯 Step 4 — Your Recall Result")

            score = int(
                st.session_state.get("recall_score", 0)
            )
            score = max(0, min(100, score))

            st.metric(
                "🧠 Recall Score",
                f"{score}%",
            )

            st.progress(
                score / 100,
                text=f"Recall performance: {score}%",
            )

            if score >= 80:
                st.success(
                    "🎉 Excellent! You remembered the important concepts."
                )
            elif score >= 60:
                st.warning(
                    "👍 Good attempt. Review the points you missed."
                )
            else:
                st.error(
                    "📚 This topic needs more revision. Try recalling it again."
                )

            st.markdown("### 🤖 AI Feedback")
            st.write(
                st.session_state.recall_result
            )

            result_col1, result_col2 = st.columns(2)

            with result_col1:
                if st.button(
                    "🔄 Try Recall Again",
                    use_container_width=True,
                ):
                    st.session_state.recall_hidden = True
                    st.session_state.recall_result = ""
                    st.session_state.recall_score = 0
                    st.rerun()

            with result_col2:
                if st.button(
                    "📖 Show Explanation Again",
                    use_container_width=True,
                ):
                    st.session_state.recall_hidden = False
                    st.session_state.recall_result = ""
                    st.session_state.recall_score = 0
                    st.rerun()


# ============================================================
# TEST ME
# ============================================================

elif page == "🧪 Test Me":

    st.header("🧪 Test Me")

    st.write(
        "Test your knowledge using questions generated "
        "from your uploaded academic material."
    )

    if not st.session_state.retriever:

        st.info(
            "📚 Please upload your academic PDF "
            "from the Dashboard first."
        )

    else:

        st.info(
            "💡 The quiz is grounded in your uploaded "
            "transcript, syllabus, and course notes."
        )

        # ----------------------------------------------------
        # START SCREEN
        # ----------------------------------------------------

        if not st.session_state.quiz_generated:

            st.subheader(
                "Ready to test yourself?"
            )

            st.write(
                "StudyBuddy will generate 10 multiple-choice "
                "questions from your academic material."
            )

            if st.button(
                "🧪 Start Test",
                type="primary",
                use_container_width=True
            ):

                with st.spinner(
                    "Creating your test from the academic material..."
                ):

                    questions = generate_quiz_from_material()

                if len(questions) >= 10:

                    st.session_state.quiz_questions = (
                        questions[:10]
                    )

                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_generated = True
                    st.session_state.quiz_weak_topics = []

                    st.rerun()

                else:

                    st.error(
                        "StudyBuddy could not create "
                        "10 valid questions from the material."
                    )

                    st.info(
                        "Try clicking Start Test again. "
                        "If the problem continues, check the "
                        "Ask AI page to confirm the retriever works."
                    )

        # ----------------------------------------------------
        # ACTIVE TEST
        # ----------------------------------------------------

        elif not st.session_state.quiz_submitted:

            questions = st.session_state.quiz_questions

            st.subheader(
                f"📝 Test — {len(questions)} Questions"
            )

            st.caption(
                "Choose one answer for every question."
            )

            st.divider()

            for index, question in enumerate(
                questions
            ):

                st.markdown(
                    f"### Question {index + 1}"
                )

                st.write(
                    question.get("question", "Question unavailable")
                )

                st.caption(
                    f"📚 Topic: {question.get('topic', 'General')}"
                )

                selected = st.radio(
                    "Select your answer:",
                    options=["A", "B", "C", "D"],
                    format_func=lambda x, q=question: (
                        f"{x}. {q.get('options', {}).get(x, 'Option unavailable')}"
                    ),
                    key=f"quiz_answer_{index}",
                    index=None,
                )

                if selected:

                    st.session_state.quiz_answers[
                        index
                    ] = selected

                st.divider()

            if st.button(
                "✅ Submit Test",
                type="primary",
                use_container_width=True
            ):

                unanswered = []

                for index in range(
                    len(questions)
                ):

                    if index not in st.session_state.quiz_answers:

                        unanswered.append(
                            index + 1
                        )

                if unanswered:

                    st.warning(
                        "Please answer all questions "
                        "before submitting."
                    )

                    st.write(
                        "Unanswered questions: "
                        + ", ".join(
                            str(number)
                            for number in unanswered
                        )
                    )

                else:

                    calculate_quiz_result()

                    st.rerun()

        # ----------------------------------------------------
        # RESULTS
        # ----------------------------------------------------

        else:

            display_quiz_result()

            st.divider()

            if st.button(
                "🔄 Take Another Test",
                use_container_width=True
            ):

                reset_quiz()

                st.rerun()


# ============================================================
# ASK AI
# ============================================================

elif page == "🤖 Ask AI":

    st.header(
        "🤖 Ask StudyBuddy"
    )

    if not st.session_state.retriever:

        st.info(
            "Please upload your academic material "
            "from the Dashboard first."
        )

    else:

        st.write(
            "Ask questions about your transcript, "
            "syllabus, notes, grades, or study plan."
        )

        question = st.text_area(
            "Your question",
            placeholder=(
                "Example: What grade did I get in "
                "Database Management Systems?"
            ),
            height=120,
        )

        if st.button(
            "🤖 Ask StudyBuddy",
            use_container_width=True
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                with st.spinner(
                    "Searching your academic material..."
                ):

                    try:

                        answer = ask_question(
                            question,
                            st.session_state.retriever
                        )

                        st.markdown(
                            "### 💬 Answer"
                        )

                        st.write(answer)

                    except Exception as error:

                        st.error(
                            "Could not answer that question from the uploaded material. Please try again."
                        )
                        st.caption(f"Q&A detail: {type(error).__name__}")


# ============================================================
# JOBS & INTERNSHIPS
# ============================================================

elif page == "💼 Jobs & Internships":

    st.header(
        "💼 Jobs & Internships"
    )

    if not st.session_state.transcript_text:

        st.info(
            "Upload your academic material first."
        )

    else:

        st.write(
            "StudyBuddy extracts skills from your "
            "academic material and uses those skills "
            "to search for relevant opportunities."
        )

        st.info(
            "🔎 Job keywords are taken from your "
            "academic material — not typed manually."
        )

        location = st.text_input(
            "Job location",
            value=st.session_state.job_location
        )

        if st.button(
            "🔎 Find Matching Jobs",
            use_container_width=True
        ):

            with st.spinner(
                "Searching for opportunities..."
            ):

                try:

                    result = search_jobs_from_transcript(
                        st.session_state.transcript_text,
                        location=location,
                        results_per_page=10
                    )

                    if isinstance(result, dict):

                        jobs = result.get(
                            "jobs",
                            []
                        )

                        matched_skills = result.get(
                            "matched_skills",
                            result.get("keywords", [])
                        )

                        # Show API/search errors without crashing the app.
                        if result.get("error"):
                            st.warning(str(result.get("error")))

                    elif isinstance(result, list):

                        jobs = result
                        matched_skills = []

                    else:

                        jobs = []
                        matched_skills = []

                    st.session_state.jobs = jobs
                    st.session_state.matched_skills = matched_skills
                    st.session_state.job_location = location

                except Exception as error:

                    st.error(
                        "Could not search for jobs right now. Please try again."
                    )
                    st.caption(f"Job search detail: {type(error).__name__}")

        if st.session_state.matched_skills:

            st.subheader(
                "🧠 Skills detected from your material"
            )

            st.write(
                ", ".join(
                    str(skill)
                    for skill in st.session_state.matched_skills
                )
            )

        jobs = st.session_state.jobs

        if jobs:

            st.subheader(
                "📋 Matching Opportunities"
            )

            for index, job in enumerate(
                jobs,
                start=1
            ):

                if not isinstance(job, dict):
                    continue

                title = job.get(
                    "title",
                    "Untitled position"
                )

                company = job.get(
                    "company",
                    {}
                )

                if isinstance(company, dict):
                    company_name = company.get(
                        "display_name",
                        "Company not specified"
                    )
                else:
                    company_name = str(company)

                location_data = job.get(
                    "location",
                    {}
                )

                if isinstance(location_data, dict):
                    location_name = location_data.get(
                        "display_name",
                        location
                    )
                else:
                    location_name = str(location_data)

                description = job.get(
                    "description",
                    ""
                )

                url = job.get(
                    "redirect_url",
                    ""
                )

                with st.container(border=True):

                    st.markdown(
                        f"### {index}. {title}"
                    )

                    st.write(
                        f"🏢 **Company:** {company_name}"
                    )

                    st.write(
                        f"📍 **Location:** {location_name}"
                    )

                    if description:

                        short_description = description[:500]

                        st.write(
                            short_description
                            + (
                                "..."
                                if len(description) > 500
                                else ""
                            )
                        )

                    if url:

                        st.link_button(
                            "🔗 View Opportunity",
                            url
                        )

        else:

            st.info(
                "Click 'Find Matching Jobs' "
                "to search for opportunities."
            )


# ============================================================
# MY FILES
# ============================================================

elif page == "🔖 Bookmarked Topics":
    display_bookmarks_page()

elif page == "📁 My Files":

    st.header(
        "📁 My Files"
    )

    if not st.session_state.processed_file_name:

        st.info(
            "No academic material has been uploaded yet."
        )

    else:

        st.subheader(
            "📄 Current Academic Material"
        )

        with st.container(border=True):

            st.write(
                f"📄 **File:** "
                f"{st.session_state.processed_file_name}"
            )

            st.write(
                f"📚 **Study plan topics:** "
                f"{len(st.session_state.study_plan)}"
            )

            st.write(
                f"📉 **Weak subjects:** "
                f"{len(st.session_state.weak_subjects)}"
            )

            st.write(
                f"💪 **Studying well:** "
                f"{len(st.session_state.strong_subjects)}"
            )

            st.write(
                f"📚 **Missing topics:** "
                f"{len(st.session_state.missing_topics)}"
            )

            st.write(
                f"🚀 **Fresher Readiness:** "
                f"{st.session_state.fresher_readiness.get('score', 0)}/100"
                if st.session_state.fresher_readiness
                else "🚀 **Fresher Readiness:** Not calculated"
            )

            st.write(
                f"🔍 **Skill Gap Analyzer:** "
                f"Ready" if st.session_state.skill_gap_analysis
                else "🔍 **Skill Gap Analyzer:** Not analyzed"
            )

            st.write(
                f"🧪 **Test Me:** "
                f"{'Ready' if st.session_state.retriever else 'Not Ready'}"
            )

            st.write(
                f"📅 **Scheduled days:** "
                f"{len(st.session_state.daily_schedule)}"
            )

            if st.session_state.retriever:

                st.success(
                    "✅ Document is ready for Q&A and Test Me."
                )

            else:

                st.warning(
                    "Q&A retriever is not available."
                )

        st.divider()

        st.subheader(
            "📌 Processing Status"
        )

        st.write("✅ PDF loaded")
        st.write("✅ Text extracted")
        st.write("✅ Document chunks created")
        st.write("✅ Vector store created")
        st.write("✅ Retriever created")
        st.write("✅ Transcript analyzed")
        st.write("✅ Weak subjects identified")
        st.write("✅ Strong subjects identified")
        st.write("✅ Missing syllabus topics identified")
        st.write("✅ Study plan generated")
        st.write("✅ Daily schedule generated")
        st.write("✅ Fresher Readiness Score calculated")
        st.write("✅ Test Me module ready")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🎓 StudyBuddy — Academic + Career Copilot"
)
