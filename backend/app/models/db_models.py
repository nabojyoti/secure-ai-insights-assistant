from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    genre: Mapped[str] = mapped_column(String(80), index=True)
    release_year: Mapped[int] = mapped_column(Integer, index=True)
    production_budget: Mapped[float] = mapped_column(Float, default=0)


class Viewer(Base):
    __tablename__ = "viewers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment: Mapped[str] = mapped_column(String(120), index=True)
    city: Mapped[str] = mapped_column(String(120), index=True)
    age_band: Mapped[str] = mapped_column(String(40))


class WatchActivity(Base):
    __tablename__ = "watch_activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    viewer_id: Mapped[int] = mapped_column(ForeignKey("viewers.id"), index=True)
    watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    watch_minutes: Mapped[int] = mapped_column(Integer)
    completed: Mapped[bool] = mapped_column(default=False)
    revenue: Mapped[float] = mapped_column(Float, default=0)

    movie: Mapped[Movie] = relationship()
    viewer: Mapped[Viewer] = relationship()


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    rating: Mapped[float] = mapped_column(Float)
    sentiment: Mapped[str] = mapped_column(String(40))
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class MarketingSpend(Base):
    __tablename__ = "marketing_spend"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    channel: Mapped[str] = mapped_column(String(80), index=True)
    spend: Mapped[float] = mapped_column(Float)
    campaign_month: Mapped[str] = mapped_column(String(7), index=True)


class RegionalPerformance(Base):
    __tablename__ = "regional_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    city: Mapped[str] = mapped_column(String(120), index=True)
    engagement_score: Mapped[float] = mapped_column(Float)
    month: Mapped[str] = mapped_column(String(7), index=True)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    document_type: Mapped[str] = mapped_column(String(80), default="report")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    document: Mapped[Document] = relationship(back_populates="chunks")

    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk"),)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    query: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ToolTrace(Base):
    __tablename__ = "tool_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    query: Mapped[str] = mapped_column(Text)
    tool_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
