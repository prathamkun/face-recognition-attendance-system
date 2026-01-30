# Smart Face Recognition Attendance System 🎥✅

A Smart Face Recognition based Attendance System built using **Flask + OpenCV + face_recognition (dlib)**.
It detects faces from webcam, recognizes known users, and marks attendance automatically using a smart confirmation logic.

Live Demo: https://web-production-3014.up.railway.app/
---

## 🚀 Features
- ✅ Face Recognition using trained encodings (`encodings.pkl`)
- ✅ Smart Auto Attendance Mode (marks only after confirming face 3 times)
- ✅ Prevents duplicate attendance for same user on same day
- ✅ Attendance stored in **SQLite Database**
- ✅ Admin page to view attendance records
---

## 🛠 Tech Stack
- Python 3.11
- Flask
- OpenCV
- face_recognition / dlib
- SQLite3
- HTML + Bootstrap (CDN)
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
│ ├── person1/
│ └── person2/
│
└── templates/
├── index.html
└── attendance.html
```
