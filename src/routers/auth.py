from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from src.db.connect_to_db import get_db
from src.db.models import User, RoleEnum
from src.db.schemas import SignupRequest, LoginRequest, MonitoringTokenRequest
from src.auth.security import (
    hash_password, verify_password, create_access_token,
    create_monitoring_token, decode_token, MONITORING_API_KEY,
    bearer_scheme
)
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=422, detail="Email already registered")
    user = User(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        institution_id=body.institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "role": user.role}


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "role": user.role}


@router.post("/monitoring-token")
def get_monitoring_token(
    body: MonitoringTokenRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    payload = decode_token(credentials.credentials)
    if payload.get("role") != "monitoring_officer":
        raise HTTPException(status_code=403, detail="Only monitoring officers can use this endpoint")

    if body.key != MONITORING_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    user_id = payload.get("sub")
    monitoring_token = create_monitoring_token(user_id)
    return {"monitoring_token": monitoring_token, "expires_in": "1 hour", "scope": "monitoring_readonly"}
