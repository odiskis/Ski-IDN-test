from flask import Flask, request, jsonify, session, send_from_directory, send_file
import json, os, uuid, hashlib, base64, io
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "skitest-ntnu-2026-odin")

DATA_FILE = "data/responses.json"
os.makedirs("data", exist_ok=True)

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
    if not check_pw(pw):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(load_data())

@app.route("/api/admin/combined/<pid>", methods=["GET"])
def combined_map(pid):
    pw = request.args.get("pw", "")
    if not check_pw(pw):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        from PIL import Image
    except ImportError:
        return jsonify({"error": "PIL not installed"}), 500

    responses = load_data()
    entry = next((r for r in responses if r.get("pid") == pid), None)
    if not entry:
        return jsonify({"error": "Not found"}), 404

    # Start with base map
    base_path = os.path.join(os.path.dirname(__file__), "kart.png")
    if os.path.exists(base_path):
        base = Image.open(base_path).convert("RGBA")
    else:
        base = Image.new("RGBA", (1200, 780), (200, 220, 180, 255))

    def extract_strokes(data_url, base_size):
        """Extract only the drawn strokes from a canvas PNG by removing the map background."""
        b64 = data_url.split(",")[1] if "," in data_url else data_url
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        img = img.resize(base_size, Image.LANCZOS)
        pixels = img.load()
        w, h = img.size
        # Make white/near-white pixels transparent so only strokes show
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                brightness = (r + g + b) / 3
                if brightness > 200:
                    pixels[x, y] = (r, g, b, 0)
        return img

    # Overlay route_before (red strokes)
    if entry.get("route_before"):
        try:
            strokes = extract_strokes(entry["route_before"], base.size)
            base = Image.alpha_composite(base, strokes)
        except Exception as e:
            print("Error overlaying before:", e)

    # Overlay route_after (green strokes)
    if entry.get("route_after"):
        try:
            strokes = extract_strokes(entry["route_after"], base.size)
            base = Image.alpha_composite(base, strokes)
        except Exception as e:
            print("Error overlaying after:", e)

    output = io.BytesIO()
    base.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png",
                     download_name=f"kombinert_{pid}.png",
                     as_attachment=True)

@app.route("/api/admin/delete/<pid>", methods=["DELETE"])
def delete_entry(pid):
    pw = request.args.get("pw", "")
    if not check_pw(pw):
        return jsonify({"error": "Unauthorized"}), 401
    responses = [r for r in load_data() if r.get("pid") != pid]
    save_data(responses)
    return jsonify({"ok": True})

@app.route("/api/admin/delete-all", methods=["DELETE"])
def delete_all():
    pw = request.args.get("pw", "")
    if not check_pw(pw):
        return jsonify({"error": "Unauthorized"}), 401
    save_data([])
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True, port=5050)
