from typing import Any, Literal

from pydantic import BaseModel, Field


DatasetName = Literal[
    "movies",
    "viewers",
    "watch_activity",
    "reviews",
    "marketing_spend",
    "regional_performance",
]


class TokenRequest(BaseModel):
    user_id: str = Field(default="demo-user", min_length=3, max_length=120)
    role: str = Field(default="analyst", min_length=3, max_length=60)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class ChatRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)


class SourceReference(BaseModel):
    source_type: str
    name: str
    snippet: str | None = None


class ChatTrace(BaseModel):
    tools_used: list[str]
    workflow: list[str] = []
    synthesis_engine: str | None = None
    confidence: str | None = None
    reasoning: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    metrics: dict[str, Any]
    recommendations: list[str]
    trace: ChatTrace
    guardrails: dict[str, Any] = Field(default_factory=dict)


class CsvIngestionResponse(BaseModel):
    dataset: DatasetName
    rows_loaded: int
    status: str = "loaded"


class PdfIngestionResponse(BaseModel):
    document_id: int
    chunks_loaded: int
    status: str = "loaded"


class SeedResponse(BaseModel):
    status: str
    rows: dict[str, int]
    documents: int


class TopTitle(BaseModel):
    title: str
    genre: str
    views: int
    revenue: float
    completion_rate: float


class ComparisonMetric(BaseModel):
    title: str
    views: int
    revenue: float
    avg_rating: float | None
    completion_rate: float


class CityEngagement(BaseModel):
    city: str
    engagement_score: float
    watch_minutes: int


class GenrePerformance(BaseModel):
    genre: str
    views: int
    revenue: float
    avg_rating: float | None


class AudienceSegment(BaseModel):
    segment: str
    views: int
    watch_minutes: int
    revenue: float
