"""
Seed script: creates realistic test data for SkillBridge API.
Run with: python -m src.seed
"""
from src.db.connect_to_db import SessionLocal, engine
from src.db.models import Base, User, Institution, Batch, BatchTrainer, BatchStudent, BatchInvite, Session, Attendance, RoleEnum, AttendanceStatus
from src.auth.security import hash_password
from datetime import datetime, timedelta
import uuid

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def run():
    print("🌱 Seeding database...")

    inst1 = Institution(id=str(uuid.uuid4()), name="Delhi Skill Center")
    inst2 = Institution(id=str(uuid.uuid4()), name="Mumbai Tech Institute")
    db.add_all([inst1, inst2])
    db.flush()
    print(f"Institutions: {inst1.name}, {inst2.name}")

    pm = User(
        name="Programme Manager",
        email="pm@skillbridge.com",
        hashed_password=hash_password("pm@1234"),
        role=RoleEnum.programme_manager,
    )
    db.add(pm)

    mo = User(
        name="Monitoring Officer",
        email="monitor@skillbridge.com",
        hashed_password=hash_password("monitor@1234"),
        role=RoleEnum.monitoring_officer,
    )
    db.add(mo)

    inst_user1 = User(
        name="Delhi Institution Admin",
        email="delhi@skillbridge.com",
        hashed_password=hash_password("delhi@1234"),
        role=RoleEnum.institution,
        institution_id=inst1.id,
    )
    inst_user2 = User(
        name="Mumbai Institution Admin",
        email="mumbai@skillbridge.com",
        hashed_password=hash_password("mumbai@1234"),
        role=RoleEnum.institution,
        institution_id=inst2.id,
    )
    db.add_all([inst_user1, inst_user2])

    trainers = []
    trainer_data = [
        ("Trainer Rahul", "rahul@skillbridge.com", inst1.id),
        ("Trainer Priya", "priya@skillbridge.com", inst1.id),
        ("Trainer Amit", "amit@skillbridge.com", inst2.id),
        ("Trainer Sneha", "sneha@skillbridge.com", inst2.id),
    ]
    for name, email, inst_id in trainer_data:
        t = User(
            name=name,
            email=email,
            hashed_password=hash_password("trainer@1234"),
            role=RoleEnum.trainer,
            institution_id=inst_id,
        )
        db.add(t)
        trainers.append(t)

    students = []
    for i in range(1, 16):
        s = User(
            name=f"Student {i:02d}",
            email=f"student{i:02d}@skillbridge.com",
            hashed_password=hash_password("student@1234"),
            role=RoleEnum.student,
        )
        db.add(s)
        students.append(s)

    db.flush()
    print(f"Users created: 1 PM, 1 MO, 2 Institution, 4 Trainers, 15 Students")

    batch1 = Batch(name="Web Dev Batch A", institution_id=inst1.id)
    batch2 = Batch(name="Data Science Batch B", institution_id=inst1.id)
    batch3 = Batch(name="AI/ML Batch C", institution_id=inst2.id)
    db.add_all([batch1, batch2, batch3])
    db.flush()
    print(f"Batches: {batch1.name}, {batch2.name}, {batch3.name}")

    db.add_all([
        BatchTrainer(batch_id=batch1.id, trainer_id=trainers[0].id),
        BatchTrainer(batch_id=batch1.id, trainer_id=trainers[1].id),
        BatchTrainer(batch_id=batch2.id, trainer_id=trainers[1].id),
        BatchTrainer(batch_id=batch3.id, trainer_id=trainers[2].id),
        BatchTrainer(batch_id=batch3.id, trainer_id=trainers[3].id),
    ])

    for s in students[:6]:
        db.add(BatchStudent(batch_id=batch1.id, student_id=s.id))
    for s in students[5:11]:
        db.add(BatchStudent(batch_id=batch2.id, student_id=s.id))
    for s in students[10:]:
        db.add(BatchStudent(batch_id=batch3.id, student_id=s.id))
    db.flush()

    base_date = datetime.utcnow().date()
    sessions_data = [
        (batch1.id, trainers[0].id, "HTML & CSS Basics",     "09:00", "11:00"),
        (batch1.id, trainers[0].id, "JavaScript Intro",       "09:00", "11:00"),
        (batch1.id, trainers[1].id, "React Fundamentals",     "14:00", "16:00"),
        (batch2.id, trainers[1].id, "Python for Data Science","09:00", "11:00"),
        (batch2.id, trainers[1].id, "Pandas & NumPy",         "09:00", "11:00"),
        (batch3.id, trainers[2].id, "ML Introduction",        "10:00", "12:00"),
        (batch3.id, trainers[2].id, "Neural Networks",        "10:00", "12:00"),
        (batch3.id, trainers[3].id, "Deep Learning Basics",   "14:00", "16:00"),
    ]

    sess_objects = []
    for i, (bid, tid, title, st, et) in enumerate(sessions_data):
        s = Session(
            batch_id=bid,
            trainer_id=tid,
            title=title,
            date=str(base_date - timedelta(days=i)),
            start_time=st,
            end_time=et,
        )
        db.add(s)
        sess_objects.append(s)
    db.flush()
    print(f"Sessions: {len(sess_objects)} created")

    statuses = [AttendanceStatus.present, AttendanceStatus.present, AttendanceStatus.present, AttendanceStatus.late, AttendanceStatus.absent]
    att_count = 0

    batch_student_map = {
        batch1.id: students[:6],
        batch2.id: students[5:11],
        batch3.id: students[10:],
    }

    for sess in sess_objects:
        batch_students = batch_student_map.get(sess.batch_id, [])
        for idx, student in enumerate(batch_students):
            status = statuses[idx % len(statuses)]
            db.add(Attendance(
                session_id=sess.id,
                student_id=student.id,
                status=status,
            ))
            att_count += 1

    print("\n Seeded IDs (use these in curl examples):")
    print(f"  Institution 1 (Delhi): {inst1.id}")
    print(f"  Institution 2 (Mumbai): {inst2.id}")
    print(f"  Batch 1 (Web Dev): {batch1.id}")
    print(f"  Batch 2 (Data Science): {batch2.id}")
    print(f"  Batch 3 (AI/ML): {batch3.id}")
    print(f"  Session 1 ID: {sess_objects[0].id}")

    db.commit()
    print(f"Attendance records: {att_count} created")
    print("\n Seed complete! Test accounts:")
    print("  student01@skillbridge.com     / student@1234  (Student)")
    print("  rahul@skillbridge.com         / trainer@1234  (Trainer - batch1)")
    print("  delhi@skillbridge.com         / delhi@1234    (Institution)")
    print("  pm@skillbridge.com            / pm@1234       (Programme Manager)")
    print("  monitor@skillbridge.com       / monitor@1234  (Monitoring Officer)")


if __name__ == "__main__":
    run()
