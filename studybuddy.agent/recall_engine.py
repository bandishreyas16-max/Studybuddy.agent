from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# OLLAMA MODEL
# ============================================================

llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0
)


# ============================================================
# GENERATE SIMPLE EXPLANATION
# ============================================================

def generate_explanation(topic, context):

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are StudyBuddy, a personal learning assistant.

Explain the requested topic using ONLY the student's uploaded
academic material.

Rules:
- Explain like the student is a complete beginner.
- Use simple language.
- Explain the important concepts.
- Give a small example when useful.
- Do not invent information.
- Keep the explanation useful for exam preparation.
"""
        ),
        (
            "human",
            """
TOPIC:
{topic}

UPLOADED MATERIAL:
{context}

Explain this topic in a simple and beginner-friendly way.
"""
        )
    ])

    response = llm.invoke(
        prompt.invoke({
            "topic": topic,
            "context": context
        })
    )

    return response.content


# ============================================================
# CHECK STUDENT RECALL
# ============================================================

def check_recall(topic, context, student_answer):

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are StudyBuddy's Recall Checker.

Compare the student's answer with the uploaded academic material.

Evaluate understanding rather than exact wording.

Return the response in exactly this format:

SCORE: <number from 0 to 100>

VERDICT: <Correct / Mostly Correct / Partially Correct / Needs Revision>

WHAT YOU GOT RIGHT:
- point
- point

WHAT YOU MISSED:
- point
- point

BETTER UNDERSTANDING:
short explanation

Rules:
- Use ONLY the uploaded material.
- Do not invent facts.
- Focus on important concepts.
- Do not give a high score simply because the answer is long.
"""
        ),
        (
            "human",
            """
TOPIC:
{topic}

UPLOADED MATERIAL:
{context}

STUDENT'S RECALL:
{student_answer}

Check the student's understanding.
"""
        )
    ])

    response = llm.invoke(
        prompt.invoke({
            "topic": topic,
            "context": context,
            "student_answer": student_answer
        })
    )

    return response.content


# ============================================================
# EXTRACT RECALL SCORE
# ============================================================

def extract_recall_score(result):

    try:

        for line in result.splitlines():

            line = line.strip()

            if line.upper().startswith("SCORE:"):

                score_text = line.split(":", 1)[1].strip()

                score = int(
                    score_text.replace("%", "").strip()
                )

                return max(0, min(100, score))

    except Exception:
        pass

    return 0