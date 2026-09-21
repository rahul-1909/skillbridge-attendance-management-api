# SkillBridge Attendance Management API

A modern, role-based educational attendance and training cohort management system built with **FastAPI**, **SQLAlchemy**, and **Pydantic**. Features multi-tenant batch management, secure single-use invite tokens, strict Indian Standard Time (IST) attendance window validation, dual-token scoped telemetry for monitoring officers, and a sleek, modern, minimal web dashboard.

---

## 🚀 Live Server & Deployment

- **Main Application Dashboard:** [https://skillbridge-attendance-management-api.onrender.com/](https://skillbridge-attendance-management-api.onrender.com/)
- **Interactive REST API Documentation (Swagger):** [https://skillbridge-attendance-management-api.onrender.com/docs](https://skillbridge-attendance-management-api.onrender.com/docs)
- **Health Check Endpoint:** [https://skillbridge-attendance-management-api.onrender.com/health](https://skillbridge-attendance-management-api.onrender.com/health)

---

## ✨ What's New in This Version

- **Modern Minimalist Frontend:** Completely redesigned dark/slate glassmorphism interface featuring responsive layouts, micro-interactions, and KPI metric cards.
- **1-Click Quick Demo Login:** Instant one-click persona switcher on the login screen to test Trainer, Student, Institution, PM, and Monitoring Officer flows without manually entering credentials.
- **Real-Time Live IST Clock:** Synchronized with Indian Standard Time (`UTC+05:30`) to visually confirm whether session attendance windows are currently active.
- **Built-in Developer API Console:** Live slide-over inspector displaying outgoing requests, headers, and formatted JSON responses.
- **Automated Zero-Config Seeding (`AUTO_SEED=true`):** Newly deployed environments automatically populate test institutions, accounts, batches, and sessions on first boot.
- **Dual-Root Deployment Compatibility:** Works out-of-the-box whether your cloud platform points to the repository root or the `submission/` directory (`render.yaml`, `Dockerfile`, `Procfile`, and root proxy `main.py` included).

---

## 👥 Seeded Test Accounts

> **Universal Password:** `SkillBridge123!`

| Role | Email | Capabilities |
| :--- | :--- | :--- |
| **Trainer** | `trainer1@skillbridgeapp.com` | Create batches, generate single-use invite tokens, schedule training sessions, inspect session rosters |
| **Student** | `student1@skillbridgeapp.com` | Join batches via invite tokens, record session attendance within active IST windows |
| **Institution** | `institution1@skillbridgeapp.com` | Create institutional cohorts, view aggregated batch attendance analytics |
| **Programme Manager** | `pm@skillbridgeapp.com` | Register new institutions, view global programme & institution telemetry |
| **Monitoring Officer** | `monitor@skillbridgeapp.com` | Exchange secret key for short-lived scoped token, stream live global attendance feed |

---

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.10+
- `pip` package manager

### Steps
```bash
# 1. Clone repository and navigate to submission directory
cd submission

# 2. Create and activate a virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Start the local server (auto-seeds database on first launch)
uvicorn src.main:app --reload --port 8000
```

Open your browser at `http://localhost:8000/` to explore the dashboard or `http://localhost:8000/docs` for the interactive Swagger UI.

---

## ☁️ Deploying to Render (or Cloud PaaS)

### Option A: Render Blueprint (Recommended - 1 Click)
1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** → **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](render.yaml) and configure:
   - **Build Command:** `pip install -r submission/requirements.txt`
   - **Start Command:** `uvicorn submission.src.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** `PYTHON_VERSION=3.11.9`, `AUTO_SEED=true`, `MONITORING_API_KEY=monitoring-dev-key`
4. Click **Apply**. Your app will build, auto-seed the demo database, and go live!

### Option B: Manual Web Service Setup on Render
If configuring manually as a **Web Service**:
- **Environment:** `Python`
- **Build Command:** `pip install -r submission/requirements.txt` (or set Root Directory to `submission` and use `pip install -r requirements.txt`)
- **Start Command:** `uvicorn submission.src.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:**
  - `PYTHON_VERSION`: `3.11.9`
  - `AUTO_SEED`: `true`
  - `MONITORING_API_KEY`: `monitoring-dev-key`
  - `JWT_SECRET`: Any secure random string

### Option C: Docker Deployment
A production-ready [`Dockerfile`](Dockerfile) is included. You can deploy to any container platform (Railway, Fly.io, Render Docker, or AWS ECS):
```bash
docker build -t skillbridge-api .
docker run -p 8000:8000 -e AUTO_SEED=true skillbridge-api
```

---

## 🧪 Testing

Run the integration test suite with `pytest`:
```bash
cd submission
pytest tests/test_api.py -v
```

The test suite covers:
- User signup and login JWT issuance
- Trainer batch & session creation
- Student enrollment via invite tokens
- IST session attendance marking window boundaries
- Role-based authorization and HTTP 401/403/405 protection

---

## 📡 Core API Endpoints

### Authentication
- `POST /auth/signup` - Register a new user (`student`, `trainer`, `institution`, `programme_manager`, `monitoring_officer`)
- `POST /auth/login` - Authenticate and receive standard Bearer access token
- `POST /auth/monitoring-token` - Exchange secret API key for scoped monitoring token (`typ=monitoring`, `scope=monitoring_read`)

### Batches & Sessions
- `POST /batches` - Create a new cohort batch (Trainers & Institutions)
- `POST /batches/{id}/invite` - Generate a time-limited, single-use invite token (Trainers)
- `POST /batches/join` - Redeem an invite token to enroll in a batch (Students)
- `POST /sessions` - Schedule a classroom training session (Trainers)
- `GET /sessions/{id}/attendance` - Retrieve student attendance list for a session (Trainers)

### Attendance & Analytics
- `POST /attendance/mark` - Mark attendance (`present`, `late`, `absent`) within the active IST session window (Students)
- `GET /batches/{id}/summary` - View session counts and attendance summary (Institutions)
- `GET /programme/summary` - View platform-wide global attendance metrics (Programme Managers)
- `GET /institutions/{id}/summary` - View institution performance metrics (Programme Managers)
- `GET /monitoring/attendance` - Stream live attendance telemetry feed (Monitoring Officers with scoped token)
