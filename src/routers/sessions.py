from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from src.db.connect_to_db import get_db
from src.db.models import Session, Batch, BatchTrainer, Attendance, RoleEnum
from src.db.schemas import SessionCreate, SessionResponse
from src.auth.security import require_role

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", status_code=201, response_model=SessionResponse)
def create_session(
    body: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(require_role(RoleEnum.trainer)),
):
    batch = db.query(Batch).filter(Batch.id == body.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    assigned = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == body.batch_id,
        BatchTrainer.trainer_id == current_user["sub"],
    ).first()
    if not assigned:
        raise HTTPException(status_code=403, detail="You are not assigned to this batch")

    session = Session(
        batch_id=body.batch_id,
        trainer_id=current_user["sub"],
        title=body.title,
        date=body.date,             
        start_time=body.start_time, 
        end_time=body.end_time,     
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session  


@router.get("/{session_id}/attendance")
def get_session_attendance(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(require_role(RoleEnum.trainer)),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = db.query(Attendance).filter(Attendance.session_id == session_id).all()
    return {
        "session_id": session_id,
        "session_title": session.title,
        "date": str(session.date),
        "total_records": len(records),
        "attendance": [
            {
                "student_id": r.student_id,
                "status": r.status,
                "marked_at": r.marked_at,
            }
            for r in records
        ],
    }