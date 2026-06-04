from flask import Flask, request, jsonify, session, send_from_directory
import json, os, uuid, hashlib
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "skitest-ntnu-2026-odin")

DATA_FILE = "data/responses.json"
os.makedirs("data", exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/admin")
def admin():
    return send_from_directory("static", "admin.html")

@app.route("/api/start", methods=["POST"])
def start_session():
    participant_id = str(uuid.uuid4())[:8]
    session["pid"] = participant_id
    return jsonify({"pid": participant_id})

@app.route("/api/submit", methods=["POST"])
def submit():
    data = request.get_json()
    pid = session.get("pid", str(uuid.uuid4())[:8])
    responses = load_data()
    entry = {
        "pid": pid,
        "timestamp": datetime.now().isoformat(),
        "experience": data.get("experience"),
        "route_before": data.get("route_before"),
        "route_before_reason": data.get("route_before_reason"),
        "route_after": data.get("route_after"),
        "route_after_reason": data.get("route_after_reason"),
        "route_changed": data.get("route_changed"),
        "survey": data.get("survey", {})
    }
    responses.append(entry)
    save_data(responses)
    return jsonify({"ok": True, "pid": pid})

@app.route("/api/admin/data", methods=["GET"])
def admin_data():
    pw = request.args.get("pw", "")
    if hashlib.sha256(pw.encode()).hexdigest() != hashlib.sha256(b"ntnu2026odin").hexdigest():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(load_data())

if __name__ == "__main__":
    app.run(debug=True, port=5050)
