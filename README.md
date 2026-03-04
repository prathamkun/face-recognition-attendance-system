# Smart Face Recognition Attendance System

A web-based **AI-powered attendance system** that automatically marks attendance using **face recognition**.  
It prevents proxy attendance and manages lecture sessions with time limits.

Built with **Flask, OpenCV, Face Recognition, SQLite, and Bootstrap**.

---

## 🚀 Features

- 🔐 Admin Login & Signup
- 📷 Face Recognition Attendance
- ⏱ Lecture Session Timer
- 👤 Prevents Proxy Attendance
- 📊 Attendance Records Dashboard
- 📱 Mobile Camera Compatible
- 💾 SQLite Database Storage
- 🎯 AI Face Encoding using `face_recognition`

---

## 🧠 How It Works

1. Admin logs into the system
2. Admin starts a **lecture session** with duration
3. Camera captures student faces
4. System compares with **trained encodings**
5. If matched → attendance is marked
6. Each student can be marked **only once per session**

---

## 🏗 Project Structure
```
face-recognition-attendance-system
│
├── app.py # Main Flask application
├── train.py # Face encoding training script
├── encodings.pkl # Saved trained face encodings
├── attendance.db # SQLite database
├── requirements.txt # Python dependencies
│
├── dataset/ # Face images for training
│
├── templates/
│ ├── index.html
│ ├── login.html
│ ├── signup.html
│ └── attendance.html
│
├── static/
│ └── style.css
│
└── .gitignore
```

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/prathamkun/face-recognition-attendance-system.git
cd face-recognition-attendance-system
```

Create virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```
Add Face Dataset:
 create Folder structure like:
 ```
dataset/
   student_name/
       img1.jpg
       img2.jpg
       img3.jpg
```
Example:
```
dataset/
   john/
       1.jpg
       2.jpg
   alice/
       1.jpg
       2.jpg
```
Train Face Model:
Run
```
python train.py
```
This will generate:
```
encoding.pkl
```
which stores all face embeddings
 

