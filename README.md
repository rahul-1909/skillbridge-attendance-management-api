# SkillBridge Attendance Management API

A production-ready, multi-tenant educational attendance and cohort management API built with **FastAPI**, **SQLAlchemy**, and **Pydantic**. Engineered for vocational institutions and training programs to manage batches, schedule classroom sessions, issue single-use secure invite tokens, enforce strict Indian Standard Time (IST) attendance windows, and stream live telemetry via dual-token authentication.

---

## 🌐 Live Service & Documentation

- **Live Application:** [https://skillbridge-attendance-management-api.onrender.com/](https://skillbridge-attendance-management-api.onrender.com/)
- **Interactive Swagger Documentation:** [https://skillbridge-attendance-management-api.onrender.com/docs](https://skillbridge-attendance-management-api.onrender.com/docs)
- **Health Check Endpoint:** [https://skillbridge-attendance-management-api.onrender.com/health](https://skillbridge-attendance-management-api.onrender.com/health)

---

## 🏛️ System Architecture

```
+---------------------------------------------------------------------------------------+
|                                    CLIENT LAYER                                       |
|  - Minimalist Web Dashboard (SPA)             - API Clients / Swagger UI / cURL       |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | HTTP (JSON / Bearer Token)
                                            v
+---------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION LAYER                               |
|  - Uvicorn ASGI Server (CORS Middleware, Route Dispatcher, Global Exception Handlers) |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                             SECURITY & AUTHENTICATION LAYER                           |
|  - Password Hashing (PBKDF2-SHA256)                                                   |
|  - Standard JWT Access Token (typ="access", 24h lifetime)                             |
|  - Scoped Telemetry Token for Monitoring Officers (typ="monitoring", scope="read")   |
|  - Role-Based Access Control (RBAC): Student, Trainer, Institution, PM, Monitor       |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                                  BUSINESS LOGIC CORE                                  |
|  +--------------------+  +----------------------+  +--------------------------------+ |
|  | Batch & Invites    |  | Sessions Engine      |  | Attendance Engine              | |
|  | - Single-Use Token |  | - Date & Time Window |  | - Strict IST Active Window     | |
|  | - Expiration Check |  | - Trainer Assignment |  | - Upsert Attendance Record     | |
|  +--------------------+  +----------------------+  +--------------------------------+ |
|  +----------------------------------------------------------------------------------+ |
|  | Analytics & Reporting Engine (Batch Summaries, Institution & Global Telemetry)  | |
|  +----------------------------------------------------------------------------------+ |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                                DATA ACCESS LAYER (ORM)                                |
|  - SQLAlchemy 2.0 (Declarative Models, Relationships, Constraints, Auto-Seeding)      |
+-------------------------------------------+-------------------------------------------+
                                            |
                         +------------------+------------------+
                         |                                     |
                         v                                     v
           +---------------------------+         +---------------------------+
           | PostgreSQL (Render Cloud) |         | SQLite (Local / Pytest)   |
           +---------------------------+         +---------------------------+
```

---

## 🔑 Core Features & Architectural Decisions

### 1. Dual-Token Architecture for Monitoring
Instead of granting broad administrative access with a single JWT, **Monitoring Officers** use a two-step scoped credential exchange:
1. Log in via `/auth/login` to obtain an identity token.
2. Call `POST /auth/monitoring-token` with the secure system key (`MONITORING_API_KEY`) to receive a short-lived (1-hour) scoped token.
3. The live telemetry route (`GET /monitoring/attendance`) strictly validates `typ="monitoring"` and `scope="monitoring_read"`.

### 2. Timezone-Aware Attendance Engine (IST)
Vocational training sessions operate on fixed physical schedule windows. When a student marks attendance:
- Server checks the live clock converted to **Indian Standard Time (IST, UTC+05:30)**.
- Rejects attendance submission with `403 Session is not currently active` if the request is made before `start_time` or after `end_time`.
- Enforces batch enrollment checks to prevent unauthorized submissions.

### 3. Single-Use Invite Token System
- Trainers generate URL-safe invite tokens (`secrets.token_urlsafe(24)`) with configurable expiration (`expires_in_hours`).
- Tokens have an `expires_at` timestamp and a `used` boolean flag in the database.
- Once a student redeems a token via `/batches/join`, it is immediately flagged as `used = True` to prevent replay attacks.

### 4. Automated Zero-Config Seeding (`AUTO_SEED=true`)
When newly deployed to a cloud environment (e.g., Render, Railway, Fly.io), the application verifies whether the database contains user accounts. If empty, it safely seeds demo institutions, batches, trainers, students, sessions, and records on first boot.

---

## 👥 Seeded Test Accounts

> **Universal Password:** `SkillBridge123!`

| Role | Email | Scope & Permissions |
| :--- | :--- | :--- |
| **Trainer** | `trainer1@skillbridgeapp.com` | Create batches, generate invite tokens, schedule sessions, view session attendance |
| **Student** | `student1@skillbridgeapp.com` | Join batches using tokens, submit attendance during active session window |
| **Institution** | `institution1@skillbridgeapp.com` | Create institutional cohorts, view aggregated batch performance summaries |
| **Programme Manager** | `pm@skillbridgeapp.com` | Register new institutions, view global programme & institution analytics |
| **Monitoring Officer** | `monitor@skillbridgeapp.com` | Authorize secret key for scoped token, monitor real-time global telemetry feed |

---

## 🛠️ Tech Stack & Dependencies

- **Language & Runtime:** Python 3.10+
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (0.116+)
- **ASGI Web Server:** [Uvicorn](https://www.uvicorn.org/) (0.35+)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) 2.0
- **Database:** PostgreSQL (Cloud) / SQLite (Local & Testing)
- **Token Management:** `python-jose` (HS256 JWT)
- **Password Security:** `passlib` with `pbkdf2_sha256`
- **Validation:** Pydantic v2 & `email-validator`
- **Testing:** `pytest` & `httpx`
- **Frontend:** Clean Minimalist Vanilla JS / CSS Single Page Application

---

## 📂 Project Directory Structure

```
skillbridge-attendance-management-api/
├── main.py                        # Root proxy entrypoint for cloud hosting
├── requirements.txt               # Root dependency specification
├── render.yaml                    # Render Blueprint configuration
├── Dockerfile                     # Container definition for Docker/Railway/Fly.io
├── Procfile                       # Process manager definition
├── .env.example                   # Environment variable template
├── README.md                      # Complete system documentation
└── submission/
    ├── requirements.txt           # Pinned production requirements
    ├── render.yaml                # Sub-directory Render blueprint
    ├── Procfile                   # Sub-directory process definition
    ├── .env.example
    ├── src/
    │   ├── db.py                  # Database engine, connection pooling, session generator
    │   ├── models.py              # SQLAlchemy DB models & relational constraints
    │   ├── schemas.py             # Pydantic request/response validation schemas
    │   ├── auth.py                # Password hashing and JWT generation
    │   ├── dependencies.py        # RBAC dependencies & token validation
    │   ├── seed.py                # Idempotent database population script
    │   ├── main.py                # FastAPI app, routing, CORS, and startup hooks
    │   └── frontend/
    │       └── application.html   # Clean, neat, minimalist web dashboard
    └── tests/
        ├── conftest.py            # Test database fixture & test harness
        └── test_api.py            # Complete integration test suite
```

---

## 💻 Local Development Setup

### 1. Clone & Setup Virtual Environment
```bash
# Navigate to the project directory
cd submission

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

### 3. Run Application
```bash
uvicorn src.main:app --reload --port 8000
```
Open **`http://localhost:8000/`** to view the clean web interface or **`http://localhost:8000/docs`** for the Swagger API documentation.

---

## 🧪 Automated Testing

Execute the test suite using `pytest`:
```bash
cd submission
pytest tests/test_api.py -v
```

### Test Coverage Highlights:
- ✅ Student registration, authentication, and JWT issuance
- ✅ Trainer batch creation and classroom session scheduling
- ✅ Single-use invite token generation and student enrollment
- ✅ Timezone validation (IST active window attendance marking)
- ✅ Scoped telemetry token enforcement and HTTP 401/403/405 checks

---

## 📡 Complete API Reference

### Authentication
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/signup` | Public | Register user (`student`, `trainer`, `institution`, `programme_manager`, `monitoring_officer`) |
| `POST` | `/auth/login` | Public | Authenticate user and receive Bearer access token |
| `POST` | `/auth/monitoring-token` | Monitoring Officer | Exchange API key for scoped telemetry token |

### Batches & Invites
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/batches` | Trainer / Institution | Create a new batch cohort |
| `POST` | `/batches/{id}/invite` | Trainer | Generate a single-use invite token |
| `POST` | `/batches/join` | Student | Join batch using invite token |
| `GET` | `/batches/{id}/summary` | Institution | Retrieve session and attendance breakdown |

### Sessions & Attendance
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/sessions` | Trainer | Schedule classroom training session |
| `GET` | `/sessions/{id}/attendance` | Trainer | View student attendance records for session |
| `POST` | `/attendance/mark` | Student | Mark attendance (`present`, `late`, `absent`) within active IST window |

### Management & Monitoring
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/institutions` | Programme Manager | Register a new vocational institute |
| `GET` | `/institutions/{id}/summary` | Programme Manager | Retrieve metrics for an institution |
| `GET` | `/programme/summary` | Programme Manager | Retrieve platform-wide global telemetry |
| `GET` | `/monitoring/attendance` | Monitoring Officer | Stream latest 200 real-time attendance events |
| `GET` | `/time` | Public | Get server Indian Standard Time (IST) clock |
| `GET` | `/health` | Public | Service health verification |

---

## ☁️ Deployment Guide

### Deploy to Render via Blueprint (1-Click)
1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** → **Blueprint**.
3. Select your repository. Render will automatically read `render.yaml` and set:
   - **Build Command:** `pip install -r submission/requirements.txt`
   - **Start Command:** `uvicorn submission.src.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** `PYTHON_VERSION=3.11.9`, `AUTO_SEED=true`, `MONITORING_API_KEY=monitoring-dev-key`
4. Click **Apply**.
