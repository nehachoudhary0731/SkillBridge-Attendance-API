from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from src.db.connect_to_db import get_db
from src.db.models import Institution, Batch, Attendance, RoleEnum
from src.auth.security import require_role

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.get("/{institution_id}/summary")
def institution_summary(
    institution_id: str,
    db: DBSession = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.programme_manager)),
):
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch_summaries = []
    for batch in institution.batches:
        session_ids = [s.id for s in batch.sessions]
        records = db.query(Attendance).filter(Attendance.session_id.in_(session_ids)).all() if session_ids else []
        present = sum(1 for r in records if r.status == "present")
        batch_summaries.append({
            "batch_id": batch.id,
            "batch_name": batch.name,
            "total_sessions": len(batch.sessions),
            "total_students": len(batch.students),
            "present_count": present,
            "total_records": len(records),
        })

    return {
        "institution_id": institution_id,
        "institution_name": institution.name,
        "total_batches": len(institution.batches),
        "batches": batch_summaries,
    }
