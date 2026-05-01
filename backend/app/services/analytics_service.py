from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.db_models import MarketingSpend, Movie, RegionalPerformance, Review, Viewer, WatchActivity


class AnalyticsService:
    def top_titles(self, db: Session, year: int = 2025, limit: int = 5) -> list[dict]:
        completed_count = func.sum(case((WatchActivity.completed.is_(True), 1), else_=0))
        revenue = func.coalesce(func.sum(WatchActivity.revenue), 0).label("revenue")
        rows = (
            db.query(
                Movie.title,
                Movie.genre,
                func.count(WatchActivity.id).label("views"),
                revenue,
                completed_count.label("completed_count"),
            )
            .join(WatchActivity, WatchActivity.movie_id == Movie.id)
            .filter(Movie.release_year == year)
            .group_by(Movie.id, Movie.title, Movie.genre)
            .order_by(revenue.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "title": row.title,
                "genre": row.genre,
                "views": int(row.views),
                "revenue": round(float(row.revenue), 2),
                "completion_rate": round(float(row.completed_count or 0) / max(int(row.views), 1), 3),
            }
            for row in rows
        ]

    def compare_titles(self, db: Session, title_a: str, title_b: str) -> list[dict]:
        completed_count = func.sum(case((WatchActivity.completed.is_(True), 1), else_=0))
        rows = (
            db.query(
                Movie.title,
                func.count(WatchActivity.id).label("views"),
                func.coalesce(func.sum(WatchActivity.revenue), 0).label("revenue"),
                completed_count.label("completed_count"),
                func.avg(Review.rating).label("avg_rating"),
            )
            .join(WatchActivity, WatchActivity.movie_id == Movie.id)
            .outerjoin(Review, Review.movie_id == Movie.id)
            .filter(Movie.title.in_([title_a, title_b]))
            .group_by(Movie.id, Movie.title)
            .order_by(Movie.title)
            .all()
        )
        return [
            {
                "title": row.title,
                "views": int(row.views),
                "revenue": round(float(row.revenue), 2),
                "avg_rating": round(float(row.avg_rating), 2) if row.avg_rating is not None else None,
                "completion_rate": round(float(row.completed_count or 0) / max(int(row.views), 1), 3),
            }
            for row in rows
        ]

    def strongest_city(self, db: Session, month: str = "2026-04") -> dict | None:
        engagement_score = func.avg(RegionalPerformance.engagement_score).label("engagement_score")
        row = (
            db.query(
                RegionalPerformance.city,
                engagement_score,
                func.coalesce(func.sum(WatchActivity.watch_minutes), 0).label("watch_minutes"),
            )
            .outerjoin(Movie, Movie.id == RegionalPerformance.movie_id)
            .outerjoin(WatchActivity, WatchActivity.movie_id == Movie.id)
            .filter(RegionalPerformance.month == month)
            .group_by(RegionalPerformance.city)
            .order_by(engagement_score.desc())
            .first()
        )
        if not row:
            return None
        return {
            "city": row.city,
            "engagement_score": round(float(row.engagement_score), 2),
            "watch_minutes": int(row.watch_minutes or 0),
        }

    def weak_genres(self, db: Session, limit: int = 3) -> list[dict]:
        views = func.count(WatchActivity.id).label("views")
        rows = (
            db.query(
                Movie.genre,
                views,
                func.coalesce(func.sum(WatchActivity.revenue), 0).label("revenue"),
                func.avg(Review.rating).label("avg_rating"),
            )
            .join(WatchActivity, WatchActivity.movie_id == Movie.id)
            .outerjoin(Review, Review.movie_id == Movie.id)
            .group_by(Movie.genre)
            .order_by(views)
            .limit(limit)
            .all()
        )
        return [
            {
                "genre": row.genre,
                "views": int(row.views),
                "revenue": round(float(row.revenue), 2),
                "avg_rating": round(float(row.avg_rating), 2) if row.avg_rating is not None else None,
            }
            for row in rows
        ]

    def audience_segments(self, db: Session, limit: int = 5) -> list[dict]:
        revenue = func.coalesce(func.sum(WatchActivity.revenue), 0).label("revenue")
        rows = (
            db.query(
                Viewer.segment,
                func.count(WatchActivity.id).label("views"),
                func.coalesce(func.sum(WatchActivity.watch_minutes), 0).label("watch_minutes"),
                revenue,
            )
            .join(WatchActivity, WatchActivity.viewer_id == Viewer.id)
            .group_by(Viewer.segment)
            .order_by(revenue.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "segment": row.segment,
                "views": int(row.views),
                "watch_minutes": int(row.watch_minutes or 0),
                "revenue": round(float(row.revenue), 2),
            }
            for row in rows
        ]

    def marketing_roi(self, db: Session) -> list[dict]:
        revenue = func.coalesce(func.sum(WatchActivity.revenue), 0).label("revenue")
        rows = (
            db.query(
                Movie.title,
                MarketingSpend.channel,
                func.sum(MarketingSpend.spend).label("spend"),
                revenue,
            )
            .join(Movie, Movie.id == MarketingSpend.movie_id)
            .outerjoin(WatchActivity, WatchActivity.movie_id == Movie.id)
            .group_by(Movie.title, MarketingSpend.channel)
            .order_by(revenue.desc())
            .all()
        )
        return [
            {
                "title": row.title,
                "channel": row.channel,
                "spend": round(float(row.spend), 2),
                "revenue": round(float(row.revenue), 2),
                "roi": round(float(row.revenue) / max(float(row.spend), 1), 4),
            }
            for row in rows
        ]
