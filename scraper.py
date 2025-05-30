import json
import logging
from logging.handlers import RotatingFileHandler
from tqdm import tqdm
from config_loader import load_institutions_config
from institution_runner import run_institution_scraper

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
HEADERS = {
    "Content-Type": "application/json"
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

# --- Main Execution ---
if __name__ == "__main__":

    institutions = load_institutions_config()

    for institution in tqdm(institutions, desc="Institutions", unit="org"):
        results = run_institution_scraper(institution)

        # Write full job response to file. One file per institution.
        safe_name = institution["name"].replace(" ", "_").replace("&", "and")
        filename = f"json_output/workday_response_{safe_name}.json"
    
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        logging.info(f"Filtered job response saved to {filename}")
