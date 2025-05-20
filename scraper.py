import requests
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from tqdm import tqdm
import notion_client as nc

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
        for location in tqdm(TARGET_LOCATIONS, desc="Location facets", unit="location"):
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

        total_jobs_found = 0
        page_pbar = tqdm(desc="Pages scraped", unit="page")
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
                    for job in tqdm(response.json().get("jobPostings", []), desc="Jobs data", unit="job")
                    if "externalPath" in job
                    ]
                
                total_jobs_found += len(jobs_data)

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

            page_pbar.update(1)
        
        tqdm.write(f"🔍 Total job URLs collected: {total_jobs_found}")
        tqdm.write(f"📄 Total pages scraped: {page_pbar.n}")

        # --- Job URL Loop ---
        fetched_job_postings = []

        for idx, url in tqdm(enumerate(job_urls), total=len(job_urls), desc="Fetching job data", unit="job"):
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
        existing_ids_db = nc.fetch_existing_req_ids(nc.DATABASE_ID)
        existing_ids_applied = nc.fetch_existing_req_ids(nc.APPLIED_DATABASE_ID, company_filter="M&T Bank")
        existing_req_ids = existing_ids_db.union(existing_ids_applied)
        logging.info(f"Found {len(existing_req_ids)} total existing Req IDs.")

        # --- Notion Mapping + Upload ---
        success_count = 0
        skipped_count = 0
        error_count = 0

        for job in tqdm(fetched_job_postings, desc="Notion Upload", unit="job"):
            job_req_id = job.get("jobReqId", "").strip()
            if job_req_id in existing_req_ids:
                logging.info(f"[SKIP] Req ID {job_req_id} already exists. Skipping.")
                skipped_count += 1
                continue

            try:
                NOTION_PAYLOAD = nc.create_notion_payload(job)  # This builds the page payload from a job dictionary
                notion_response = requests.post(nc.NOTION_API_URL, headers=nc.NOTION_HEADERS, json=NOTION_PAYLOAD)

                if notion_response.status_code == 200:
                    success_count += 1
                    logging.info(f"Job '{job.get('title')}' added to Notion.")

                    # ✅ Get Notion page ID from creation response
                    new_page_id = notion_response.json().get("id")

                    # ✅ Append jobDescription as page body content
                    html_desc = job.get("jobDescription", "")
                    if html_desc:
                        nc.append_job_description_to_page(new_page_id, html_desc)

                else:
                    error_count += 1
                    logging.error(f"Failed to add '{job.get('title')}' — {notion_response.status_code}: {notion_response.text}")

                time.sleep(0.5)  # Respectful delay to avoid rate limits

            except Exception as e:
                error_count += 1
                logging.error(f"Failed processing job '{job.get('title')}': {str(e)}")

        tqdm.write(f"\n📊 Notion Upload Summary:")
        tqdm.write(f"  ✅ Success     : {success_count}")
        tqdm.write(f"  🟡 Skipped     : {skipped_count}")
        tqdm.write(f"  🔴 Failed      : {error_count}")
        tqdm.write(f"  📦 Total jobs  : {len(fetched_job_postings)}")

        # Write full job response to file        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(fetched_job_postings, f, indent=4)
        logging.info(f"Filtered job response saved to {OUTPUT_FILE}")

    else:
        logging.error(f"Failed to fetch initial facets: {response.status_code}")