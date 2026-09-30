import streamlit as st

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


# ==================================================
# OLLAMA MODEL
# ==================================================

@st.cache_resource
def get_llm():

    return ChatOllama(
        model="llama3.2:3b",
        temperature=0
    )


# ==================================================
# PROMPT
# ==================================================

QA_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are StudyBuddy, a personal learning assistant.

Answer the student's question using ONLY the
provided document context.

Rules:
- Use the uploaded material as the source.
- Do not invent grades, marks, subjects or topics.
- If the information is not present, say that it
  was not found in the uploaded material.
- Give a short, clear answer suitable for a student.

DOCUMENT CONTEXT:
{context}
"""
    ),
    (
        "human",
        "{question}"
    )
])


# ==================================================
# ASK QUESTION
# ==================================================

def ask_question(question, retriever):

    # Retrieve relevant document chunks
    documents = retriever.invoke(question)

    if not documents:
        return (
            "I couldn't find relevant information "
            "in your uploaded material."
        )

    # Combine retrieved chunks
    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    # Create prompt
    prompt = QA_PROMPT.invoke({
        "context": context,
        "question": question
    })

    # Get Ollama model
    llm = get_llm()

    # Ask Ollama
    response = llm.invoke(prompt)

    return response.content