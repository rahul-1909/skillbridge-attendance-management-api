from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from .auth import hash_password
from .db import Base, SessionLocal, engine
from .models import Attendance, Batch, BatchStudent, BatchTrainer, Institution, Session as SessionModel, User


PASSWORD = "SkillBridge123!"


def _get_or_create_user(
    db: Session,
    name: str,
    email: str,
    role: str,
    institution_id: int | None,
) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(PASSWORD),
        role=role,
        institution_id=institution_id,
    )
    db.add(user)
    db.flush()
    return user


def run_seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Seed skipped: data already exists")
            return

        inst1 = Institution(name="SkillBridge North Institute")
        inst2 = Institution(name="SkillBridge South Institute")
        db.add_all([inst1, inst2])
        db.flush()

        trainers = [
            _get_or_create_user(db, "Trainer One", "trainer1@skillbridgeapp.com", "trainer", inst1.id),
            _get_or_create_user(db, "Trainer Two", "trainer2@skillbridgeapp.com", "trainer", inst1.id),
            _get_or_create_user(db, "Trainer Three", "trainer3@skillbridgeapp.com", "trainer", inst2.id),
            _get_or_create_user(db, "Trainer Four", "trainer4@skillbridgeapp.com", "trainer", inst2.id),
        ]

        institution_users = [
            _get_or_create_user(
                db,
                "Institution Admin North",
                "institution1@skillbridgeapp.com",
                "institution",
                inst1.id,
            ),
            _get_or_create_user(
                db,
                "Institution Admin South",
                "institution2@skillbridgeapp.com",
                "institution",
                inst2.id,
            ),
        ]

        _get_or_create_user(
            db,
            "Programme Manager",
            "pm@skillbridgeapp.com",
            "programme_manager",
            None,
        )
        _get_or_create_user(
            db,
            "Monitoring Officer",
            "monitor@skillbridgeapp.com",
            "monitoring_officer",
            None,
        )

        students = []
        for idx in range(1, 16):
            institution_id = inst1.id if idx <= 8 else inst2.id
            students.append(
                _get_or_create_user(
                    db,
                    f"Student {idx}",
                    f"student{idx}@skillbridgeapp.com",
                    "student",
                    institution_id,
                )
            )

        batches = [
            Batch(name="North Data Analytics", institution_id=inst1.id),
            Batch(name="North Web Development", institution_id=inst1.id),
            Batch(name="South Electrician", institution_id=inst2.id),
        ]
        db.add_all(batches)
        db.flush()

        db.add_all(
            [
                BatchTrainer(batch_id=batches[0].id, trainer_id=trainers[0].id),
                BatchTrainer(batch_id=batches[0].id, trainer_id=trainers[1].id),
                BatchTrainer(batch_id=batches[1].id, trainer_id=trainers[1].id),
                BatchTrainer(batch_id=batches[2].id, trainer_id=trainers[2].id),
            ]
        )

        for student in students[:6]:
            db.add(BatchStudent(batch_id=batches[0].id, student_id=student.id))
        for student in students[6:10]:
            db.add(BatchStudent(batch_id=batches[1].id, student_id=student.id))
        for student in students[10:]:
            db.add(BatchStudent(batch_id=batches[2].id, student_id=student.id))

        today = date.today()
        session_templates = [
            (batches[0].id, trainers[0].id, "Intro Session", -2),
            (batches[0].id, trainers[1].id, "Python Basics", -1),
            (batches[0].id, trainers[0].id, "APIs Lab", 0),
            (batches[1].id, trainers[1].id, "HTML Foundations", -1),
            (batches[1].id, trainers[1].id, "CSS Workshop", 0),
            (batches[2].id, trainers[2].id, "Electrical Safety", -2),
            (batches[2].id, trainers[2].id, "Wiring Practice", -1),
            (batches[2].id, trainers[2].id, "Assessment", 0),
        ]

        sessions: list[SessionModel] = []
        for batch_id, trainer_id, title, day_offset in session_templates:
            session = SessionModel(
                batch_id=batch_id,
                trainer_id=trainer_id,
                title=title,
                date=today + timedelta(days=day_offset),
                start_time=time(9, 0),
                end_time=time(11, 0),
            )
            db.add(session)
            db.flush()
            sessions.append(session)

        for session in sessions:
            batch_students = (
                db.query(BatchStudent)
                .filter(BatchStudent.batch_id == session.batch_id)
                .all()
            )
            for idx, bs in enumerate(batch_students):
                status = ["present", "late", "absent"][idx % 3]
                db.add(
                    Attendance(
                        session_id=session.id,
                        student_id=bs.student_id,
                        status=status,
                        marked_at=datetime.utcnow() - timedelta(hours=idx),
                    )
                )

        db.commit()
        print("Seed complete")
        print("Password for all seeded users:", PASSWORD)
        print("Institution users:", [u.email for u in institution_users])
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
