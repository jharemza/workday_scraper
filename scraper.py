import requests
import json
import time

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

        # --- Build Final Payload ---
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

        # Write full job response to file        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(job_urls, f, indent=4)
        print(f"Filtered job response saved to {OUTPUT_FILE}")

    else:
        print(f"Failed to fetch initial facets: {response.status_code}")