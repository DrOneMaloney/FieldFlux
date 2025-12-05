from typing import Dict, List, Optional

from data.storage import generate_id, load_db, save_db


def list_farmers() -> List[Dict]:
    data = load_db()
    return data.get("farmers", [])


def get_farmer(farmer_id: str) -> Optional[Dict]:
    return next((farmer for farmer in list_farmers() if farmer["id"] == farmer_id), None)


def create_farmer(payload: Dict) -> Dict:
    data = load_db()
    farmer = {
        "id": generate_id(),
        "name": payload.get("name", "Unnamed Farmer").strip() or "Unnamed Farmer",
        "contact": payload.get("contact", ""),
    }
    data.setdefault("farmers", []).append(farmer)
    save_db(data)
    return farmer


def update_farmer(farmer_id: str, payload: Dict) -> Optional[Dict]:
    data = load_db()
    for farmer in data.get("farmers", []):
        if farmer["id"] == farmer_id:
            farmer["name"] = payload.get("name", farmer["name"]).strip() or farmer["name"]
            farmer["contact"] = payload.get("contact", farmer.get("contact", ""))
            save_db(data)
            return farmer
    return None


def delete_farmer(farmer_id: str) -> bool:
    data = load_db()
    farmers = data.get("farmers", [])
    fields = data.get("fields", [])
    before_count = len(farmers)
    data["farmers"] = [f for f in farmers if f["id"] != farmer_id]
    data["fields"] = [field for field in fields if field.get("farmerId") != farmer_id]
    save_db(data)
    return len(data["farmers"]) < before_count
