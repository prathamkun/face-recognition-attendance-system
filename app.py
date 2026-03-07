from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pickle
import face_recognition
import numpy as np
from datetime import datetime, timedelta
import os
import io
import base64
from PIL import Image

app = Flask(__name__)
app.secret_key = "supersecretkey"

ENCODINGS_FILE = "encodings.pkl"
DB_FILE = "attendance.db"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"




class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1])
    return None




with open(ENCODINGS_FILE, "rb") as f:
    known_encodings, known_names = pickle.load(f)



def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT
        )
    """)

    # Sessions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_name TEXT,
            start_time TEXT,
            end_time TEXT
        )
    """)

   
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            lecture_name TEXT,
            time TEXT,
            UNIQUE(name, lecture_name)
        )
    """)

    conn.commit()
    conn.close()



def get_active_session():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    now = datetime.now().isoformat()

    cur.execute("""
        SELECT lecture_name, end_time
        FROM sessions
        WHERE end_time > ?
        ORDER BY id DESC
        LIMIT 1
    """, (now,))

    session = cur.fetchone()
    conn.close()
    return session



@app.route("/")
@login_required
def home():
    active_session = get_active_session()
    return render_template("index.html", active_session=active_session)


@app.route("/start_session", methods=["POST"])
@login_required
def start_session():
    lecture_name = request.form["lecture_name"]
    duration = int(request.form["duration"])

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sessions (lecture_name, start_time, end_time)
        VALUES (?, ?, ?)
    """, (lecture_name, start_time.isoformat(), end_time.isoformat()))
    conn.commit()
    conn.close()

    return redirect(url_for("home"))


@app.route("/attendance")
@login_required
def attendance_page():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        SELECT name, lecture_name, time
        FROM attendance
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return render_template("attendance.html", rows=rows)


@app.route("/predict", methods=["POST"])
@login_required
def predict():

    active_session = get_active_session()

    if not active_session:
        return jsonify({
            "success": False,
            "message": "Session expired"
        })

    lecture_name = active_session[0]

    if "image" not in request.files:
        return jsonify({"success": False, "faces": []})

    file = request.files["image"]
    img = face_recognition.load_image_file(file)

    face_locations = face_recognition.face_locations(img)
    face_encodings = face_recognition.face_encodings(img, face_locations)

    if len(face_encodings) == 0:
        return jsonify({"success": False, "faces": []})

    results = []

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = int(np.argmin(face_distances))

        if face_distances[best_match_index] < 0.50:
            name = known_names[best_match_index]

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR IGNORE INTO attendance (name, lecture_name, time)
                VALUES (?, ?, ?)
            """, (name, lecture_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
            conn.close()

        else:
            name = "Unknown"

        results.append({
            "name": name,
            "box": {"top": top, "right": right, "bottom": bottom, "left": left}
        })

    return jsonify({"success": True, "faces": results})

@app.route("/register_face", methods=["GET", "POST"])
@login_required
def register_face():
    global known_encodings, known_names

    if request.method == "GET":
        return render_template("register_face.html")
    
    # POST request handling
    data = request.json
    name = data.get("name")
    images_base64 = data.get("images", [])

    if not name or not images_base64:
        return jsonify({"success": False, "message": "Name and images are required."})
    
    # Create directory for the person if it doesn't exist
    dataset_dir = os.path.join("dataset", name)
    os.makedirs(dataset_dir, exist_ok=True)

    saved_count = 0
    for i, img_b64 in enumerate(images_base64):
        try:
            # Remove header if present (e.g., "data:image/jpeg;base64,")
            if "," in img_b64:
                img_b64 = img_b64.split(",")[1]
            
            img_data = base64.b64decode(img_b64)
            
            # Save raw JPEG bytes directly to file
            img_path = os.path.join(dataset_dir, f"{i}.jpg")
            with open(img_path, "wb") as img_file:
                img_file.write(img_data)
            
            saved_count += 1

        except Exception as e:
            print(f"Error saving image {i}: {e}")
            continue
    
    if saved_count == 0:
        return jsonify({"success": False, "message": "Failed to save any images."})

    # Run train.py to retrain the model with the new dataset
    import subprocess
    import sys
    try:
        result = subprocess.run(
            [sys.executable, "train.py"],
            capture_output=True, text=True, timeout=120
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"train.py error: {result.stderr}")
            return jsonify({"success": False, "message": f"Training failed: {result.stderr}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Training error: {str(e)}"})

    # Reload the updated encodings into memory
    with open(ENCODINGS_FILE, "rb") as f:
        known_encodings, known_names = pickle.load(f)

    return jsonify({"success": True, "message": f"Saved {saved_count} images and trained model successfully! Total faces: {len(known_names)}"})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT id, email, password_hash FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            login_user(User(user[0], user[1]))
            return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, (name, email, password))
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)