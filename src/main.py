from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from src.routers import auth, batches, sessions, attendance, institutions, programme, monitoring


app = FastAPI(
    title="SkillBridge Attendance API",
    description="Attendance management system for SkillBridge skilling programme",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        })
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=404, content={"detail": "Referenced resource not found or constraint violated"})



app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(institutions.router)
app.include_router(programme.router)
app.include_router(monitoring.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "SkillBridge API is running"}
