import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "in")


# ---------------------------------------------------------
# Helper: safely get a string
# ---------------------------------------------------------

def safe_string(value, default=""):
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


# ---------------------------------------------------------
# Helper: extract technical skills from academic material
# ---------------------------------------------------------

def extract_skills(transcript_text):
    """
    Extract relevant technical skills from academic material (transcript,
    syllabus, or course notes).
    """
    if not transcript_text:
        return []

    text = safe_string(transcript_text).lower()

    # Common technical skills to detect
    skill_definitions = [
        ("Python", r"\bpython\b"),
        ("Java", r"\bjava\b"),
        ("SQL", r"\bsql\b"),
        ("MySQL", r"\bmysql\b"),
        ("MongoDB", r"\bmongodb\b"),
        ("Data Science", r"\bdata\s+science\b"),
        ("Data Analysis", r"\bdata\s+analysis\b"),
        ("Machine Learning", r"\bmachine\s+learning\b"),
        ("Deep Learning", r"\bdeep\s+learning\b"),
        ("Artificial Intelligence", r"\bartificial\s+intelligence\b"),
        ("Data Structures", r"\bdata\s+structures\b"),
        ("Algorithms", r"\balgorithms?\b"),
        ("Database", r"\bdatabases?\b|\bdbms\b"),
        ("Operating Systems", r"\boperating\s+systems?\b"),
        ("Computer Networks", r"\bcomputer\s+networks?\b|\bnetworking\b"),
        ("HTML", r"\bhtml(?:5)?\b"),
        ("CSS", r"\bcss(?:3)?\b"),
        ("JavaScript", r"\bjavascript\b|\bjs\b"),
        ("TypeScript", r"\btypescript\b"),
        ("React", r"\breact(?:\.js|js)?\b"),
        ("Node.js", r"\bnode(?:\.js|js)?\b"),
        ("REST APIs", r"\brest(?:ful)?\s+apis?\b|\bapis?\b"),
        ("Web Development", r"\bweb\s+development\b"),
        ("Power BI", r"\bpower\s+bi\b"),
        ("Excel", r"\bexcel\b"),
        ("Pandas", r"\bpandas\b"),
        ("NumPy", r"\bnumpy\b"),
        ("Matplotlib", r"\bmatplotlib\b"),
        ("Statistics", r"\bstatistics\b|\bstatistical\b"),
        ("Git", r"\bgit\b"),
        ("GitHub", r"\bgithub\b"),
        ("Cloud Computing", r"\bcloud\s+computing\b|\baws\b|\bazure\b"),
        ("Docker", r"\bdocker\b"),
        ("Linux", r"\blinux\b"),
        ("C++", r"\bc\+\+\b"),
        ("C#", r"\bc#\b"),
    ]

    matched_skills = []
    seen = set()

    for skill_name, pattern in skill_definitions:
        if re.search(pattern, text, re.IGNORECASE):
            if skill_name not in seen:
                seen.add(skill_name)
                matched_skills.append(skill_name)

    return matched_skills


# ---------------------------------------------------------
# Main job-search function
# ---------------------------------------------------------

def search_jobs_from_transcript(
    transcript_text,
    location="Hyderabad",
    results_per_page=10
):
    """
    Search live jobs on Adzuna using skills detected from the student's
    uploaded academic material.

    Returns a consistent dictionary:
    {
        "keywords": [...],
        "query": "...",
        "location": "...",
        "jobs": [...],
        "message": "...",
        "error": "..."
    }
    """
    # -----------------------------------------------------
    # Validate location
    # -----------------------------------------------------
    clean_location = safe_string(location, "Hyderabad")
    if not clean_location:
        clean_location = "Hyderabad"

    # -----------------------------------------------------
    # Validate result count
    # -----------------------------------------------------
    try:
        results_per_page = int(results_per_page)
    except (TypeError, ValueError):
        results_per_page = 10
    results_per_page = max(1, min(results_per_page, 20))

    # -----------------------------------------------------
    # Validate academic material / transcript
    # -----------------------------------------------------
    clean_transcript = safe_string(transcript_text)
    if not clean_transcript:
        return {
            "keywords": [],
            "query": "",
            "location": clean_location,
            "jobs": [],
            "message": "",
            "error": "No academic material was available for job matching. Please upload your academic material first.",
            "matched_skills": [],
        }

    # -----------------------------------------------------
    # Extract skills from transcript
    # -----------------------------------------------------
    matched_skills = extract_skills(clean_transcript)

    if not matched_skills:
        return {
            "keywords": [],
            "query": "",
            "location": clean_location,
            "jobs": [],
            "message": "",
            "error": "No job-related technical skills were found in the uploaded academic material.",
            "matched_skills": [],
        }

    # -----------------------------------------------------
    # Check Adzuna credentials
    # -----------------------------------------------------
    app_id = safe_string(os.getenv("ADZUNA_APP_ID", ADZUNA_APP_ID))
    app_key = safe_string(os.getenv("ADZUNA_APP_KEY", ADZUNA_APP_KEY))

    if not app_id or not app_key:
        # Build query for context even if credentials missing
        initial_query = " ".join(matched_skills[:2]) if len(matched_skills) >= 2 else matched_skills[0]
        return {
            "keywords": matched_skills,
            "query": initial_query,
            "location": clean_location,
            "jobs": [],
            "message": "",
            "error": "Adzuna API credentials are missing. Add ADZUNA_APP_ID and ADZUNA_APP_KEY to your .env file.",
            "matched_skills": matched_skills,
        }

    country = safe_string(os.getenv("ADZUNA_COUNTRY", ADZUNA_COUNTRY), "in").lower()
    if not country:
        country = "in"

    # -----------------------------------------------------
    # Build query from actual transcript skills (not hard-coded)
    # -----------------------------------------------------
    # Adzuna uses boolean AND for search terms in 'what'.
    # If we combine 4+ terms, Adzuna usually returns 0 results.
    # We use top 2 detected skills first, with fallback to top 1 skill.
    candidate_queries = []
    if len(matched_skills) >= 2:
        candidate_queries.append(" ".join(matched_skills[:2]))
    candidate_queries.append(matched_skills[0])

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    last_error_message = ""
    raw_jobs = []
    final_query = candidate_queries[0]

    for candidate_query in candidate_queries:
        final_query = candidate_query
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": results_per_page,
            "what": final_query,
            "where": clean_location,
            "content-type": "application/json",
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=15
            )
        except requests.exceptions.Timeout:
            return {
                "keywords": matched_skills,
                "query": final_query,
                "location": clean_location,
                "jobs": [],
                "message": "",
                "error": "The job search request timed out. Please check your network and try again.",
                "matched_skills": matched_skills,
            }
        except requests.exceptions.ConnectionError:
            return {
                "keywords": matched_skills,
                "query": final_query,
                "location": clean_location,
                "jobs": [],
                "message": "",
                "error": "Could not connect to the Adzuna job service. Check your internet connection and try again.",
                "matched_skills": matched_skills,
            }
        except requests.exceptions.RequestException as err:
            return {
                "keywords": matched_skills,
                "query": final_query,
                "location": clean_location,
                "jobs": [],
                "message": "",
                "error": f"Could not contact the Adzuna job service: {safe_string(err)}",
                "matched_skills": matched_skills,
            }
        except Exception as unexpected:
            return {
                "keywords": matched_skills,
                "query": final_query,
                "location": clean_location,
                "jobs": [],
                "message": "",
                "error": f"An unexpected error occurred during job search: {safe_string(unexpected)}",
                "matched_skills": matched_skills,
            }

        # Handle non-200 HTTP status
        if response.status_code != 200:
            if response.status_code in (401, 403):
                last_error_message = "Adzuna rejected the API credentials. Check ADZUNA_APP_ID and ADZUNA_APP_KEY in your .env file."
            elif response.status_code == 429:
                last_error_message = "Adzuna rate limit reached. Please wait and try again later."
            elif response.status_code >= 500:
                last_error_message = f"Adzuna server is temporarily unavailable (HTTP {response.status_code}). Please try again later."
            else:
                last_error_message = f"Adzuna returned an unexpected response (HTTP {response.status_code})."

            return {
                "keywords": matched_skills,
                "query": final_query,
                "location": clean_location,
                "jobs": [],
                "message": "",
                "error": last_error_message,
                "matched_skills": matched_skills,
            }

        # Safely parse JSON response
        try:
            data = response.json()
        except (ValueError, Exception):
            return {
                "keywords": matched_skills,
                "query": final_query,
                "location": clean_location,
                "jobs": [],
                "message": "",
                "error": "Adzuna returned an invalid or malformed response. Please try again.",
                "matched_skills": matched_skills,
            }

        if not isinstance(data, dict):
            return {
                "keywords": matched_skills,
                "query": final_query,
                "location": clean_location,
                "jobs": [],
                "message": "",
                "error": "Adzuna returned an unexpected response format. Please try again.",
                "matched_skills": matched_skills,
            }

        results = data.get("results")
        if isinstance(results, list) and len(results) > 0:
            raw_jobs = results
            break

    # -----------------------------------------------------
    # Parse and clean jobs list
    # -----------------------------------------------------
    jobs = []
    for item in raw_jobs:
        if not isinstance(item, dict):
            continue

        company_data = item.get("company")
        if isinstance(company_data, dict):
            company = safe_string(company_data.get("display_name"), "Unknown company")
        else:
            company = safe_string(company_data, "Unknown company")

        location_data = item.get("location")
        if isinstance(location_data, dict):
            job_loc = safe_string(location_data.get("display_name"), clean_location)
        else:
            job_loc = safe_string(location_data, clean_location)

        title = safe_string(item.get("title"), "Position Available")
        description = safe_string(item.get("description"), "")
        # Remove simple HTML tags that Adzuna sometimes includes
        description = re.sub(r"<[^>]+>", "", description).strip()

        job_url = safe_string(item.get("redirect_url"), "")
        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")

        jobs.append({
            "title": title,
            "company": company,
            "location": job_loc,
            "description": description,
            "url": job_url,
            "salary_min": salary_min,
            "salary_max": salary_max,
        })

    # -----------------------------------------------------
    # Return formatted result
    # -----------------------------------------------------
    if not jobs:
        return {
            "keywords": matched_skills,
            "query": final_query,
            "location": clean_location,
            "jobs": [],
            "message": f"No matching jobs were found in {clean_location} for '{final_query}'. Try another location.",
            "error": "",
            "matched_skills": matched_skills,
        }

    return {
        "keywords": matched_skills,
        "query": final_query,
        "location": clean_location,
        "jobs": jobs,
        "message": f"Found {len(jobs)} matching opportunity(ies) in {clean_location}.",
        "error": "",
        "matched_skills": matched_skills,
    }