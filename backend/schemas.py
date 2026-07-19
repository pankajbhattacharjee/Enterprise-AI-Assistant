from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Citation(BaseModel):
    document: str
    page: int | None = None
    score: float
    excerpt: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: float | None = None
    citations: list[Citation] = []
    sql: str | None = None
    rows: list[dict] = []


class ReportRequest(BaseModel):
    title: str = Field(default="Enterprise Assistant Report", max_length=160)
    question: str = Field(min_length=2, max_length=4000)
    answer: str = Field(min_length=1, max_length=20000)
    findings: list[str] = []


class HistoryItem(BaseModel):
    question: str
    answer: str
    intent: str
    created_at: datetime
