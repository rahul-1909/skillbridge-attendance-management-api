# SkillBridge Attendance API

## 1. Live Server & Deployment Notes
I deployed the app on Render. You can check it out here:
- **Live server UI:** [https://skillbridge-attendance-management-api.onrender.com/application#](https://skillbridge-attendance-management-api.onrender.com/application#)
- **Live server API testing UI:** [https://skillbridge-attendance-management-api.onrender.com/](https://skillbridge-attendance-management-api.onrender.com/)


## 2. Local Setup Instructions
If you want to run this locally from scratch (assuming you already have Python and pip installed):

```bash
# Clone or navigate to the project directory
cd submission

# Create a virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
copy .env.example .env

# Run the seed script to populate the DB
python src/seed.py

# Start the server
uvicorn src.main:app --reload
```
Once it's running, you can hit `http://127.0.0.1:8000/application` for the app.

## 3. Test Accounts

**Password for all of them:** `SkillBridge123!`

- **Trainer:** `trainer1@skillbridgeapp.com`
- **Student:** `student1@skillbridgeapp.com`
- **Institution:** `institution1@skillbridgeapp.com`
- **Programme Manager:** `pm@skillbridgeapp.com`
- **Monitoring Officer:** `monitor@skillbridgeapp.com`

## Maintain this userflow for best experience
## Login as a trainer
--> Create a Batch by entering a name under create batch tab
--> You will get a batch id after creating the batch, this will be used in the next tab
--> Enter the batch id to generate a token to share with students (copy this token and keep it handy to test student flow)
--> Schedule a session by entering all necessary details
--> Enter session id in the session attendance tab to load attendace of all students

## Login as a Student
--> Under join batch tab enter the batch token copied from trainer login
--> Under mark attendance enter session id which is currently active and mark our attendance (can be tested again with trainer login for that specific session)

## Login as a Institution
--> Can create batches like a trainer and also view batch reports by entering batch id

## Login as a Program Manager
--> Analytics on institution specific, global analytics views

## Login as a Monitoring Officer
--> Authorize a special token from .env file and view Live data feed



## 4. Sample CURL Commands

**Auth - Login (Get Access Token)**
```cmd
curl -X POST "http://127.0.0.1:8000/auth/login" -H "Content-Type: application/json" -d "{\"email\": \"student1@skillbridgeapp.com\", \"password\": \"SkillBridge123!\"}"
```

**Get Monitoring Scoped Token (Requires Monitoring Officer Login Token)**
```cmd
# First get the normal token for monitor@skillbridgeapp.com, then:
curl -X POST "http://127.0.0.1:8000/auth/monitoring-token" -H "Authorization: Bearer YOUR_MONITOR_LOGIN_TOKEN" -H "Content-Type: application/json" -d "{\"key\": \"monitoring-dev-key\"}"
```

**Institutions - Create (Programme Manager only)**
```cmd
curl -X POST "http://127.0.0.1:8000/institutions" -H "Authorization: Bearer YOUR_PM_TOKEN" -H "Content-Type: application/json" -d "{\"name\": \"New Institution\"}"
```

**Batches - Create (Trainer/Institution)**
```cmd
curl -X POST "http://127.0.0.1:8000/batches" -H "Authorization: Bearer YOUR_TRAINER_TOKEN" -H "Content-Type: application/json" -d "{\"name\": \"Morning Batch\"}"
```

**Batches - Generate Invite (Trainer only)**
```cmd
curl -X POST "http://127.0.0.1:8000/batches/1/invite" -H "Authorization: Bearer YOUR_TRAINER_TOKEN" -H "Content-Type: application/json" -d "{\"expires_in_hours\": 24}"
```

**Batches - Join (Student)**
```cmd
curl -X POST "http://127.0.0.1:8000/batches/join" -H "Authorization: Bearer YOUR_STUDENT_TOKEN" -H "Content-Type: application/json" -d "{\"token\": \"INVITE_TOKEN_HERE\"}"
```

**Sessions - create (trainer)**
```cmd
curl -X POST "http://127.0.0.1:8000/sessions" -H "Authorization: Bearer YOUR_TRAINER_TOKEN" -H "Content-Type: application/json" -d "{\"batch_id\": 1, \"title\": \"Python Basics\", \"date\": \"2026-04-25\", \"start_time\": \"10:00:00\", \"end_time\": \"12:00:00\"}"
```

**Attendance - mark (student)**
```cmd
curl -X POST "http://127.0.0.1:8000/attendance/mark" -H "Authorization: Bearer YOUR_STUDENT_TOKEN" -H "Content-Type: application/json" -d "{\"session_id\": 1, \"status\": \"present\"}"
```

**Summaries (Programme Manager)**
```cmd
curl -X GET "http://127.0.0.1:8000/programme/summary" -H "Authorization: Bearer YOUR_PM_TOKEN"
```

**Monitoring Endpoint (Monitoring Officer - Scoped Token ONLY)**
```cmd
curl -X GET "http://127.0.0.1:8000/monitoring/attendance" -H "Authorization: Bearer YOUR_SCOPED_MONITORING_TOKEN"
```

## 5. Schema Decisions
A few notes on how i modeled the database:
- **`batch_trainers`**: I used an explicit many-to-many relationship here so a single batch can have multiple trainers assigned to it.
- **`batch_invites`**: I created a tokenized invite system. The tokens have an `expires_at` timestamp and a `used` boolean flag. This prevents replay attacks and controls enrollment timeframes.
- **Dual-token approach for Monitoring Officer**: Instead of just using one token for everything, the Monitoring Officer logs in to get a standard JWT, and then hits a specific endpoint to exchange it for a short-lived scoped token. The `/monitoring/attendance` route strictly validates `typ=monitoring` and `scope=monitoring_read`.

## 6. What's working / Partial / Skipped
**Everything is comepletely done.** 
The auth, RBAC, endpoints, batch management, invite workflow, dual-token system, and even the frontend are fully functional. I didn't skip any of the core requirements or leave anything partially done. The test suite is also fully working.

## 7. What I'd do differently with more time
Honestly, I'd build a **better UI and improve the project flow between user roles**. 
Right now, it works, but the UX is not great. With more time, I would create a smoother, more polished frontend experience so that moving between logging in, generating invites, and marking attendance feels more intuitive. Also maybe some better error messages on the frontend.
