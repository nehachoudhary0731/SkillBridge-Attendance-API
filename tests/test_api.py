import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def uid():
    return str(uuid.uuid4())[:8]


def test_student_signup_and_login(client):
    email = f"student_{uid()}@test.com"
    password = "testpass123"

    # Signup
    res = client.post("/auth/signup", json={
        "name": "Test Student",
        "email": email,
        "password": password,
        "role": "student",
    })
    assert res.status_code == 201, res.text
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "student"

    # Login
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert len(data["access_token"].split(".")) == 3  


def test_trainer_creates_session(client):
    from src.db.models import Institution, Batch, BatchTrainer

    trainer_email = f"trainer_{uid()}@test.com"

    res = client.post("/auth/signup", json={
        "name": "Test Trainer",
        "email": trainer_email,
        "password": "trainerpass",
        "role": "trainer",
    })
    assert res.status_code == 201
    trainer_token = res.json()["access_token"]
    trainer_id = res.json()["user_id"]

    db = TestingSessionLocal()
    inst = Institution(name=f"Inst {uid()}")
    db.add(inst)
    db.flush()
    batch = Batch(name=f"Batch {uid()}", institution_id=inst.id)
    db.add(batch)
    db.flush()
    db.add(BatchTrainer(batch_id=batch.id, trainer_id=trainer_id))
    db.commit()
    batch_id = batch.id
    db.close()

    res = client.post("/sessions", json={
        "title": "Intro to Python",
        "date": "2025-08-01",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "batch_id": batch_id,
    }, headers={"Authorization": f"Bearer {trainer_token}"})
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["title"] == "Intro to Python"
    assert data["batch_id"] == batch_id


def test_student_marks_attendance(client):
    from src.db.models import Institution, Batch, BatchTrainer, BatchStudent, Session
    from datetime import date, time

    student_email = f"stu_{uid()}@test.com"
    trainer_email = f"trn_{uid()}@test.com"

    res = client.post("/auth/signup", json={
        "name": "Attending Student",
        "email": student_email,
        "password": "pass123",
        "role": "student",
    })
    assert res.status_code == 201
    student_token = res.json()["access_token"]
    student_id = res.json()["user_id"]

    res = client.post("/auth/signup", json={
        "name": "Session Trainer",
        "email": trainer_email,
        "password": "pass123",
        "role": "trainer",
    })
    assert res.status_code == 201
    trainer_id = res.json()["user_id"]

    db = TestingSessionLocal()
    inst = Institution(name=f"Inst {uid()}")
    db.add(inst)
    db.flush()
    batch = Batch(name=f"Batch {uid()}", institution_id=inst.id)
    db.add(batch)
    db.flush()
    db.add(BatchTrainer(batch_id=batch.id, trainer_id=trainer_id))
    db.add(BatchStudent(batch_id=batch.id, student_id=student_id))
    db.flush()
    sess = Session(
        batch_id=batch.id,
        trainer_id=trainer_id,
        title="Test Session",
        date=date(2025, 8, 1),
        start_time=time(9, 0, 0),
        end_time=time(11, 0, 0),
    )
    db.add(sess)
    db.commit()
    session_id = sess.id
    db.close()

    res = client.post("/attendance/mark", json={
        "session_id": session_id,
        "status": "present",
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "present"
    assert data["student_id"] == student_id


def test_monitoring_post_returns_405(client):
    res = client.post("/monitoring/attendance", json={})
    assert res.status_code == 405, res.text


def test_no_token_returns_401(client):
    res = client.get("/monitoring/attendance")
    assert res.status_code in [401, 403], res.text

    res = client.post("/sessions", json={
        "title": "x",
        "date": "2025-01-01",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "batch_id": "fakeid",
    })
    assert res.status_code in [401, 403], res.text