# ⚛️ Keya Fusion – AI Face Recognition Attendance System

**Keya Fusion** is a premium, fast, and robust attendance management system powered by Python, Flask, and OpenCV. It uses cutting-edge AI to recognize faces in real-time and manages attendance logs in a cloud-hosted Supabase database.

---

## ✨ Key Features

- **🛡️ Admin Dashboard**: Full control over employee registration, record management, and attendance history in a sleek AI-themed interface.
- **🖥️ Dedicated User Kiosk**: A high-performance, responsive screen for employees to mark attendance via face recognition.
- **☁️ Cloud Database (Supabase)**: Persistent storage in the cloud, allowing the system to be accessed from anywhere.
- **⚡ Real-time Recognition**: High-speed "Fusion" engine for instantaneous marking (~0.6s).
- **📊 Excel Export**: Download detailed analytical reports with a single click.
- **🛠️ AI Registration**: Robust capture system that takes multiple samples per person for maximum accuracy.

---

## 🚀 Quick Start (Local Setup)

### 1. Requirements
Ensure you have **Python 3.10+** installed.

### 2. Installation
Double-click **`run_app.bat`**. This will:
- Create a virtual environment (`venv`).
- Install all dependencies (OpenCV, Flask, face_recognition, etc.).
- Start the server.

### 3. Cloud Database Setup (Supabase)
To enable cloud storage:
1. Create a project on [Supabase.com](https://supabase.com).
2. Go to **Settings > Database** and copy your **URI connection string**.
3. Open the **`.env`** file in the project folder.
4. Paste your link: `DATABASE_URL=your_supabase_uri_here`

---

## 🎬 Launchers

- **`run_app.bat`**: Launches the full Admin System.
- **`run_user_panel.bat`**: Launches the server and opens the **Keya Fusion Kiosk** directly.
- **`open_user_panel.bat`**: Just opens the kiosk in the browser.

---

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL (Supabase) / SQLite (Local Fallback)
- **Computer Vision**: OpenCV, dlib, face_recognition (HOG Model)
- **Frontend**: Glassmorphism UI (Keya Fusion Theme), JavaScript, PWA

---

## 📁 Project Structure

```text
├── app.py                # Main Flask Application
├── database.py           # Multi-mode Database Engine
├── face_utils.py         # AI Logic & Face Encoding
├── static/               # CSS (Keya Fusion Theme), JS, and Images
├── templates/            # HTML Interface
├── render.yaml           # Cloud Deployment Blueprint
└── .env                  # Cloud Configuration
```

---

## 📝 License
This project is part of the Keya Fusion suite.
