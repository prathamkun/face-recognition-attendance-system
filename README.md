#  Face Recognition Based Attendance System

An intelligent and automated attendance system that uses face recognition technology to detect and record attendance in real-time. This system eliminates manual effort and prevents proxy attendance using AI-based verification.

---

## 🚀 Features
```
🔐 Admin Login & Signup System
🎥 Real-time Face Recognition using Webcam
🧠 Machine Learning-based Face Encoding
⏱️ Session-based Attendance Tracking
❌ Prevents Duplicate Attendance
📊 Attendance Records Storage (SQLite)
🧾 Live Attendance Viewing Dashboard
👤 Face Registration via Website
📱 Responsive UI (Mobile Supported)
```
---
## 🛠️ Tech Stack
Frontend: HTML, CSS, Bootstrap
Backend: Python (Flask)
Libraries: OpenCV, face_recognition, NumPy
Database: SQLite
Others: Flask-Login, Pickle
---
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
---
⚙️ Installation & Setup
1️⃣ Clone Repository
```
git clone https://github.com/your-username/face-recognition-system.git
cd face-recognition-system
```
---
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
5️⃣ Run Application
```
python app.py
```
👉 Open in browser:
```
http://127.0.0.1:5000
```
---
## 📸 How It Works
1. Register user face via website
2. Images stored in dataset
3. Model generates facial encodings
4. Webcam captures live video
5. Faces detected & matched
6. Attendance marked automatically
7. Stored in SQLite database

---
## 🧠 Algorithm Used
Face detection & encoding using face_recognition (dlib-based model)
Matching using Euclidean Distance
Threshold-based recognition (0.50)

---


## 🛡️ Key Functionalities
✅ Multi-frame confirmation (prevents false detection)
✅ Session timer system
✅ Unique attendance per lecture
✅ Roll number validation (auto format like 03)
✅ Error handling for camera & recognition

---

## 📊 Database Schema
Users Table
```
id
name
email
password_hash
```
Sessions Table
```
id
lecture_name
start_time
end_time
```
Attendance Table
```
id
name
lecture_name
time
```

---

## ⚠️ Notes
- Dataset should NOT be pushed to GitHub (use .gitignore)
- Ensure camera permission is enabled
- Best accuracy with clear face images

---

## 🔮 Future Improvements
- 🌐 Cloud deployment
- 📱 Mobile app integration
- 📷 Multi-camera support
- 📊 Analytics dashboard
- 🤖 Deep learning models (CNN, FaceNet)

---


## 👨‍💻 Contributors
- Prathamesh Borkar
- Manas Ghadshi
- Satyam Khandual
- Abhi Mhaparle

---

📜 License

This project is for academic purposes.

---
⭐ Support

If you like this project, give it a ⭐ on GitHub!
