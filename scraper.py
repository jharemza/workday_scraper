import requests
import json
import time
import os
from dotenv import load_dotenv

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

NOTION_API_URL = "https://api.notion.com/v1/pages"
HEADERS = {
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

# --- Notion Mapping Function ---

def create_notion_page(job, notion_token, database_id):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    payload = {
        "parent": { "database_id": database_id },
        "properties": {
            "Title": {
                "title": [
                    { "text": { "content": job.get("title", "Untitled") } }
                ]
            },
            "Location": {
                "rich_text": [
                    { "text": { "content": job.get("location", "") } }
                ]
            },
            "Start Date": {
                "date": {
                    "start": job.get("startDate", None)
                }
            },
            "Job ID": {
                "rich_text": [
                    { "text": { "content": job.get("jobReqId", "") } }
                ]
            },
            "External URL": {
                "url": job.get("externalUrl", "")
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.status_code, response.text


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
                print(f"Found: {location} → FacetParameter: {facet_param} → ID: {location_id}")
                location_ids.append(location_id)
            else:
                print(f"Warning: {location} not found in facets.")

        if not location_ids:
            print("No matching locations found. Exiting.")
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
                    print("No more jobs found. Exiting pagination.")
                    break

                job_urls.extend(jobs_data)

                print(f"Fetched {len(jobs_data)} jobs at offset {OFFSET}...")

                if len(jobs_data) < LIMIT:
                    # Less than requested, end of available data
                    print("Reached last page.")
                    break
                
                OFFSET += LIMIT

                time.sleep(0.5)

            else:
                print(f"Failed to fetch jobs with filters: {response.status_code}")
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
                        print(f"Fetched jobPostingInfo from {url} ({idx+1}/{len(job_urls)})")
                    else:
                        print(f"No jobPostingInfo found in {url}")
                else:
                    print(f"Failed to fetch {url} — Status Code: {response.status_code}")
            except Exception as e:
                print(f"Exception fetching {url}: {str(e)}")

            time.sleep(0.5)  # Polite crawling


        # Write full job response to file        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(fetched_job_postings, f, indent=4)
        print(f"Filtered job response saved to {OUTPUT_FILE}")

    else:
        print(f"Failed to fetch initial facets: {response.status_code}")