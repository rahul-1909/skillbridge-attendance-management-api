from datetime import date, datetime, timedelta, timezone

import src.main as main_module


def create_institution_and_users(client):
    pm_signup = client.post(
        "/auth/signup",
        json={
            "name": "PM User",
            "email": "pm@test.com",
            "password": "Pass1234!",
            "role": "programme_manager",
        },
    )
    pm_token = pm_signup.json()["access_token"]

    create_inst = client.post(
        "/institutions",
        json={"name": "Alpha Institute"},
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert create_inst.status_code == 200

    trainer_signup = client.post(
        "/auth/signup",
        json={
            "name": "Trainer A",
            "email": "trainer@test.com",
            "password": "Pass1234!",
            "role": "trainer",
            "institution_id": 1,
        },
    )
    student_signup = client.post(
        "/auth/signup",
        json={
            "name": "Student A",
            "email": "student@test.com",
            "password": "Pass1234!",
            "role": "student",
            "institution_id": 1,
        },
    )

    return trainer_signup.json()["access_token"], student_signup.json()["access_token"]


def test_student_signup_and_login_returns_jwt(client):
    pm_signup = client.post(
        "/auth/signup",
        json={
            "name": "PM",
            "email": "pm1@test.com",
            "password": "Pass1234!",
            "role": "programme_manager",
        },
    )
    pm_token = pm_signup.json()["access_token"]

    client.post(
        "/institutions",
        json={"name": "Inst One"},
        headers={"Authorization": f"Bearer {pm_token}"},
    )

    signup_resp = client.post(
        "/auth/signup",
        json={
            "name": "Student One",
            "email": "student1@test.com",
            "password": "Pass1234!",
            "role": "student",
            "institution_id": 1,
        },
    )
    assert signup_resp.status_code == 200
    assert "access_token" in signup_resp.json()

    login_resp = client.post(
        "/auth/login",
        json={"email": "student1@test.com", "password": "Pass1234!"},
    )
    assert login_resp.status_code == 200
    assert isinstance(login_resp.json()["access_token"], str)


def test_trainer_can_create_session(client):
    trainer_token, _ = create_institution_and_users(client)

    batch_resp = client.post(
        "/batches",
        json={"name": "Batch One"},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert batch_resp.status_code == 200

    now = datetime.now()
    session_resp = client.post(
        "/sessions",
        json={
            "batch_id": 1,
            "title": "Session 1",
            "date": str(date.today()),
            "start_time": (now - timedelta(minutes=15)).strftime("%H:%M:%S"),
            "end_time": (now + timedelta(minutes=45)).strftime("%H:%M:%S"),
        },
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert session_resp.status_code == 200


def test_student_can_mark_own_attendance(client):
    trainer_token, student_token = create_institution_and_users(client)

    client.post(
        "/batches",
        json={"name": "Batch Two"},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )

    invite_resp = client.post(
        "/batches/1/invite",
        json={"expires_in_hours": 2},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    invite_token = invite_resp.json()["message"].split(": ", 1)[1]

    join_resp = client.post(
        "/batches/join",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert join_resp.status_code == 200

    now = datetime.now()
    client.post(
        "/sessions",
        json={
            "batch_id": 1,
            "title": "Live Session",
            "date": str(date.today()),
            "start_time": (now - timedelta(minutes=10)).strftime("%H:%M:%S"),
            "end_time": (now + timedelta(minutes=50)).strftime("%H:%M:%S"),
        },
        headers={"Authorization": f"Bearer {trainer_token}"},
    )

    mark_resp = client.post(
        "/attendance/mark",
        json={"session_id": 1, "status": "present"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert mark_resp.status_code == 200


def test_student_can_mark_attendance_in_ist_window(client, monkeypatch):
    trainer_token, student_token = create_institution_and_users(client)

    client.post(
        "/batches",
        json={"name": "Batch IST"},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )

    invite_resp = client.post(
        "/batches/1/invite",
        json={"expires_in_hours": 2},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    invite_token = invite_resp.json()["message"].split(": ", 1)[1]

    join_resp = client.post(
        "/batches/join",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert join_resp.status_code == 200

    client.post(
        "/sessions",
        json={
            "batch_id": 1,
            "title": "IST Session",
            "date": "2026-04-22",
            "start_time": "10:00:00",
            "end_time": "11:00:00",
        },
        headers={"Authorization": f"Bearer {trainer_token}"},
    )

    ist = timezone(timedelta(hours=5, minutes=30))
    ist_now = datetime(2026, 4, 22, 10, 30, 0, tzinfo=ist)

    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return ist_now.astimezone(tz)
            return ist_now.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return ist_now.astimezone(timezone.utc).replace(tzinfo=None)

    monkeypatch.setattr(main_module, "datetime", FakeDateTime)

    mark_resp = client.post(
        "/attendance/mark",
        json={"session_id": 1, "status": "present"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert mark_resp.status_code == 200


def test_post_monitoring_attendance_returns_405(client):
    resp = client.post("/monitoring/attendance")
    assert resp.status_code == 405


def test_protected_endpoint_without_token_returns_401(client):
    resp = client.post("/batches", json={"name": "Denied Batch"})
    assert resp.status_code == 401
