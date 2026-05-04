from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from src.db.connect_to_db import get_db
from src.db.models import Attendance, Session, BatchStudent, AttendanceStatus, RoleEnum
from src.db.schemas import MarkAttendanceRequest
from src.auth.security import require_role

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/mark", status_code=201)
def mark_attendance(
    body: MarkAttendanceRequest,
    db: DBSession = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.student)),
):
    session = db.query(Session).filter(Session.id == body.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    enrolled = db.query(BatchStudent).filter(
        BatchStudent.batch_id == session.batch_id,
        BatchStudent.student_id == current_user["sub"],
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this session's batch")

    # Check if already marked
    existing = db.query(Attendance).filter(
        Attendance.session_id == body.session_id,
        Attendance.student_id == current_user["sub"],
    ).first()
    if existing:
        raise HTTPException(status_code=422, detail="Attendance already marked for this session")

    record = Attendance(
        session_id=body.session_id,
        student_id=current_user["sub"],
        status=body.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "session_id": record.session_id,
        "student_id": record.student_id,
        "status": record.status,
        "marked_at": record.marked_at,
    }
