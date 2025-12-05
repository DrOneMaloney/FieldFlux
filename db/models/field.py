from typing import Dict, List, Optional

from pyproj import Transformer
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import transform

from data.storage import generate_id, load_db, save_db
from db.models.farmer import get_farmer
from db.models.field_history import add_history_entry

ACRE_CONVERSION = 4046.8564224
_transformer = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)


def _normalize_polygon(geometry: Dict) -> Polygon:
    if not geometry:
        raise ValueError("Geometry is required")
    geom = shape(geometry)
    if not isinstance(geom, Polygon):
        raise ValueError("Geometry must be a Polygon")
    if geom.is_empty or not geom.is_valid:
        raise ValueError("Polygon geometry is invalid")
    return geom


def _compute_acres(geom: Polygon) -> float:
    projected = transform(_transformer.transform, geom)
    square_meters = projected.area
    return round(square_meters / ACRE_CONVERSION, 4)


def _ensure_farmer_exists(farmer_id: str):
    if not get_farmer(farmer_id):
        raise ValueError("Farmer not found")


def _validate_overlap(farmer_id: str, new_geom: Polygon, field_id: Optional[str] = None):
    data = load_db()
    for field in data.get("fields", []):
        if field.get("farmerId") != farmer_id:
            continue
        if field_id and field["id"] == field_id:
            continue
        existing = shape(field["geometry"])
        if existing.overlaps(new_geom) or (
            existing.intersects(new_geom) and not existing.touches(new_geom)
        ):
            raise ValueError(
                f"Polygon overlaps with existing field '{field.get('name', 'Unnamed Field')}'."
            )


def list_fields_for_farmer(farmer_id: str) -> List[Dict]:
    data = load_db()
    return [field for field in data.get("fields", []) if field.get("farmerId") == farmer_id]


def get_field(farmer_id: str, field_id: str) -> Optional[Dict]:
    return next(
        (field for field in list_fields_for_farmer(farmer_id) if field["id"] == field_id),
        None,
    )


def create_field(farmer_id: str, payload: Dict) -> Dict:
    _ensure_farmer_exists(farmer_id)
    geom = _normalize_polygon(payload.get("geometry"))
    _validate_overlap(farmer_id, geom)

    data = load_db()
    field = {
        "id": generate_id(),
        "farmerId": farmer_id,
        "name": payload.get("name", "New Field").strip() or "New Field",
        "notes": payload.get("notes", ""),
        "geometry": mapping(geom),
        "acres": _compute_acres(geom),
    }
    data.setdefault("fields", []).append(field)
    save_db(data)
    add_history_entry(field["id"], "created", field)
    return field


def update_field(farmer_id: str, field_id: str, payload: Dict) -> Optional[Dict]:
    data = load_db()
    fields = data.get("fields", [])
    for field in fields:
        if field.get("id") == field_id and field.get("farmerId") == farmer_id:
            geom = _normalize_polygon(payload.get("geometry", field.get("geometry")))
            _validate_overlap(farmer_id, geom, field_id)
            previous = field.copy()
            field["name"] = payload.get("name", field["name"]).strip() or field["name"]
            field["notes"] = payload.get("notes", field.get("notes", ""))
            field["geometry"] = mapping(geom)
            field["acres"] = _compute_acres(geom)
            save_db(data)
            add_history_entry(field_id, "updated", previous)
            return field
    return None


def delete_field(farmer_id: str, field_id: str) -> bool:
    data = load_db()
    fields = data.get("fields", [])
    before = len(fields)
    data["fields"] = [
        f
        for f in fields
        if not (f.get("id") == field_id and f.get("farmerId") == farmer_id)
    ]
    removed = len(data["fields"]) < before
    if removed:
        save_db(data)
        add_history_entry(field_id, "deleted", {"fieldId": field_id})
    return removed
