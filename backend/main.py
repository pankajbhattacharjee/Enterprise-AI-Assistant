import logging
from pathlib import Path
from uuid import uuid4
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from agents.manager import run_workflow
from backend.auth import create_access_token, current_user, hash_password, verify_password
from backend.config import get_settings
from backend.database import Base, engine, get_db
from backend.models import ChatMessage, Document, Report, User
from backend.schemas import ChatRequest, ChatResponse, HistoryItem, LoginRequest, RegisterRequest, ReportRequest, TokenResponse
from rag.pipeline import index_document
from reports.generator import generate_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
settings = get_settings()
app = FastAPI(title="Enterprise AI Assistant", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def initialise() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # A minimal analytics dataset makes the SQL agent demonstrable out of the box.
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, customer VARCHAR(100), region VARCHAR(40), amount NUMERIC, sold_at DATE)"))
        count = connection.execute(text("SELECT COUNT(*) FROM sales")).scalar_one()
        if count == 0:
            connection.execute(text("INSERT INTO sales (id, customer, region, amount, sold_at) VALUES (1, 'Acme Ltd', 'North', 12500, '2026-06-04'), (2, 'Globex', 'South', 8700, '2026-06-15'), (3, 'Initech', 'North', 15300, '2026-07-02')"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "environment": settings.app_env}


@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenResponse(access_token=create_access_token(user))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return TokenResponse(access_token=create_access_token(user))


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    allowed = {".pdf", ".docx", ".txt"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=415, detail="Only PDF, DOCX and TXT files are allowed")
    contents = await file.read()
    if not contents or len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is empty or exceeds the upload size limit")
    safe_name = f"{uuid4().hex}{suffix}"
    target = settings.upload_dir / safe_name
    target.write_bytes(contents)
    document = Document(filename=Path(file.filename).name, stored_path=str(target), uploaded_by=user.id)
    db.add(document); db.commit(); db.refresh(document)
    try:
        chunks = index_document(target, document.id, user.id, document.filename)
    except Exception as exc:
        db.delete(document); db.commit(); target.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Could not extract document text: {exc}")
    return {"document_id": document.id, "filename": document.filename, "chunks_indexed": chunks}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ChatResponse:
    try:
        result = run_workflow(payload.question, user.id, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.add(ChatMessage(user_id=user.id, question=payload.question, answer=result["answer"], intent=result["intent"]))
    db.commit()
    return ChatResponse(**result)


@app.get("/api/history", response_model=list[HistoryItem])
def history(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[ChatMessage]:
    return db.query(ChatMessage).filter(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(100).all()


@app.post("/api/reports")
def create_report(payload: ReportRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    filename = f"report-{uuid4().hex}.pdf"
    path = settings.report_dir / filename
    generate_report(path, payload.title, payload.question, payload.answer, payload.findings)
    report = Report(filename=filename, path=str(path), user_id=user.id)
    db.add(report); db.commit(); db.refresh(report)
    return {"report_id": report.id, "download_url": f"/api/reports/{report.id}/download"}


@app.get("/api/reports/{report_id}/download")
def download_report(report_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> FileResponse:
    report = db.get(Report, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report.path, media_type="application/pdf", filename=report.filename)
