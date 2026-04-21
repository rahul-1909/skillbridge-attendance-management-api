# SkillBridge Attendance API

A FastAPI + PostgreSQL backend for the SkillBridge prototype attendance system with:
- role-based access control on protected endpoints
- JWT authentication for all users
- additional short-lived scoped token flow for Monitoring Officer
- seed data + pytest suite
- minimal frontend served by the backend

## 1) Live API Base URL and Deployment Notes
- Live base URL: **Not deployed yet from this environment**
- Deployment status: Partial (code is deployment-ready; actual cloud deployment needs your Railway/Render/Fly and Neon credentials)
- What was attempted here: local build and test setup only
- Where deployment is blocked here: no access to your cloud accounts/secrets from this workspace session

Suggested deployment:
1. Create a Neon PostgreSQL database.
2. Deploy this repo to Railway/Render/Fly.
3. Configure environment variables from `.env.example`.
4. Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

## 2) Local Setup Instructions (From Scratch)

```bash
cd submission
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
# edit .env values

python -m src.seed
uvicorn src.main:app --reload
```

Open:
- API docs: `http://127.0.0.1:8000/docs`
- Frontend landing page: `http://127.0.0.1:8000/`
- Functional frontend app: `http://127.0.0.1:8000/app`

## 3) Seeded Test Accounts (All Roles)
Seed password for all accounts: `SkillBridge123!`

- Student: `student1@skillbridgeapp.com`
- Trainer: `trainer1@skillbridgeapp.com`
- Institution: `institution1@skillbridgeapp.com`
- Programme Manager: `pm@skillbridgeapp.com`
- Monitoring Officer: `monitor@skillbridgeapp.com`

## 4) Sample curl Commands for Every Endpoint
Base URL:

```bash
BASE_URL=http://127.0.0.1:8000
```

### Auth

Signup:
```bash
curl -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"name":"New Student","email":"newstudent@example.com","password":"Pass1234!","role":"student","institution_id":1}'
```

Login:
```bash
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"student1@skillbridgeapp.com","password":"SkillBridge123!"}'
```

Monitoring scoped token (requires Monitoring Officer login token):
```bash
MONITOR_LOGIN_TOKEN=<monitoring_officer_access_token>
curl -X POST "$BASE_URL/auth/monitoring-token" \
  -H "Authorization: Bearer $MONITOR_LOGIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key":"replace-with-monitoring-api-key"}'
```

### Institutions

Create institution (programme_manager only):
```bash
PM_TOKEN=<programme_manager_access_token>
curl -X POST "$BASE_URL/institutions" \
  -H "Authorization: Bearer $PM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"SkillBridge East"}'
```

### Batches

Create batch (trainer or institution):
```bash
TRAINER_TOKEN=<trainer_access_token>
curl -X POST "$BASE_URL/batches" \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Batch A"}'
```

Generate invite (trainer only):
```bash
curl -X POST "$BASE_URL/batches/1/invite" \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expires_in_hours":24}'
```

Join batch (student):
```bash
STUDENT_TOKEN=<student_access_token>
INVITE_TOKEN=<invite_token>
curl -X POST "$BASE_URL/batches/join" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$INVITE_TOKEN\"}"
```

Batch summary (institution only):
```bash
INSTITUTION_TOKEN=<institution_access_token>
curl -X GET "$BASE_URL/batches/1/summary" \
  -H "Authorization: Bearer $INSTITUTION_TOKEN"
```

### Sessions and Attendance

Create session (trainer):
```bash
curl -X POST "$BASE_URL/sessions" \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"batch_id":1,"title":"Session X","date":"2026-04-21","start_time":"09:00:00","end_time":"11:00:00"}'
```

Mark attendance (student):
```bash
curl -X POST "$BASE_URL/attendance/mark" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":1,"status":"present"}'
```

Session attendance list (trainer):
```bash
curl -X GET "$BASE_URL/sessions/1/attendance" \
  -H "Authorization: Bearer $TRAINER_TOKEN"
```

### Programme-level Summaries

Institution summary (programme_manager):
```bash
curl -X GET "$BASE_URL/institutions/1/summary" \
  -H "Authorization: Bearer $PM_TOKEN"
```

Programme summary (programme_manager):
```bash
curl -X GET "$BASE_URL/programme/summary" \
  -H "Authorization: Bearer $PM_TOKEN"
```

### Monitoring Endpoint (scoped token only)

```bash
MONITOR_SCOPED_TOKEN=<monitoring_scoped_token>
curl -X GET "$BASE_URL/monitoring/attendance" \
  -H "Authorization: Bearer $MONITOR_SCOPED_TOKEN"
```

POST must return 405:
```bash
curl -X POST "$BASE_URL/monitoring/attendance"
```

## 5) Schema Decisions

- `batch_trainers`: explicit many-to-many table so a batch can have multiple trainers and authorization can validate assignment per batch.
- `batch_invites`: tokenized join workflow with `expires_at` + `used` to control enrollment and prevent invite replay.
- Dual-token approach for Monitoring Officer:
  - normal access token from `/auth/login`
  - extra short-lived, scoped token from `/auth/monitoring-token`
  - `/monitoring/attendance` accepts only scoped monitoring token (`typ=monitoring`, `scope=monitoring_read`)

## JWT Payload Structures

Standard access token (`/auth/signup`, `/auth/login`):
```json
{
  "user_id": 12,
  "role": "trainer",
  "iat": 1713690000,
  "exp": 1713776400,
  "typ": "access"
}
```

Monitoring scoped token (`/auth/monitoring-token`):
```json
{
  "user_id": 20,
  "role": "monitoring_officer",
  "scope": "monitoring_read",
  "iat": 1713690000,
  "exp": 1713693600,
  "typ": "monitoring"
}
```

## Token Rotation and Revocation (Production Approach)

- Rotate `JWT_SECRET` periodically via secret manager.
- Add `jti` claim + token blacklist/allowlist in Redis for revocation.
- Use short expiries and refresh-token rotation.
- Track compromised accounts and revoke all active sessions.

## 6) Working vs Partial vs Skipped

Fully working locally:
- auth signup/login
- monitoring scoped token flow
- RBAC on protected endpoints
- batch/session/attendance operations
- summary endpoints
- seed script with required sample scale
- pytest suite with five required tests
- minimal frontend for quick login + summary check

Partially done:
- cloud deployment documentation is ready, but live URL is not provided because deployment could not be executed in this environment

Skipped:
- advanced region model for Programme Manager (current implementation is programme-wide)

## 7) One Thing I Would Do Differently With More Time

- Move from single access token to full access+refresh token lifecycle with revocation list and audit trails for all privileged operations.

## Security Note

Current known issue:
- No rate-limiting or account lockout on `/auth/login`, making brute-force attempts possible.

Fix with more time:
- Add IP/user-based rate-limiting (e.g., Redis-backed), temporary account lockouts, and structured auth event logging.

## Running Tests

```bash
cd submission
pytest -q
```

At least two tests hit a real SQLite test database (not mocked).
