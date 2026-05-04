from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DBSession
from src.db.connect_to_db import get_db
from src.db.models import Attendance
from src.auth.security import get_monitoring_user

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/attendance")
def monitoring_attendance(
    db: DBSession = Depends(get_db),
    current_user=Depends(get_monitoring_user),
):
    records = db.query(Attendance).all()
    return {
        "total_records": len(records),
        "attendance": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "student_id": r.student_id,
                "status": r.status,
                "marked_at": r.marked_at,
            }
            for r in records
        ],
    }


@router.post("/attendance")
@router.put("/attendance")
@router.patch("/attendance")
@router.delete("/attendance")
def monitoring_method_not_allowed():
    return JSONResponse(status_code=405, content={"detail": "Method Not Allowed. This endpoint is read-only."})
