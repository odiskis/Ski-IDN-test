from flask import Flask, request, jsonify, session, send_from_directory
import json, os, uuid, hashlib
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "skitest-ntnu-2026-odin")

DATA_FILE = "data/responses.json"
os.makedirs("data", exist_ok=True)

STATUS_FILE = "data/study_status.json"

def is_study_open():
    if not os.path.exists(STATUS_FILE):
        return True
    with open(STATUS_FILE) as f:
        return json.load(f).get("open", True)

def set_study_open(value):
    with open(STATUS_FILE, "w") as f:
        json.dump({"open": value}, f)

CLOSED_MESSAGE = "Brukertesten tar ikke lengre imot svar. Tusen takk for at du ville bidra!"

ADMIN_PW_HASH = hashlib.sha256(b"ntnu2026odin").hexdigest()

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def check_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest() == ADMIN_PW_HASH

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/admin")
def admin():
    return send_from_directory("static", "admin.html")

@app.route("/kart.png")
def kart():
    return send_from_directory(".", "kart.png")

@app.route("/maps/<path:filename>")
def maps_folder(filename):
    return send_from_directory("static/maps", filename)

@app.route("/topomap.js")
def topomap_js():
    return send_from_directory("static/js", "topomap.js")

@app.route("/api/status")
def study_status():
    return jsonify({"open": is_study_open(), "message": CLOSED_MESSAGE})

@app.route("/api/start", methods=["POST"])
def start_session():
    if not is_study_open():
        return jsonify({"error": "closed", "message": CLOSED_MESSAGE}), 403
    participant_id = str(uuid.uuid4())[:8]
    session["pid"] = participant_id
    return jsonify({"pid": participant_id})

@app.route("/api/submit", methods=["POST"])
def submit():
    if not is_study_open():
        return jsonify({"error": "closed", "message": CLOSED_MESSAGE}), 403
    data = request.get_json()
    pid = session.get("pid", str(uuid.uuid4())[:8])
    responses = load_data()

    # `tasks` is an object with one key per task (e.g. "topp" and "dal").
    # Each task contains `time_seconds`, `status` ("finished"/"gaveup"),
    # and `distance_m`. `distance_m` is a placeholder (None) until the
    # terrain model (Unity) sends real distance data via postMessage.
    entry = {
        "pid": pid,
        "timestamp": datetime.now().isoformat(),
        "ski_experience": data.get("ski_experience"),
        "map_experience": data.get("map_experience"),
        "tasks": data.get("tasks", {}),
        "survey": data.get("survey", {})
    }
    responses.append(entry)
    save_data(responses)
    return jsonify({"ok": True, "pid": pid})

@app.route("/api/admin/data", methods=["GET"])
def admin_data():
    pw = request.args.get("pw", "")
    if not check_pw(pw):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(load_data())

@app.route("/api/admin/delete/<pid>", methods=["GET","POST","DELETE"])
def delete_entry(pid):
    pw = request.args.get("pw", "")
    if not check_pw(pw):
        return jsonify({"error": "Unauthorized"}), 401
    responses = [r for r in load_data() if r.get("pid") != pid]
    save_data(responses)
    return jsonify({"ok": True})

@app.route("/api/admin/delete-all", methods=["GET","DELETE","POST"])
def delete_all():
    pw = request.args.get("pw", "")
    if not check_pw(pw):
        return jsonify({"error": "Unauthorized"}), 401
    save_data([])
    return jsonify({"ok": True})

@app.route("/api/admin/toggle-study", methods=["POST"])
def toggle_study():
    pw = request.args.get("pw", "")
    if not check_pw(pw):
        return jsonify({"error": "Unauthorized"}), 401
    new_state = not is_study_open()
    set_study_open(new_state)
    return jsonify({"ok": True, "open": new_state})

if __name__ == "__main__":
    app.run(debug=True, port=5050)
