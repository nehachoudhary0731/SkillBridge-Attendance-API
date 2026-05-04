from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from src.db.connect_to_db import get_db
from src.db.models import Institution, Attendance, RoleEnum
from src.auth.security import require_role

router = APIRouter(prefix="/programme", tags=["Programme"])


@router.get("/summary")
def programme_summary(
    db: DBSession = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.programme_manager)),
):
    institutions = db.query(Institution).all()
    summary = []

    for inst in institutions:
        total_sessions = sum(len(b.sessions) for b in inst.batches)
        total_students = sum(len(b.students) for b in inst.batches)
        session_ids = [s.id for b in inst.batches for s in b.sessions]
        records = db.query(Attendance).filter(Attendance.session_id.in_(session_ids)).all() if session_ids else []
        present = sum(1 for r in records if r.status == "present")

        summary.append({
            "institution_id": inst.id,
            "institution_name": inst.name,
            "total_batches": len(inst.batches),
            "total_sessions": total_sessions,
            "total_students": total_students,
            "present_count": present,
            "total_attendance_records": len(records),
        })

    return {
        "programme": "SkillBridge",
        "total_institutions": len(institutions),
        "institutions": summary,
    }
