from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from src.db.connect_to_db import get_db
from src.db.models import Batch, BatchTrainer, BatchStudent, BatchInvite, Institution, Attendance, RoleEnum
from src.db.schemas import BatchCreate, JoinBatchRequest
from src.auth.security import require_role, get_current_user
import uuid

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.post("", status_code=201)
def create_batch(
    body: BatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.trainer, RoleEnum.institution)),
):
    institution = db.query(Institution).filter(Institution.id == body.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch = Batch(name=body.name, institution_id=body.institution_id)
    db.add(batch)
    db.flush()

    if current_user.role == RoleEnum.trainer:
        bt = BatchTrainer(batch_id=batch.id, trainer_id=current_user.id)
        db.add(bt)

    db.commit()
    db.refresh(batch)
    return {"id": batch.id, "name": batch.name, "institution_id": batch.institution_id, "created_at": batch.created_at}


@router.post("/{batch_id}/invite", status_code=201)
def create_invite(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.trainer)),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    token = str(uuid.uuid4())
    invite = BatchInvite(
        batch_id=batch_id,
        token=token,
        created_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        used=False,
    )
    db.add(invite)
    db.commit()
    return {"invite_token": token, "expires_at": invite.expires_at, "batch_id": batch_id}


@router.post("/join")
def join_batch(
    body: JoinBatchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.student)),
):
    invite = db.query(BatchInvite).filter(BatchInvite.token == body.token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite token")
    if invite.used:
        raise HTTPException(status_code=422, detail="Invite token already used")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=422, detail="Invite token expired")

    existing = db.query(BatchStudent).filter(
        BatchStudent.batch_id == invite.batch_id,
        BatchStudent.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=422, detail="Already a member of this batch")

    bs = BatchStudent(batch_id=invite.batch_id, student_id=current_user.id)
    db.add(bs)
    invite.used = True
    db.commit()
    return {"message": "Successfully joined batch", "batch_id": invite.batch_id}


@router.get("/{batch_id}/summary")
def batch_summary(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.institution)),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    total_sessions = len(batch.sessions)
    total_students = len(batch.students)

    session_ids = [s.id for s in batch.sessions]
    attendance_records = db.query(Attendance).filter(Attendance.session_id.in_(session_ids)).all() if session_ids else []

    present_count = sum(1 for a in attendance_records if a.status == "present")
    total_possible = total_sessions * total_students

    return {
        "batch_id": batch_id,
        "batch_name": batch.name,
        "total_sessions": total_sessions,
        "total_students": total_students,
        "total_attendance_records": len(attendance_records),
        "present_count": present_count,
        "attendance_rate": f"{(present_count / total_possible * 100):.1f}%" if total_possible > 0 else "N/A",
    }
