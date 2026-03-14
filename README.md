# 👁️ SightSync – AI Face Recognition Attendance System

SightSync is a modern, fast, and robust attendance management system powered by Python, Flask, and OpenCV. It uses deep learning to recognize faces in real-time and manages attendance logs in a cloud-hosted Supabase database.

---

## ✨ Key Features

- **🛡️ Admin Dashboard**: Full control over employee registration, record management, and attendance history.
- **🖥️ Dedicated User Kiosk**: A premium, standalone screen for employees to mark attendance via face recognition.
- **☁️ Cloud Database (Supabase)**: Persistent storage in the cloud, allowing the system to be accessed from anywhere.
- **⚡ Real-time Recognition**: High-speed face detection for instantaneous marking.
- **📊 Excel Export**: Download detailed attendance reports with a single click.
- **🛠️ Robust Registration**: Smart capture system that takes 20 samples per person for maximum accuracy.

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
5. Replace `[YOUR-PASSWORD]` with your actual database password.

---

## 🎬 Launchers

We have provided dedicated launchers for different use cases:

- **`run_app.bat`**: Launches the full Admin System.
- **`run_user_panel.bat`**: Launches the server and opens the **User Kiosk** directly.
- **`open_user_panel.bat`**: Just opens the kiosk in the browser (use this if the server is already running).

---

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL (Supabase) / SQLite (Local Fallback)
- **Computer Vision**: OpenCV, dlib, face_recognition
- **Frontend**: Vanilla CSS (Glassmorphism), JavaScript (Fetch API), PWA (Mobile Support)
- **Data Analysis**: Pandas, OpenPyXL

---

## 📁 Project Structure

```text
├── app.py                # Main Flask Application
├── database.py           # Multi-mode Database Engine
├── face_utils.py         # AI Logic & Face Encoding
├── static/               # CSS, JS, and Images
├── templates/            # HTML Interface
├── run_app.bat           # Main System Launcher
├── run_user_panel.bat    # Dedicated Kiosk Launcher
└── .env                  # Cloud Configuration
```

---

## 📝 License
This project is open-source. Feel free to modify and adapt it for your needs.
