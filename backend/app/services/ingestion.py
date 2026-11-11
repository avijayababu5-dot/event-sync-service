import json
from pathlib import Path
from pydantic import ValidationError

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

def load_json(filename):
    path = DATA_DIR / filename
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{filename} must contain a JSON array")
    return data

def load_sources():
    return load_json("calendar_events.json"), load_json("crm_events.json")
