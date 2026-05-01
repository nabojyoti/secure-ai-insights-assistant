from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.models.schemas import AudienceSegment, CityEngagement, ComparisonMetric, GenrePerformance, TopTitle
from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics = AnalyticsService()


@router.get("/top-titles", response_model=list[TopTitle])
def top_titles(
    year: int = Query(default=2025, ge=2000, le=2100),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return analytics.top_titles(db, year=year, limit=limit)


@router.get("/compare-titles", response_model=list[ComparisonMetric])
def compare_titles(
    title_a: str = Query(min_length=1, max_length=200),
    title_b: str = Query(min_length=1, max_length=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return analytics.compare_titles(db, title_a, title_b)


@router.get("/strongest-city", response_model=CityEngagement | None)
def strongest_city(
    month: str = Query(default="2026-04", pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return analytics.strongest_city(db, month=month)


@router.get("/weak-genres", response_model=list[GenrePerformance])
def weak_genres(
    limit: int = Query(default=3, ge=1, le=20),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return analytics.weak_genres(db, limit=limit)


@router.get("/audience-segments", response_model=list[AudienceSegment])
def audience_segments(
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return analytics.audience_segments(db, limit=limit)
