# 🎓 FaceAttend AI — AI Attendance System

A **production-ready AI-powered attendance system** using face recognition. Register students once with their webcam photo, then automatically mark attendance by scanning their face.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 AI Face Recognition | Uses `face_recognition` (dlib) to encode and compare faces |
| 📸 Live Webcam Capture | In-browser webcam integration for registration & marking |
| ✅ Auto Attendance | One-click scan marks attendance — no duplicates per day |
| 📋 Records & Export | Filter by date/name, export to CSV |
| 🌐 Web Dashboard | Responsive dark glassmorphism UI |
| 🔒 Admin Auth | Session-based login to protect all routes |

---

## 🚀 Run Locally

### 1. Prerequisites

- Python 3.9+ 
- `cmake` (needed by dlib): Install from https://cmake.org/download/ or via `winget install cmake`
- A working webcam

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Note:** `face_recognition` requires `dlib` which compiles from source. This may take 5–10 minutes.

### 3. Start the Server

```bash
python app.py
```

Open → **http://localhost:5000**

### 4. Login

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

---

## 🌐 Hosting / Deployment

### Option A: Render.com (Recommended — Free Tier)

> ⚠️ **Important**: `face_recognition` (dlib) requires a C++ build environment. Render's free tier supports this.

1. Push your project to **GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ai-attendance.git
   git push -u origin main
   ```

2. Go to **[render.com](https://render.com)** → New → **Web Service**

3. Connect your GitHub repo

4. Set these settings:
   | Field | Value |
   |---|---|
   | Environment | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

5. Add environment variable:
   - `SECRET_KEY` → any long random string

6. Click **Deploy** — your app will be live at `https://your-app.onrender.com`

---

### Option B: Railway.app

1. Install Railway CLI: `npm install -g @railway/cli`
2. `railway login`
3. `railway init`
4. `railway up`

The `Procfile` is already configured for Railway.

---

### Option C: Local Network (LAN)

The app already binds to `0.0.0.0:5000`, so anyone on your local network can access it via your IP:

```bash
python app.py
# Access from other devices: http://192.168.x.x:5000
```

---

## 📁 Project Structure

```
├── app.py                 # Flask backend + API routes
├── requirements.txt       # Python dependencies
├── Procfile               # Deployment start command
├── runtime.txt            # Python version hint
├── attendance.db          # SQLite database (auto-created)
├── static/
│   └── style.css          # Premium dark glassmorphism UI
└── templates/
    ├── login.html         # Login page
    ├── dashboard.html     # Main dashboard with stats
    ├── register.html      # Student face registration
    ├── attendance.html    # Face scan & mark attendance
    └── records.html       # View/filter/export records
```

---

## 🔐 Security Notes

- Change `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `app.py` before deploying
- Set a strong `SECRET_KEY` environment variable in production
- The SQLite database is file-based — back it up regularly

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · Flask |
| AI/ML | face_recognition · dlib · OpenCV · NumPy |
| Database | SQLite 3 |
| Frontend | HTML5 · Vanilla CSS (glassmorphism) · Vanilla JS |
| Deployment | Gunicorn · Render / Railway |
