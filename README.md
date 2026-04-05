#  Face Recognition Based Attendance System

An intelligent and automated attendance system that uses face recognition technology to detect and record attendance in real-time. This system eliminates manual effort and prevents proxy attendance using AI-based verification.

--

## 🚀 Features
🔐 Admin Login & Signup System
🎥 Real-time Face Recognition using Webcam
🧠 Machine Learning-based Face Encoding
⏱️ Session-based Attendance Tracking
❌ Prevents Duplicate Attendance
📊 Attendance Records Storage (SQLite)
🧾 Live Attendance Viewing Dashboard
👤 Face Registration via Website
📱 Responsive UI (Mobile Supported)
--
## 🛠️ Tech Stack
Frontend: HTML, CSS, Bootstrap
Backend: Python (Flask)
Libraries: OpenCV, face_recognition, NumPy
Database: SQLite
Others: Flask-Login, Pickle
--
## 📂 Project Structure
```
face-recognition-system/
│
├── app.py
├── train.py
├── encodings.pkl
├── attendance.db
├── requirements.txt
│
├── dataset/
│   └── person_name/
│       ├── 1.jpg
│       ├── 2.jpg
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── attendance.html
│   ├── register_face.html
│
├── static/
│   └── style.css
│
└── README.md
```
--
⚙️ Installation & Setup
1️⃣ Clone Repository
```
git clone https://github.com/your-username/face-recognition-system.git
cd face-recognition-system
```
--
2️⃣ Create Virtual Environment
```
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```
---
3️⃣ Install Dependencies
```
pip install -r requirements.txt
```
---
4️⃣ Train Model
```
python train.py
```
👉 This will generate:
```
encodings.pkl
```
---

