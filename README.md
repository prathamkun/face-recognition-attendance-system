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
