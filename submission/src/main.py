import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import (
    create_access_token,
    create_monitoring_token,
    hash_password,
    verify_password,
)
from .db import Base, engine, get_db
from .dependencies import (
    get_current_monitoring_user,
    get_current_user,
    require_roles,
)
from .models import Attendance, Batch, BatchInvite, BatchStudent, BatchTrainer, Institution, Session as SessionModel, User
from .schemas import (
    AttendanceListResponse,
    AttendanceMarkRequest,
    BatchCreate,
    BatchInviteCreate,
    BatchJoinRequest,
    BatchSummaryResponse,
    InstitutionCreate,
    InstitutionSummaryResponse,
    LoginRequest,
    MessageResponse,
    MonitoringTokenRequest,
    ProgrammeSummaryResponse,
    SessionAttendanceItem,
    SessionCreate,
    SignupRequest,
    TokenResponse,
)

load_dotenv()

MONITORING_API_KEY = os.getenv("MONITORING_API_KEY", "monitoring-dev-key")
BASE_DIR = Path(__file__).resolve().parent
IST = timezone(timedelta(hours=5, minutes=30))

app = FastAPI(title="SkillBridge Attendance API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> FileResponse:
    return FileResponse(BASE_DIR / "frontend" / "index.html")


@app.get("/app")
def frontend_app() -> FileResponse:
    return FileResponse(BASE_DIR / "frontend" / "index.html")


@app.get("/application")
def actual_application() -> FileResponse:
    return FileResponse(BASE_DIR / "frontend" / "application.html")


@app.get("/role/{role_name}")
def role_frontend(role_name: str) -> FileResponse:
    if role_name in ["trainer", "student", "institution", "programme_manager", "monitoring_officer"]:
        return FileResponse(BASE_DIR / "frontend" / "index.html")
    raise HTTPException(status_code=404, detail="Role not found")


@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    allowed_roles = {"student", "trainer", "institution", "programme_manager", "monitoring_officer"}
    if payload.role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Invalid role")

    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.role in {"student", "trainer", "institution"} and not payload.institution_id:
        raise HTTPException(status_code=422, detail="institution_id is required for this role")

    if payload.institution_id:
        institution = db.query(Institution).filter(Institution.id == payload.institution_id).first()
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
        institution_id=payload.institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token)


@app.post("/auth/monitoring-token", response_model=TokenResponse)
def create_monitoring_readonly_token(
    payload: MonitoringTokenRequest,
    current_user: User = Depends(require_roles("monitoring_officer")),
):
    if payload.key != MONITORING_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    token = create_monitoring_token(user_id=current_user.id, role=current_user.role)
    return TokenResponse(access_token=token)


@app.post("/institutions", response_model=MessageResponse)
def create_institution(
    payload: InstitutionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("programme_manager")),
):
    existing = db.query(Institution).filter(Institution.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution already exists")

    institution = Institution(name=payload.name)
    db.add(institution)
    db.commit()
    return MessageResponse(message="Institution created")


@app.post("/batches", response_model=MessageResponse)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("trainer", "institution")),
):
    institution_id = payload.institution_id
    if current_user.role in {"trainer", "institution"}:
        institution_id = current_user.institution_id

    if not institution_id:
        raise HTTPException(status_code=422, detail="institution_id required")

    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch = Batch(name=payload.name, institution_id=institution_id)
    db.add(batch)
    db.flush()

    if current_user.role == "trainer":
        db.add(BatchTrainer(batch_id=batch.id, trainer_id=current_user.id))

    db.commit()
    return MessageResponse(message=f"Batch created with id {batch.id}")


@app.post("/batches/{batch_id}/invite", response_model=MessageResponse)
def generate_invite(
    batch_id: int,
    payload: BatchInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("trainer")),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    trainer_link = (
        db.query(BatchTrainer)
        .filter(BatchTrainer.batch_id == batch_id, BatchTrainer.trainer_id == current_user.id)
        .first()
    )
    if not trainer_link:
        raise HTTPException(status_code=403, detail="Trainer is not assigned to this batch")

    invite = BatchInvite(
        batch_id=batch_id,
        token=secrets.token_urlsafe(24),
        created_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(hours=payload.expires_in_hours),
        used=False,
    )
    db.add(invite)
    db.commit()
    return MessageResponse(message=f"Invite token: {invite.token}")


@app.post("/batches/join", response_model=MessageResponse)
def join_batch(
    payload: BatchJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    invite = db.query(BatchInvite).filter(BatchInvite.token == payload.token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.used:
        raise HTTPException(status_code=403, detail="Invite already used")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invite expired")

    exists = (
        db.query(BatchStudent)
        .filter(BatchStudent.batch_id == invite.batch_id, BatchStudent.student_id == current_user.id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Student already joined this batch")

    db.add(BatchStudent(batch_id=invite.batch_id, student_id=current_user.id))
    invite.used = True
    db.commit()
    return MessageResponse(message="Joined batch successfully")


@app.post("/sessions", response_model=MessageResponse)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("trainer")),
):
    batch = db.query(Batch).filter(Batch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    trainer_link = (
        db.query(BatchTrainer)
        .filter(BatchTrainer.batch_id == payload.batch_id, BatchTrainer.trainer_id == current_user.id)
        .first()
    )
    if not trainer_link:
        raise HTTPException(status_code=403, detail="Trainer is not assigned to this batch")

    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=422, detail="end_time must be later than start_time")

    session = SessionModel(
        batch_id=payload.batch_id,
        trainer_id=current_user.id,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(session)
    db.commit()
    return MessageResponse(message=f"Session created with id {session.id}")


@app.post("/attendance/mark", response_model=MessageResponse)
def mark_attendance(
    payload: AttendanceMarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    if payload.status not in {"present", "absent", "late"}:
        raise HTTPException(status_code=422, detail="Invalid attendance status")

    session = db.query(SessionModel).filter(SessionModel.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    enrollment = (
        db.query(BatchStudent)
        .filter(BatchStudent.batch_id == session.batch_id, BatchStudent.student_id == current_user.id)
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="Student is not enrolled in this session's batch",
        )

    now = datetime.now(IST)
    current_date = now.date()
    current_time = now.time().replace(tzinfo=None)
    is_active = (
        session.date == current_date
        and session.start_time <= current_time <= session.end_time
    )
    if not is_active:
        raise HTTPException(status_code=403, detail="Session is not currently active")

    existing = (
        db.query(Attendance)
        .filter(Attendance.session_id == session.id, Attendance.student_id == current_user.id)
        .first()
    )
    if existing:
        existing.status = payload.status
        existing.marked_at = datetime.utcnow()
    else:
        db.add(
            Attendance(
                session_id=session.id,
                student_id=current_user.id,
                status=payload.status,
            )
        )

    db.commit()
    return MessageResponse(message="Attendance marked")


@app.get("/sessions/{session_id}/attendance", response_model=AttendanceListResponse)
def get_session_attendance(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("trainer")),
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Trainer cannot view this session")

    rows = (
        db.query(Attendance, User)
        .join(User, User.id == Attendance.student_id)
        .filter(Attendance.session_id == session_id)
        .all()
    )
    records = [
        SessionAttendanceItem(
            student_id=user.id,
            student_name=user.name,
            student_email=user.email,
            status=attendance.status,
            marked_at=attendance.marked_at,
        )
        for attendance, user in rows
    ]
    return AttendanceListResponse(session_id=session_id, records=records)


@app.get("/batches/{batch_id}/summary", response_model=BatchSummaryResponse)
def batch_summary(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("institution")),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Not allowed for this batch")

    total_sessions = db.query(SessionModel).filter(SessionModel.batch_id == batch_id).count()

    status_counts = (
        db.query(Attendance.status, func.count(Attendance.id))
        .join(SessionModel, SessionModel.id == Attendance.session_id)
        .filter(SessionModel.batch_id == batch_id)
        .group_by(Attendance.status)
        .all()
    )
    counts = {status_name: count for status_name, count in status_counts}

    return BatchSummaryResponse(
        batch_id=batch.id,
        batch_name=batch.name,
        total_sessions=total_sessions,
        present=counts.get("present", 0),
        absent=counts.get("absent", 0),
        late=counts.get("late", 0),
    )


@app.get("/institutions/{institution_id}/summary", response_model=InstitutionSummaryResponse)
def institution_summary(
    institution_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("programme_manager")),
):
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch_ids_query = db.query(Batch.id).filter(Batch.institution_id == institution_id)
    batch_ids = [row[0] for row in batch_ids_query.all()]

    total_batches = len(batch_ids)
    total_sessions = db.query(SessionModel).filter(SessionModel.batch_id.in_(batch_ids)).count() if batch_ids else 0
    total_students = (
        db.query(func.count(func.distinct(BatchStudent.student_id)))
        .filter(BatchStudent.batch_id.in_(batch_ids))
        .scalar()
        if batch_ids
        else 0
    )

    status_counts = (
        db.query(Attendance.status, func.count(Attendance.id))
        .join(SessionModel, SessionModel.id == Attendance.session_id)
        .filter(SessionModel.batch_id.in_(batch_ids))
        .group_by(Attendance.status)
        .all()
        if batch_ids
        else []
    )
    counts = {status_name: count for status_name, count in status_counts}

    return InstitutionSummaryResponse(
        institution_id=institution.id,
        institution_name=institution.name,
        total_batches=total_batches,
        total_sessions=total_sessions,
        total_students=total_students or 0,
        present=counts.get("present", 0),
        absent=counts.get("absent", 0),
        late=counts.get("late", 0),
    )


@app.get("/programme/summary", response_model=ProgrammeSummaryResponse)
def programme_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("programme_manager")),
):
    total_institutions = db.query(Institution).count()
    total_batches = db.query(Batch).count()
    total_sessions = db.query(SessionModel).count()
    total_students = db.query(User).filter(User.role == "student").count()

    status_counts = (
        db.query(Attendance.status, func.count(Attendance.id))
        .group_by(Attendance.status)
        .all()
    )
    counts = {status_name: count for status_name, count in status_counts}

    return ProgrammeSummaryResponse(
        total_institutions=total_institutions,
        total_batches=total_batches,
        total_sessions=total_sessions,
        total_students=total_students,
        present=counts.get("present", 0),
        absent=counts.get("absent", 0),
        late=counts.get("late", 0),
    )


@app.get("/monitoring/attendance")
def monitoring_attendance(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_monitoring_user),
):
    rows = (
        db.query(Attendance, SessionModel, User)
        .join(SessionModel, SessionModel.id == Attendance.session_id)
        .join(User, User.id == Attendance.student_id)
        .order_by(Attendance.marked_at.desc())
        .limit(200)
        .all()
    )

    records = [
        {
            "attendance_id": attendance.id,
            "session_id": session.id,
            "session_title": session.title,
            "student_id": student.id,
            "student_name": student.name,
            "status": attendance.status,
            "marked_at": attendance.marked_at.isoformat(),
        }
        for attendance, session, student in rows
    ]
    return {"count": len(records), "records": records}


@app.get("/health")
def health():
    return {"status": "ok"}
