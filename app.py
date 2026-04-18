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
import subprocess
import sys
import re

app = Flask(__name__)
app.secret_key = "supersecretkey"

ENCODINGS_FILE = "encodings.pkl"
DB_FILE = "attendance.db"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# =============================
# USER CLASS
# =============================

class User(UserMixin):
    def __init__(self, id, email, name=None):
        self.id = id
        self.email = email
        self.name = name or email


@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_FILE, timeout=10)
    cur = conn.cursor()

    cur.execute("SELECT id, email, name FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()

    conn.close()

    if user:
        return User(user[0], user[1], user[2])

    return None


# =============================
# LOAD ENCODINGS SAFELY
# =============================

known_encodings = []
known_names = []

if os.path.exists(ENCODINGS_FILE):
    with open(ENCODINGS_FILE, "rb") as f:
        known_encodings, known_names = pickle.load(f)


# =============================
# DATABASE INIT
# =============================

def init_db():

    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT
        )
    """)

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
            session_date TEXT,
            time TEXT,
            UNIQUE(name, lecture_name, session_date)
        )
    """)

    # Registered faces table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registered_faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll_no TEXT UNIQUE
        )
    """)

    # Subjects table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            teacher_name TEXT NOT NULL
        )
    """)

    # Pre-seed subjects if table is empty
    cur.execute("SELECT COUNT(*) FROM subjects")
    if cur.fetchone()[0] == 0:
        default_subjects = [
            ("Logic and Data Interpretation (OE)", "Mrs. Bagayatkar K. M."),
            ("Mini Project", "Ms. Sakpal S. R."),
            ("Web Technology (MDM)", "Ms. Panchal D. S."),
            ("Operating System", "Mrs. Vankar P. P."),
            ("BMD", "Mr. Wategaonkar R. D."),
            ("Computational Theory", "Mr. Pusalkar P. V."),
            ("DBMS", "Ms. Mohite B. B."),
            ("Design Thinking", "Ms. Dongare P. A."),
        ]
        cur.executemany("INSERT INTO subjects (subject_name, teacher_name) VALUES (?, ?)", default_subjects)

    conn.commit()
    conn.close()


# =============================
# ACTIVE SESSION
# =============================

def get_active_session():

    conn = sqlite3.connect(DB_FILE, timeout=10)
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


# =============================
# HOME PAGE
# =============================

@app.route("/")
@login_required
def home():

    active_session = get_active_session()

    conn = sqlite3.connect(DB_FILE, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT id, subject_name, teacher_name FROM subjects ORDER BY subject_name")
    subjects = cur.fetchall()
    conn.close()

    return render_template(
        "index.html",
        active_session=active_session,
        subjects=subjects
    )


# =============================
# START SESSION
# =============================

@app.route("/start_session", methods=["POST"])
@login_required
def start_session():

    # Prevent overlapping sessions
    if get_active_session():
        return redirect(url_for("home"))

    subject_id = request.form.get("subject_id")
    duration = int(request.form["duration"])

    # Look up subject + teacher to build lecture name
    conn = sqlite3.connect(DB_FILE, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT subject_name, teacher_name FROM subjects WHERE id=?", (subject_id,))
    subject = cur.fetchone()

    if not subject:
        conn.close()
        return redirect(url_for("home"))

    lecture_name = f"{subject[0]} — {subject[1]}"

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration)

    cur.execute("""
        INSERT INTO sessions (lecture_name, start_time, end_time)
        VALUES (?, ?, ?)
    """, (lecture_name, start_time.isoformat(), end_time.isoformat()))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# =============================
# MANAGE SUBJECTS
# =============================

@app.route("/add_subject", methods=["POST"])
@login_required
def add_subject():
    subject_name = request.form.get("subject_name", "").strip()
    teacher_name = request.form.get("teacher_name", "").strip()

    if subject_name and teacher_name:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cur = conn.cursor()
        cur.execute("INSERT INTO subjects (subject_name, teacher_name) VALUES (?, ?)", (subject_name, teacher_name))
        conn.commit()
        conn.close()

    return redirect(url_for("home"))


@app.route("/delete_subject/<int:subject_id>", methods=["POST"])
@login_required
def delete_subject(subject_id):
    conn = sqlite3.connect(DB_FILE, timeout=10)
    cur = conn.cursor()
    cur.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# =============================
# STOP SESSION
# =============================

@app.route("/stop_session", methods=["POST"])
@login_required
def stop_session():

    now = datetime.now().isoformat()

    conn = sqlite3.connect(DB_FILE, timeout=10)
    cur = conn.cursor()

    cur.execute("""
        UPDATE sessions
        SET end_time = ?
        WHERE end_time > ?
    """, (now, now))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# =============================
# ATTENDANCE PAGE
# =============================

@app.route("/attendance")
@login_required
def attendance_page():

    from collections import OrderedDict

    # Read filter params
    filter_subject = request.args.get("subject", "").strip()
    filter_date = request.args.get("date", "").strip()
    filter_search = request.args.get("search", "").strip()

    conn = sqlite3.connect(DB_FILE, timeout=10)
    cur = conn.cursor()

    # Fetch distinct subjects and dates for dropdowns
    cur.execute("SELECT DISTINCT lecture_name FROM attendance ORDER BY lecture_name ASC")
    all_subjects = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT DATE(time) FROM attendance ORDER BY DATE(time) DESC")
    all_dates_raw = [row[0] for row in cur.fetchall() if row[0]]
    # Convert to DD-MM-YYYY for display, keep YYYY-MM-DD as value
    all_dates = []
    for d in all_dates_raw:
        try:
            display = datetime.strptime(d, "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            display = d
        all_dates.append({"value": d, "display": display})

    # Build filtered query
    query = "SELECT name, lecture_name, time FROM attendance WHERE 1=1"
    params = []

    if filter_subject:
        query += " AND lecture_name = ?"
        params.append(filter_subject)

    if filter_date:
        query += " AND DATE(time) = ?"
        params.append(filter_date)

    if filter_search:
        query += " AND name LIKE ?"
        params.append(f"%{filter_search}%")

    query += " ORDER BY DATE(time) DESC, lecture_name ASC, name ASC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    # Group rows into: { date_str: { session_name: [ {name, roll_no, time} ] } }
    grouped = OrderedDict()
    for full_name, lecture_name, time_str in rows:
        # Extract name and roll_no from "Name (roll_no)" format
        match = re.match(r'^(.+?)\s*\((\S+)\)$', full_name)
        if match:
            display_name = match.group(1).strip()
            roll_no = match.group(2)
        else:
            display_name = full_name
            roll_no = '-'
        if ' ' in time_str:
            date_part, time_part = time_str.split(' ', 1)
        else:
            date_part = time_str
            time_part = ''
        # Convert YYYY-MM-DD to DD-MM-YYYY
        try:
            date_part = datetime.strptime(date_part, "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            pass
        if date_part not in grouped:
            grouped[date_part] = OrderedDict()
        if lecture_name not in grouped[date_part]:
            grouped[date_part][lecture_name] = []
        grouped[date_part][lecture_name].append({
            'name': display_name,
            'roll_no': roll_no,
            'time': time_part,
        })

    return render_template(
        "attendance.html",
        grouped=grouped,
        all_subjects=all_subjects,
        all_dates=all_dates,
        filter_subject=filter_subject,
        filter_date=filter_date,
        filter_search=filter_search,
    )


# =============================
# STUDENT DASHBOARD
# =============================

@app.route("/dashboard")
@login_required
def dashboard():

    conn = sqlite3.connect(DB_FILE, timeout=10)
    cur = conn.cursor()

    # Get all registered students
    cur.execute("SELECT name, roll_no FROM registered_faces ORDER BY roll_no ASC")
    students = cur.fetchall()

    # Get total sessions per subject (lecture_name)
    cur.execute("""
        SELECT lecture_name, COUNT(*) as total
        FROM sessions
        GROUP BY lecture_name
    """)
    sessions_per_subject = {row[0]: row[1] for row in cur.fetchall()}

    # Total distinct sessions
    cur.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cur.fetchone()[0]

    # Get all distinct subjects from sessions
    subject_list = sorted(sessions_per_subject.keys())

    # Build per-student analytics
    student_data = []
    for student_name, roll_no in students:
        full_name = f"{student_name} ({roll_no})"

        # Per-subject attendance for this student
        cur.execute("""
            SELECT lecture_name, COUNT(*) as attended
            FROM attendance
            WHERE name = ?
            GROUP BY lecture_name
        """, (full_name,))
        attended_map = {row[0]: row[1] for row in cur.fetchall()}

        # Subject-wise breakdown
        subject_breakdown = []
        total_attended = 0
        total_possible = 0
        for subj in subject_list:
            conducted = sessions_per_subject.get(subj, 0)
            attended = attended_map.get(subj, 0)
            total_attended += attended
            total_possible += conducted
            pct = round((attended / conducted) * 100) if conducted > 0 else 0
            subject_breakdown.append({
                'subject': subj,
                'attended': attended,
                'conducted': conducted,
                'percentage': pct,
            })

        overall_pct = round((total_attended / total_possible) * 100) if total_possible > 0 else 0

        student_data.append({
            'name': student_name,
            'roll_no': roll_no,
            'total_attended': total_attended,
            'total_possible': total_possible,
            'overall_pct': overall_pct,
            'subjects': subject_breakdown,
        })

    # Compute class-wide stats
    avg_pct = round(sum(s['overall_pct'] for s in student_data) / len(student_data)) if student_data else 0
    low_attendance = sum(1 for s in student_data if s['overall_pct'] < 75)

    conn.close()

    return render_template(
        "dashboard.html",
        student_data=student_data,
        subject_list=subject_list,
        total_sessions=total_sessions,
        total_students=len(students),
        avg_pct=avg_pct,
        low_attendance=low_attendance,
    )


# =============================
# FACE PREDICTION
# =============================

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

    conn = sqlite3.connect(DB_FILE, timeout=10)
    cur = conn.cursor()

    results = []

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

        if len(known_encodings) == 0:
            results.append({
                "name": "Unknown",
                "box": {"top": top, "right": right, "bottom": bottom, "left": left},
                "already_marked": False
            })
            continue

        face_distances = face_recognition.face_distance(
            known_encodings,
            face_encoding
        )

        best_match_index = int(np.argmin(face_distances))

        if face_distances[best_match_index] < 0.45:

            name = known_names[best_match_index]

            today = datetime.now().strftime("%Y-%m-%d")

            cur.execute("""
                SELECT COUNT(*)
                FROM attendance
                WHERE name=? AND lecture_name=? AND session_date=?
            """, (name, lecture_name, today))

            already_exists = cur.fetchone()[0] > 0

            if not already_exists:

                cur.execute("""
                    INSERT INTO attendance (name, lecture_name, session_date, time)
                    VALUES (?, ?, ?, ?)
                """, (
                    name,
                    lecture_name,
                    today,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                conn.commit()

        else:

            name = "Unknown"
            already_exists = False

        results.append({
            "name": name,
            "box": {
                "top": top,
                "right": right,
                "bottom": bottom,
                "left": left
            },
            "already_marked": already_exists
        })

    conn.close()

    return jsonify({
        "success": True,
        "faces": results
    })


# =============================
# REGISTER FACE
# =============================

def normalize_roll_no(raw):
    digits = re.sub(r'[^0-9]', '', raw)

    if not digits:
        return ''

    return f"C-{int(digits):02d}"


@app.route("/check_roll_no", methods=["POST"])
@login_required
def check_roll_no():
    data = request.json
    roll_no = normalize_roll_no(data.get("roll_no", ""))
    if not roll_no:
        return jsonify({"exists": False})
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM registered_faces WHERE roll_no=?", (roll_no,))
    exists = cur.fetchone()[0] > 0
    conn.close()
    return jsonify({"exists": exists})


@app.route("/register_face", methods=["GET", "POST"])
@login_required
def register_face():

    global known_encodings, known_names

    if request.method == "GET":
        return render_template("register_face.html")

    data = request.json

    name = data.get("name")
    roll_no = normalize_roll_no(data.get("roll_no", ""))
    images_base64 = data.get("images", [])

    if not name or not roll_no or not images_base64:
        return jsonify({"success": False, "message": "Name, Roll Number, and images are required."})

    # Check if roll number already exists
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM registered_faces WHERE roll_no=?", (roll_no,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return jsonify({"success": False, "message": "Roll number already registered"})
    conn.close()

    # Check if this face is already registered
    if known_encodings:
        first_img_b64 = images_base64[0]
        if "," in first_img_b64:
            first_img_b64 = first_img_b64.split(",")[1]
        img_data = base64.b64decode(first_img_b64)
        img = face_recognition.load_image_file(io.BytesIO(img_data))
        new_encodings = face_recognition.face_encodings(img)
        if new_encodings:
            distances = face_recognition.face_distance(known_encodings, new_encodings[0])
            if min(distances) < 0.45:
                best_idx = int(np.argmin(distances))
                existing_name = known_names[best_idx]
                return jsonify({
                    "success": False,
                    "message": f"This face is already registered as {existing_name}!"
                })

    # Use roll_no as dataset folder name for uniqueness
    folder_name = f"{name} ({roll_no})"
    dataset_dir = os.path.join("dataset", folder_name)
    os.makedirs(dataset_dir, exist_ok=True)

    saved_count = 0

    for i, img_b64 in enumerate(images_base64):

        if "," in img_b64:
            img_b64 = img_b64.split(",")[1]

        img_data = base64.b64decode(img_b64)

        img_path = os.path.join(dataset_dir, f"{i}.jpg")

        with open(img_path, "wb") as f:
            f.write(img_data)

        saved_count += 1

    subprocess.run(
        [sys.executable, "train.py"],
        capture_output=True,
        text=True
    )

    if os.path.exists(ENCODINGS_FILE):

        with open(ENCODINGS_FILE, "rb") as f:
            known_encodings, known_names = pickle.load(f)

    # Save name and roll_no to database
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO registered_faces (name, roll_no) VALUES (?, ?)", (name, roll_no))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Saved {saved_count} images and trained model for {name} (Roll: {roll_no})! Total faces: {len(known_names)}"})


# =============================
# LOGIN
# =============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_FILE, timeout=10)
        cur = conn.cursor()

        cur.execute("""
            SELECT id, email, password_hash
            FROM users
            WHERE email=?
        """, (email,))

        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):
            # Fetch name for the user
            conn2 = sqlite3.connect(DB_FILE, timeout=10)
            cur2 = conn2.cursor()
            cur2.execute("SELECT name FROM users WHERE id=?", (user[0],))
            name_row = cur2.fetchone()
            conn2.close()
            user_name = name_row[0] if name_row else user[1]

            login_user(User(user[0], user[1], user_name))

            return redirect(url_for("home"))

    return render_template("login.html")


# =============================
# SIGNUP
# =============================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]

        password = generate_password_hash(
            request.form["password"]
        )

        conn = sqlite3.connect(DB_FILE, timeout=10)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, (name, email, password))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


# =============================
# LOGOUT
# =============================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


# =============================
# MAIN
# =============================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)