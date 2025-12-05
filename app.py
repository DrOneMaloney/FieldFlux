from flask import Flask, jsonify, request, send_from_directory
from db.models.farmer import list_farmers, create_farmer, get_farmer, update_farmer, delete_farmer
from db.models.field import (
    list_fields_for_farmer,
    create_field,
    get_field,
    update_field,
    delete_field,
)
from data.storage import load_db

app = Flask(__name__, static_folder="public", static_url_path="")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/farmers", methods=["GET"])
def api_list_farmers():
    farmers = list_farmers()
    summary = []
    data = load_db()
    for farmer in farmers:
        fields = [f for f in data.get("fields", []) if f.get("farmerId") == farmer["id"]]
        acres = sum(f.get("acres", 0) for f in fields)
        summary.append({**farmer, "fieldCount": len(fields), "totalAcres": round(acres, 4)})
    return jsonify(summary)


@app.route("/api/farmers", methods=["POST"])
def api_create_farmer():
    payload = request.get_json(force=True)
    if not payload or not payload.get("name"):
        return jsonify({"error": "Farmer name is required."}), 400
    farmer = create_farmer(payload)
    return jsonify(farmer), 201


@app.route("/api/farmers/<farmer_id>", methods=["GET"])
def api_get_farmer(farmer_id):
    farmer = get_farmer(farmer_id)
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404
    return jsonify(farmer)


@app.route("/api/farmers/<farmer_id>", methods=["PUT"])
def api_update_farmer(farmer_id):
    payload = request.get_json(force=True)
    farmer = update_farmer(farmer_id, payload)
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404
    return jsonify(farmer)


@app.route("/api/farmers/<farmer_id>", methods=["DELETE"])
def api_delete_farmer(farmer_id):
    removed = delete_farmer(farmer_id)
    if not removed:
        return jsonify({"error": "Farmer not found"}), 404
    return jsonify({"status": "deleted"})


@app.route("/api/farmers/<farmer_id>/fields", methods=["GET"])
def api_list_fields(farmer_id):
    fields = list_fields_for_farmer(farmer_id)
    return jsonify(fields)


@app.route("/api/farmers/<farmer_id>/fields", methods=["POST"])
def api_create_field(farmer_id):
    payload = request.get_json(force=True)
    try:
        field = create_field(farmer_id, payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(field), 201


@app.route("/api/farmers/<farmer_id>/fields/<field_id>", methods=["GET"])
def api_get_field(farmer_id, field_id):
    field = get_field(farmer_id, field_id)
    if not field:
        return jsonify({"error": "Field not found"}), 404
    return jsonify(field)


@app.route("/api/farmers/<farmer_id>/fields/<field_id>", methods=["PUT"])
def api_update_field(farmer_id, field_id):
    payload = request.get_json(force=True)
    try:
        field = update_field(farmer_id, field_id, payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if not field:
        return jsonify({"error": "Field not found"}), 404
    return jsonify(field)


@app.route("/api/farmers/<farmer_id>/fields/<field_id>", methods=["DELETE"])
def api_delete_field(farmer_id, field_id):
    removed = delete_field(farmer_id, field_id)
    if not removed:
        return jsonify({"error": "Field not found"}), 404
    return jsonify({"status": "deleted"})


@app.route("/api/farmers/<farmer_id>/summary", methods=["GET"])
def api_farmer_summary(farmer_id):
    farmer = get_farmer(farmer_id)
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404
    fields = list_fields_for_farmer(farmer_id)
    total_acres = round(sum(f.get("acres", 0) for f in fields), 4)
    return jsonify({"farmerId": farmer_id, "farmer": farmer, "totalAcres": total_acres, "fieldCount": len(fields)})


@app.route("/api/summary", methods=["GET"])
def api_summary():
    data = load_db()
    farmers = data.get("farmers", [])
    response = []
    for farmer in farmers:
        fields = [f for f in data.get("fields", []) if f.get("farmerId") == farmer["id"]]
        acres = sum(f.get("acres", 0) for f in fields)
        response.append({"farmerId": farmer["id"], "farmer": farmer, "totalAcres": round(acres, 4), "fieldCount": len(fields)})
    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
