from flask import Flask, request, jsonify, render_template
import pickle
import face_recognition
import numpy as np
import sqlite3
from datetime import datetime

app = Flask(__name__)

ENCODINGS_FILE = "encodings.pkl"
DB_FILE = "attendance.db"

# Load encodings
with open(ENCODINGS_FILE, "rb") as f:
    known_encodings, known_names = pickle.load(f)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

def mark_attendance(name):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Prevent duplicate entry same day
    cur.execute("SELECT * FROM attendance WHERE name=? AND date=?", (name, date))
    exists = cur.fetchone()

    if not exists:
        cur.execute(
            "INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)",
            (name, date, time)
        )
        conn.commit()

    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/attendance")
def attendance_page():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    rows = cur.execute("SELECT name, date, time FROM attendance ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("attendance.html", rows=rows)

@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image received", "faces": []}), 400

    file = request.files["image"]
    img = face_recognition.load_image_file(file)

    face_locations = face_recognition.face_locations(img)
    face_encodings = face_recognition.face_encodings(img, face_locations)

    if len(face_encodings) == 0:
        return jsonify({"success": False, "message": "No face detected", "faces": []}), 200

    results = []

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = int(np.argmin(face_distances))

        if face_distances[best_match_index] < 0.50:
            name = known_names[best_match_index]
            mark_attendance(name)
        else:
            name = "Unknown"

        results.append({
            "name": name,
            "box": {"top": top, "right": right, "bottom": bottom, "left": left}
        })

    return jsonify({"success": True, "message": "Done ✅", "faces": results}), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
