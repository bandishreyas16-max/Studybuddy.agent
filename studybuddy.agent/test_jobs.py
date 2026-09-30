from job_search import search_jobs_from_transcript

sample_transcript = """
BSc Data Science

Python
Java
Data Structures
Algorithms
Database Management Systems
SQL
HTML
CSS
JavaScript
Data Science
Data Analysis
"""

result = search_jobs_from_transcript(
    sample_transcript,
    location="Hyderabad",
    results_per_page=5
)

print("\n==============================")
print("MATCHED SKILLS")
print("==============================")
print(result.get("matched_skills"))

print("\n==============================")
print("ERROR")
print("==============================")
print(result.get("error", "No error"))

print("\n==============================")
print("JOB COUNT")
print("==============================")
print(len(result.get("jobs", [])))

print("\n==============================")
print("JOB RESULTS")
print("==============================")

for i, job in enumerate(result.get("jobs", []), 1):
    print(f"\n{i}. {job.get('title')}")
    print(f"Company: {job.get('company')}")
    print(f"Location: {job.get('location')}")
    print(f"URL: {job.get('url')}")