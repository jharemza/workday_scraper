import requests
import json

# --- Configurations ---
URL = "https://mtb.wd5.myworkdayjobs.com/wday/cxs/mtb/MTB/jobs"
HEADERS = {
    "Content-Type": "application/json"
}
OUTPUT_FILE = "workday_response.json"

# --- Desired Locations ---
# List of known location facet IDs you want to filter on
LOCATION_IDS = [
    "4120f4e4dde7100006ccf6800f5e0000",  # Remote, USA
    "c039dd6f9c540101978bcd1ebe3f0000"   # Buffalo, NY
    # add more as needed
]

# --- Build Payload Dynamically ---
PAYLOAD = {
    "limit": 10,
    "offset": 0,
    "appliedFacets": {
        "locations": LOCATION_IDS
    },
    "searchText": "sql"
}

# --- Main Execution ---
if __name__ == "__main__":
    response = requests.post(URL, headers=HEADERS, json=PAYLOAD)

    if response.status_code == 200:
        data = response.json()

        # Write full JSON response to file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        print(f"Full response saved to {OUTPUT_FILE}")
    else:
        print(f"Failed to fetch jobs: {response.status_code}")
