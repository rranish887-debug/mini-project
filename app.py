# ============================================================
#  AI Attendance System - Flask Backend
#  app.py - Main application entry point
# ============================================================

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import base64
import numpy as np
import cv2
import face_recognition
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "attendance_secret_key_change_in_prod_2024")

# ─── Admin Credentials (hardcoded for simplicity) ────────────────────────────
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ─── Database Helper ──────────────────────────────────────────────────────────
def get_db():
    """Connect to SQLite database."""
    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row  # Allows dict-style access
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    # Students table: stores name + face encoding
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            encoding  TEXT NOT NULL,       -- JSON array of face encoding floats
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Attendance table: one record per recognition event
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            name       TEXT NOT NULL,
            date       TEXT NOT NULL,
            time       TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialised successfully.")

# ─── Utility: decode base64 image → OpenCV frame ─────────────────────────────
def decode_image(b64_string):
    """Convert a base64-encoded image string into a NumPy BGR array."""
    # Strip the data-URL prefix if present  (e.g. "data:image/jpeg;base64,...")
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    img_bytes = base64.b64decode(b64_string)
    np_arr   = np.frombuffer(img_bytes, dtype=np.uint8)
    frame    = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame

# ─── Routes: Authentication ───────────────────────────────────────────────────
@app.route("/")
def root():
    """Redirect root to login page."""
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            session["username"]  = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─── Routes: Pages ────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/register")
def register_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/mark")
def mark_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("attendance.html")

@app.route("/records")
def records_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("records.html")

# ─── API: Register a New Student ──────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def api_register():
    """
    Receives: { name: str, image: base64 }
    Detects face, extracts encoding, saves to DB.
    """
    if not session.get("logged_in"):
        return jsonify({"success": False, "message": "Unauthorised"}), 401

    data  = request.get_json()
    name  = data.get("name", "").strip()
    image = data.get("image", "")

    if not name:
        return jsonify({"success": False, "message": "Student name is required."})
    if not image:
        return jsonify({"success": False, "message": "No image captured."})

    # Decode image
    frame = decode_image(image)
    if frame is None:
        return jsonify({"success": False, "message": "Could not decode image."})

    # Convert BGR → RGB (face_recognition uses RGB)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect face locations
    face_locations = face_recognition.face_locations(rgb)
    if len(face_locations) == 0:
        return jsonify({"success": False, "message": "No face detected. Please try again."})
    if len(face_locations) > 1:
        return jsonify({"success": False, "message": "Multiple faces detected. Please ensure only one person is in frame."})

    # Extract face encoding (128-dimensional vector)
    encoding = face_recognition.face_encodings(rgb, face_locations)[0]

    # Save to database
    conn = get_db()
    conn.execute(
        "INSERT INTO students (name, encoding) VALUES (?, ?)",
        (name, json.dumps(encoding.tolist()))
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"✅ '{name}' registered successfully!"})

# ─── API: Mark Attendance ─────────────────────────────────────────────────────
@app.route("/api/mark_attendance", methods=["POST"])
def api_mark_attendance():
    """
    Receives: { image: base64 }
    Compares face against all known encodings.
    Marks attendance if recognised (once per day).
    """
    if not session.get("logged_in"):
        return jsonify({"success": False, "message": "Unauthorised"}), 401

    data  = request.get_json()
    image = data.get("image", "")

    if not image:
        return jsonify({"success": False, "message": "No image provided."})

    # Decode image
    frame = decode_image(image)
    if frame is None:
        return jsonify({"success": False, "message": "Could not decode image."})

    rgb            = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)

    if len(face_locations) == 0:
        return jsonify({"success": False, "message": "No face detected. Please look at the camera."})

    # Get all registered students from DB
    conn     = get_db()
    students = conn.execute("SELECT id, name, encoding FROM students").fetchall()

    if not students:
        conn.close()
        return jsonify({"success": False, "message": "No students registered yet."})

    # Build arrays of known encodings + metadata
    known_encodings = []
    known_ids       = []
    known_names     = []
    for s in students:
        known_encodings.append(np.array(json.loads(s["encoding"])))
        known_ids.append(s["id"])
        known_names.append(s["name"])

    # Compute encoding for detected face
    face_encodings = face_recognition.face_encodings(rgb, face_locations)
    if not face_encodings:
        conn.close()
        return jsonify({"success": False, "message": "Could not extract face features."})

    unknown_encoding = face_encodings[0]

    # Compare against known encodings (tolerance 0.55 = stricter recognition)
    distances = face_recognition.face_distance(known_encodings, unknown_encoding)
    best_idx  = int(np.argmin(distances))
    best_dist = distances[best_idx]

    THRESHOLD = 0.55
    if best_dist > THRESHOLD:
        conn.close()
        return jsonify({"success": False, "message": "Face not recognised. Please register first."})

    student_id   = known_ids[best_idx]
    student_name = known_names[best_idx]
    today        = datetime.now().strftime("%Y-%m-%d")
    now_time     = datetime.now().strftime("%H:%M:%S")

    # Prevent duplicate attendance on same day
    existing = conn.execute(
        "SELECT id FROM attendance WHERE student_id=? AND date=?",
        (student_id, today)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({
            "success": False,
            "message": f"⚠️ Attendance already marked for '{student_name}' today."
        })

    # Insert attendance record
    conn.execute(
        "INSERT INTO attendance (student_id, name, date, time) VALUES (?, ?, ?, ?)",
        (student_id, student_name, today, now_time)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"✅ Attendance marked for '{student_name}'!",
        "name":    student_name,
        "date":    today,
        "time":    now_time
    })

# ─── API: Fetch Attendance Records ────────────────────────────────────────────
@app.route("/api/attendance", methods=["GET"])
def api_attendance():
    """Return attendance records, optionally filtered by ?date=YYYY-MM-DD."""
    if not session.get("logged_in"):
        return jsonify({"success": False, "message": "Unauthorised"}), 401

    date_filter = request.args.get("date", "")
    conn        = get_db()

    if date_filter:
        rows = conn.execute(
            "SELECT * FROM attendance WHERE date=? ORDER BY date DESC, time DESC",
            (date_filter,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM attendance ORDER BY date DESC, time DESC"
        ).fetchall()

    conn.close()

    records = [dict(r) for r in rows]
    return jsonify({"success": True, "records": records})

# ─── API: Fetch All Registered Students ───────────────────────────────────────
@app.route("/api/students", methods=["GET"])
def api_students():
    """Return list of all registered students."""
    if not session.get("logged_in"):
        return jsonify({"success": False}), 401

    conn     = get_db()
    students = conn.execute(
        "SELECT id, name, created_at FROM students ORDER BY name"
    ).fetchall()
    conn.close()

    return jsonify({"success": True, "students": [dict(s) for s in students]})

# ─── API: Delete a Student ────────────────────────────────────────────────────
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_delete_student(student_id):
    if not session.get("logged_in"):
        return jsonify({"success": False}), 401

    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?",    (student_id,))
    conn.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Student deleted."})

# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()   # Create tables on first run
    port = int(os.environ.get("PORT", 5000))
    is_dev = os.environ.get("REPL_ID") is None  # disable debug on Replit
    print(f"🚀 Server running → http://0.0.0.0:{port}")
    app.run(debug=is_dev, host="0.0.0.0", port=port)
