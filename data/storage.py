import json
import uuid
from pathlib import Path
from typing import Any, Dict

DB_PATH = Path(__file__).resolve().parent / "db.json"

def _ensure_db_file():
    if not DB_PATH.exists():
        DB_PATH.write_text(json.dumps({"farmers": [], "fields": [], "fieldHistory": []}, indent=2))


def load_db() -> Dict[str, Any]:
    _ensure_db_file()
    with DB_PATH.open() as f:
        return json.load(f)


def save_db(data: Dict[str, Any]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DB_PATH.open("w") as f:
        json.dump(data, f, indent=2)


def generate_id() -> str:
    return uuid.uuid4().hex
