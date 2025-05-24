import time
from datetime import datetime
import os
from dotenv import load_dotenv
import job_parser as jp
import re
import logging
import requests

__all__ = [
    "create_notion_payload",
    "fetch_existing_req_ids",
    "append_job_description_to_page"
]

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

def create_notion_payload(job, company_name):
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
                    { "text": { "content": company_name } }
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

def append_job_description_to_page(page_id, html_description):
    blocks = jp.html_to_notion_blocks(html_description)

    max_batch_size = 100
    for i in range(0, len(blocks), max_batch_size):
        chunk = blocks[i:i + max_batch_size]

        response = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=NOTION_HEADERS,
            json={"children": chunk}
        )

        if response.status_code == 200:
            logging.info(f"Appended block chunk to page {page_id} ({i + len(chunk)}/{len(blocks)})")
        else:
            logging.error(f"Failed to append chunk to page {page_id}: {response.status_code} — {response.text}")
            break

        time.sleep(0.2)  # Polite batching
