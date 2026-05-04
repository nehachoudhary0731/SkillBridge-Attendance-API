from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum, Text, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.connect_to_db import Base
import enum
import uuid


def gen_uuid():
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    institution = relationship("Institution", back_populates="users")
    batch_trainers = relationship("BatchTrainer", back_populates="trainer")
    batch_students = relationship("BatchStudent", back_populates="student")
    sessions = relationship("Session", back_populates="trainer")
    attendances = relationship("Attendance", back_populates="student")
    invites_created = relationship("BatchInvite", back_populates="created_by_user")


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="institution")
    batches = relationship("Batch", back_populates="institution")


class Batch(Base):
    __tablename__ = "batches"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    institution = relationship("Institution", back_populates="batches")
    trainers = relationship("BatchTrainer", back_populates="batch")
    students = relationship("BatchStudent", back_populates="batch")
    sessions = relationship("Session", back_populates="batch")
    invites = relationship("BatchInvite", back_populates="batch")


class BatchTrainer(Base):
    __tablename__ = "batch_trainers"

    batch_id = Column(String, ForeignKey("batches.id"), primary_key=True)
    trainer_id = Column(String, ForeignKey("users.id"), primary_key=True)

    batch = relationship("Batch", back_populates="trainers")
    trainer = relationship("User", back_populates="batch_trainers")


class BatchStudent(Base):
    __tablename__ = "batch_students"

    batch_id = Column(String, ForeignKey("batches.id"), primary_key=True)
    student_id = Column(String, ForeignKey("users.id"), primary_key=True)

    batch = relationship("Batch", back_populates="students")
    student = relationship("User", back_populates="batch_students")


class BatchInvite(Base):
    __tablename__ = "batch_invites"

    id = Column(String, primary_key=True, default=gen_uuid)
    batch_id = Column(String, ForeignKey("batches.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)

    batch = relationship("Batch", back_populates="invites")
    created_by_user = relationship("User", back_populates="invites_created")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=gen_uuid)
    batch_id = Column(String, ForeignKey("batches.id"), nullable=False)
    trainer_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("Batch", back_populates="sessions")
    trainer = relationship("User", back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)
    marked_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="attendances")
    student = relationship("User", back_populates="attendances")
