from datetime import datetime
from typing import Dict

from data.storage import generate_id, load_db, save_db


def add_history_entry(field_id: str, action: str, payload: Dict) -> Dict:
    data = load_db()
    entry = {
        "id": generate_id(),
        "fieldId": field_id,
        "action": action,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }
    data.setdefault("fieldHistory", []).append(entry)
    save_db(data)
    return entry
