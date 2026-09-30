from pathlib import Path

from document_processor import load_pdf, extract_text


# Get the folder where this Python file is located
project_folder = Path(__file__).parent

# PDF is in the same folder
pdf_path = project_folder / "studybuddy_test_material.pdf"
if not pdf_path.exists():
    pdf_path = project_folder / "StudyBuddy_without_point_4.pdf"

print("PDF path:")
print(pdf_path)

print("\nDoes the PDF exist?")
print(pdf_path.exists())


if not pdf_path.exists():
    print("\nERROR: PDF was not found.")
    print("Files in the project folder:")

    for file in project_folder.iterdir():
        print(" -", file.name)

    raise SystemExit


# Load PDF
documents = load_pdf(str(pdf_path))

print("\nNumber of pages:", len(documents))


# Extract text
text = extract_text(documents)

print("\n========== EXTRACTED TEXT ==========\n")

print(text)