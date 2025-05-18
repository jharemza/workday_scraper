import requests
import json
import time
import os
import re
from dotenv import load_dotenv
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# --- Logging Setup ---
# Create rotating file handler (max 5MB per file, keep 5 backups)
file_handler = RotatingFileHandler(
    "scraper.log", maxBytes=5_000_000, backupCount=5, encoding='utf-8'
)
file_handler.setLevel(logging.INFO)  # or DEBUG for full verbosity

# Create console handler (logs only WARNING+ to console)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # WARNING and ERROR only

# Formatter for both
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Root logger config — no need to set handlers in basicConfig when doing it manually
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # This is the *global* threshold
logger.handlers = []  # Clear any default handlers (if re-running interactively)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --- Configurations ---
URL = "https://mtb.wd5.myworkdayjobs.com/wday/cxs/mtb/MTB/jobs"
HEADERS = {
    "Content-Type": "application/json"
}
OUTPUT_FILE = "workday_response.json"

# --- Desired Locations by Descriptor Name ---
TARGET_LOCATIONS = [
    "Remote, USA",
    "Buffalo, NY"
]
LIMIT = 20
OFFSET = 0 

# Load environment variables from .env file
load_dotenv()

# Notion Variables

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
APPLIED_DATABASE_ID = os.getenv("APPLIED_DATABASE_ID")

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# --- Function to Find Location IDs ---
# --- Function to Find ID by Descriptor (General Purpose) ---
def find_id_by_descriptor(facets, target_descriptor):
    """
    Recursively find the ID and facetParameter for a given descriptor across Workday facetParameters.

    Args:
        facets (list): The facets list loaded from JSON.
        target_descriptor (str): The descriptor text to search for.

    Returns:
        tuple: (facetParameter, id) if found, or (None, None) if not found.
    """
    target_descriptor = target_descriptor.strip().lower()

    for facet in facets:
        facet_parameter = facet.get("facetParameter", "")
        values = facet.get("values", [])

        for value in values:
            # Check if this value directly matches
            descriptor = value.get("descriptor", "").strip().lower()
            if descriptor == target_descriptor and "id" in value:
                return facet_parameter, value["id"]

            # If value has nested facetParameter + values, recurse
            if "facetParameter" in value and "values" in value:
                nested_facet_parameter = value["facetParameter"]
                nested_values = value["values"]

                found_facet_parameter, found_id = find_id_by_descriptor(
                    [{"facetParameter": nested_facet_parameter, "values": nested_values}],
                    target_descriptor
                )

                if found_id:
                    return found_facet_parameter, found_id

    return None, None

# --- Notion Functions ---
def extract_salary_range(description):
    """
    Extracts salary range (low, high) as floats from jobDescription HTML text.
    """
    match = re.search(r"\$([\d,]+(?:\.\d{2})?)\s*-\s*\$([\d,]+(?:\.\d{2})?)", description)
    if match:
        low_str = match.group(1).replace(",", "")
        high_str = match.group(2).replace(",", "")
        try:
            low = float(low_str)
            high = float(high_str)
            return low, high
        except ValueError:
            logging.debug(f"Float conversion failed: low='{low_str}', high='{high_str}'")
            return None, None
    else:
        logging.debug("Salary pattern not found in job description.")
        return None, None

def create_notion_payload(job):
    # Extract salary
    description = job.get("jobDescription", "")
    base_pay_low, base_pay_high = extract_salary_range(description)

    # TEMP debug output
    logging.debug(f"Extracted base pay: Low = {base_pay_low}, High = {base_pay_high}")

    app_end_date = job.get("endDate", datetime(datetime.today().year, 12, 31).date().isoformat())

    NOTION_PAYLOAD = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "Company": {
                "title": [
                    { "text": { "content": "M & T Bank" } }
                ]
            },
            "Position": {
                "rich_text": [
                    { "text": { "content": job.get("title", "Untitled") } }
                ]
            },
            "Req ID": {
                "rich_text": [
                    { "text": { "content": job.get("jobReqId", "") } }
                ]
            },
            "Job Posting URL": {
                "url": job.get("externalUrl", "")
            },
            "Stage": {
                "status": {
                    "name": "Ready to apply"
                }
            },
            "Base Pay Low": {
                "number": base_pay_low
            },
            "Base Pay High": {
                "number": base_pay_high
            },
            "Application Deadline": {
                "date": {
                    "start": app_end_date
                }
            }
        }
    }

    return NOTION_PAYLOAD

def fetch_existing_req_ids(database_id, company_filter=None):
    """
    Fetches all Req IDs from the given Notion database.
    Optionally filters by Company name if `company_filter` is provided.

    Raises:
        ValueError if filtering is required but not supplied.
    """
    if database_id == APPLIED_DATABASE_ID and not company_filter:
        raise ValueError("Company filter must be provided when querying APPLIED_DATABASE_ID")

    existing_ids = set()
    has_more = True
    next_cursor = None

    while has_more:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor

        if company_filter:
            payload["filter"] = {
                "property": "Company",
                "rich_text": {
                    "equals": company_filter
                }
            }

        response = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=NOTION_HEADERS,
            json=payload
        )

        if response.status_code != 200:
            logging.error(f"Failed to query Notion database {database_id}: {response.text}")
            break

        data = response.json()
        for result in data.get("results", []):
            props = result.get("properties", {})
            req_id_obj = props.get("Req ID", {}).get("rich_text", [])
            if req_id_obj:
                req_id = req_id_obj[0].get("text", {}).get("content", "").strip()
                if req_id:
                    existing_ids.add(req_id)

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    return existing_ids

# --- Main Execution ---
if __name__ == "__main__":
    # Initial fetch to get facets
    initial_payload = {
        "limit": 1,  # Just fetch facets; no need for jobs yet
        "offset": 0,
        "appliedFacets": {},  # Empty but required
        "searchText": ""      # Empty but required
    }
    response = requests.post(URL, headers=HEADERS, json=initial_payload)

    if response.status_code == 200:
        data = response.json()
        facets = data.get("facets", [])

        # Find IDs dynamically for all TARGET_LOCATIONS
        location_ids = []
        for location in TARGET_LOCATIONS:
            facet_param, location_id = find_id_by_descriptor(facets, location)
            if location_id:
                logging.info(f"Found: {location} → FacetParameter: {facet_param} → ID: {location_id}")
                location_ids.append(location_id)
            else:
                logging.warning(f"{location} not found in facets.")

        if not location_ids:
            logging.error("No matching locations found. Exiting.")
            exit()

        # --- Job List Payload ---
        job_urls = []

        while True:
            final_payload = {
                "limit": LIMIT,
                "offset": OFFSET,
                "appliedFacets": {
                    "locations": location_ids
                },
                "searchText": "sql"
            }

            # --- Fetch Jobs using dynamic location IDs ---
            response = requests.post(URL, headers=HEADERS, json=final_payload)

            if response.status_code == 200:
                jobs_data = [
                    f"https://mtb.wd5.myworkdayjobs.com/wday/cxs/mtb/MTB/job/{job.get('externalPath', '').split('/')[-1]}"
                    for job in response.json().get("jobPostings", [])
                    if "externalPath" in job
                    ]

                if not jobs_data:
                    logging.info("No more jobs found. Exiting pagination.")
                    break

                job_urls.extend(jobs_data)

                logging.info(f"Fetched {len(jobs_data)} jobs at offset {OFFSET}...")

                if len(jobs_data) < LIMIT:
                    # Less than requested, end of available data
                    logging.info("Reached last page.")
                    break
                
                OFFSET += LIMIT

                time.sleep(0.5)

            else:
                logging.error(f"Failed to fetch jobs with filters: {response.status_code}")
                break
        
        # --- Job URL Loop ---
        fetched_job_postings = []

        for idx, url in enumerate(job_urls):
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code == 200:
                    job_posting_info = response.json().get("jobPostingInfo", None)
                    if job_posting_info:
                        fetched_job_postings.append(job_posting_info)
                        logging.info(f"Fetched jobPostingInfo from {url} ({idx+1}/{len(job_urls)})")
                    else:
                        logging.error(f"No jobPostingInfo found in {url}")
                else:
                    logging.error(f"Failed to fetch {url} — Status Code: {response.status_code}")
            except Exception as e:
                logging.error(f"Exception fetching {url}: {str(e)}")

            time.sleep(0.5)  # Polite crawling

        # Collect existing Req IDs
        logging.info("Fetching existing Req IDs from Notion databases...")
        existing_ids_db = fetch_existing_req_ids(DATABASE_ID)
        existing_ids_applied = fetch_existing_req_ids(APPLIED_DATABASE_ID, company_filter="M & T Bank")
        existing_req_ids = existing_ids_db.union(existing_ids_applied)
        logging.info(f"Found {len(existing_req_ids)} total existing Req IDs.")

        # --- Notion Mapping + Upload ---
        for job in fetched_job_postings:
            job_req_id = job.get("jobReqId", "").strip()
            if job_req_id in existing_req_ids:
                logging.info(f"[SKIP] Req ID {job_req_id} already exists. Skipping.")
                continue

            try:
                NOTION_PAYLOAD = create_notion_payload(job)  # This builds the page payload from a job dictionary
                notion_response = requests.post(NOTION_API_URL, headers=NOTION_HEADERS, json=NOTION_PAYLOAD)

                if notion_response.status_code == 200:
                    logging.info(f"Job '{job.get('title')}' added to Notion.")
                else:
                    logging.error(f"Failed to add '{job.get('title')}' — {notion_response.status_code}: {notion_response.text}")

                time.sleep(0.5)  # Respectful delay to avoid rate limits
            except Exception as e:
                logging.error(f"Failed processing job '{job.get('title')}': {str(e)}")

        # Write full job response to file        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(fetched_job_postings, f, indent=4)
        logging.info(f"Filtered job response saved to {OUTPUT_FILE}")

    else:
        logging.error(f"Failed to fetch initial facets: {response.status_code}")