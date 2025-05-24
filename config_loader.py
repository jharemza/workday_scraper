import yaml

def load_institutions_config(path="config/institutions.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["institutions"]
