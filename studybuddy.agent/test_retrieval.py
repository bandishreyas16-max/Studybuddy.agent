from pathlib import Path

from document_processor import (
    load_pdf,
    split_documents,
    create_vector_store,
    get_retriever
)


# ------------------------------------------------
# 1. Locate PDF
# ------------------------------------------------

project_folder = Path(__file__).parent

pdf_path = project_folder / "StudyBuddy_without_point_4.pdf"

print("PDF:", pdf_path)
print("Exists:", pdf_path.exists())


if not pdf_path.exists():
    print("ERROR: PDF not found.")
    exit()


# ------------------------------------------------
# 2. Load PDF
# ------------------------------------------------

print("\nLoading PDF...")

documents = load_pdf(str(pdf_path))

print("Pages:", len(documents))


# ------------------------------------------------
# 3. Split PDF
# ------------------------------------------------

print("\nSplitting document...")

chunks = split_documents(documents)

print("Chunks:", len(chunks))


# ------------------------------------------------
# 4. Create Chroma database
# ------------------------------------------------

print("\nCreating Chroma vector database...")

vector_store = create_vector_store(chunks)

print("Chroma database created successfully!")


# ------------------------------------------------
# 5. Create retriever
# ------------------------------------------------

retriever = get_retriever(vector_store)


# ------------------------------------------------
# 6. Ask a question
# ------------------------------------------------

question = "What grade did I get in databases?"

print("\nQuestion:")
print(question)

print("\nSearching your documents...")


results = retriever.invoke(question)


# ------------------------------------------------
# 7. Display results
# ------------------------------------------------

print("\n========== RETRIEVED RESULTS ==========")

for i, document in enumerate(results):

    print(f"\n--- Result {i + 1} ---")

    print(document.page_content)


print("\n========================================")