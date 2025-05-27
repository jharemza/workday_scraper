import notion_client as nc
import requests
import logging
import time
from tqdm import tqdm

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
            descriptor = value.get("descriptor", "").strip().lower()
            if descriptor == target_descriptor and "id" in value:
                return facet_parameter, value["id"]

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

def log_with_prefix(level, company_name, message):
    getattr(logging, level)(f"[{company_name}] {message}")

def run_institution_scraper(institution: dict):
    """Run scraping and Notion writing for a single institution."""

    # 1. Set local vars from config
    url = institution["workday_url"]
    locations = institution.get("locations", [])
    search_text = institution["search_text"]
    company_name = institution["name"]

    log_with_prefix("info", company_name, f"🏁 Starting scrape.")

    # 2. Initial fetch for facets
    initial_payload = {
        "limit": 1,
        "offset": 0,
        "appliedFacets": {},
        "searchText": ""
    }

    response = requests.post(url, json=initial_payload, headers={"Content-Type": "application/json"})
    if response.status_code != 200:
        log_with_prefix("error", company_name, f"Failed to fetch facets.")
        return

    facets = response.json().get("facets", [])
    location_ids = []

    if locations:
        for loc in tqdm(locations, desc=f"{company_name}: Location facets", unit="loc"):
            facet_param, loc_id = find_id_by_descriptor(facets, loc)
            if loc_id:
                location_ids.append(loc_id)
            else:
                log_with_prefix("error", company_name, f"Location '{loc}' not found in facets.")

    if locations and not location_ids:
        log_with_prefix("warning", company_name, f"No valid location IDs matched descriptors. Skipping.")
        return []

    # 3. Job collection
    offset = 0
    limit = 20
    job_urls = []
    page_pbar = tqdm(desc=f"{company_name}: Pages scraped", unit="page")

    while True:

        applied_facets = {}
        if location_ids:
            applied_facets["locations"] = location_ids


        job_payload = {
            "limit": limit,
            "offset": offset,
            "appliedFacets": applied_facets,
            "searchText": search_text
        }

        response = requests.post(url, json=job_payload, headers={"Content-Type": "application/json"})

        if response.status_code != 200:
            log_with_prefix("error", company_name, f"Failed to fetch jobs.")
            break

        jobs = response.json().get("jobPostings", [])
        jobs_data = [
            f"{url.rsplit('/jobs', 1)[0]}/job/{job.get('externalPath', '').split('/')[-1]}"
            for job in jobs if "externalPath" in job
        ]

        if not jobs_data:
            break

        job_urls.extend(jobs_data)
        offset += limit
        page_pbar.update(1)

        if len(jobs) < limit:
            break

        time.sleep(0.5)

    tqdm.write(f"\n📄 {company_name} Pagination Summary:")
    tqdm.write(f"  🔍 Total job URLs collected: {len(job_urls)}")
    tqdm.write(f"  📄 Total pages scraped: {page_pbar.n}")


    page_pbar.close()

    # 4. Job detail collection
    job_postings = []
    for idx, url in tqdm(enumerate(job_urls), total=len(job_urls), desc=f"{company_name}: Fetching job data"):
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200:
                job_data = response.json().get("jobPostingInfo")
                if job_data:
                    job_postings.append(job_data)
        except Exception as e:
            log_with_prefix("error", company_name, f"Exception fetching job {url}: {str(e)}")

        time.sleep(0.5)

    # 5. Deduplication
    log_with_prefix("info", company_name, "Fetching existing Req IDs from Notion databases...")
    existing_ids_main = nc.fetch_existing_req_ids(nc.DATABASE_ID, company_filter=company_name)
    existing_ids_applied = nc.fetch_existing_req_ids(nc.APPLIED_DATABASE_ID, company_filter=company_name)
    existing_req_ids = existing_ids_main.union(existing_ids_applied)
    log_with_prefix("info", company_name, f"Found {len(existing_req_ids)} total existing Req IDs.")

    # 6. Notion upload
    success, skipped, failed = 0, 0, 0
    for job in tqdm(job_postings, desc=f"{company_name}: Notion Upload", unit="job"):
        req_id = job.get("jobReqId", "").strip()
        if req_id in existing_req_ids:
            log_with_prefix("info", company_name, f"Req ID {req_id} already exists. Skipping.")
            skipped += 1
            continue

        try:
            notion_payload = nc.create_notion_payload(job, company_name) # This builds the page payload from a job dictionary
            notion_response = requests.post(nc.NOTION_API_URL, headers=nc.NOTION_HEADERS, json=notion_payload)

            if notion_response.status_code == 200:
                success += 1
                log_with_prefix("info", company_name, f"Job '{job.get('title')}' added to Notion.")

                # ✅ Get Notion page ID from creation response
                new_page_id = notion_response.json().get("id")

                # ✅ Append jobDescription as page body content
                html_desc = job.get("jobDescription", "")
                if html_desc:
                    nc.append_job_description_to_page(new_page_id, html_desc)

            else:
                failed += 1
                log_with_prefix("error", company_name, f"Failed to upload job '{job.get('title')}' — {notion_response.status_code}: {notion_response.text}")

        except Exception as e:
            failed += 1
            log_with_prefix("error", company_name, f"Error uploading job '{job.get('title')}': {str(e)}")

        time.sleep(0.5)

    tqdm.write(f"\n📊 {company_name} Summary:")
    tqdm.write(f"  ✅ Uploaded: {success}")
    tqdm.write(f"  🟡 Skipped : {skipped}")
    tqdm.write(f"  🔴 Failed  : {failed}")
    tqdm.write(f"  📦 Total   : {len(job_postings)}")

    return job_postings
