from typing import Any


class EvidenceService:
    def build(self, question: str, metrics: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
        facts: list[str] = []

        for row in metrics.get("top_titles", [])[:3]:
            facts.append(
                f"{row['title']} generated {row['revenue']} revenue across {row['views']} views "
                f"with {row['completion_rate']:.1%} completion."
            )

        for row in metrics.get("compare_titles", []):
            rating = "unknown rating" if row.get("avg_rating") is None else f"{row['avg_rating']} average rating"
            facts.append(
                f"{row['title']} had {row['views']} views, {row['revenue']} revenue, "
                f"{row['completion_rate']:.1%} completion, and {rating}."
            )

        if metrics.get("strongest_city"):
            city = metrics["strongest_city"]
            facts.append(
                f"{city['city']} had the strongest regional engagement with score "
                f"{city['engagement_score']} and {city['watch_minutes']} watch minutes."
            )

        for row in metrics.get("weak_genres", [])[:2]:
            facts.append(
                f"{row['genre']} showed weak performance with {row['views']} views, "
                f"{row['revenue']} revenue, and {row.get('avg_rating')} average rating."
            )

        for row in metrics.get("audience_segments", [])[:3]:
            facts.append(
                f"{row['segment']} produced {row['views']} views, {row['watch_minutes']} watch minutes, "
                f"and {row['revenue']} revenue."
            )

        for row in metrics.get("marketing_roi", [])[:3]:
            facts.append(
                f"{row['title']} used {row['channel']} marketing with {row['spend']} spend, "
                f"{row['revenue']} revenue, and {row['roi']} ROI."
            )

        for doc in metrics.get("documents", [])[:4]:
            facts.append(f"{doc['document_name']} says: {doc['snippet']}")

        source_labels = []
        for source in sources:
            label = f"{source.get('source_type', 'source').upper()}: {source.get('name', 'unknown')}"
            if label not in source_labels:
                source_labels.append(label)

        return {
            "question": question,
            "facts": facts,
            "sources": source_labels,
            "metrics_available": sorted(metrics.keys()),
        }
