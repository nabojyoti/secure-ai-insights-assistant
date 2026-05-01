import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "data" / "csv"
PDF_DIR = ROOT / "data" / "pdf"


MOVIES = [
    {"id": 1, "title": "Stellar Run", "genre": "Sci-Fi", "release_year": 2025, "production_budget": 48000000},
    {"id": 2, "title": "Dark Orbit", "genre": "Sci-Fi", "release_year": 2025, "production_budget": 41000000},
    {"id": 3, "title": "Last Kingdom", "genre": "Drama", "release_year": 2025, "production_budget": 35000000},
    {"id": 4, "title": "Laugh Track", "genre": "Comedy", "release_year": 2025, "production_budget": 22000000},
    {"id": 5, "title": "City Lights", "genre": "Romance", "release_year": 2024, "production_budget": 18000000},
    {"id": 6, "title": "Final Whistle", "genre": "Sports", "release_year": 2025, "production_budget": 27000000},
]

VIEWERS = [
    {"id": 1, "segment": "Gen Z streamers", "city": "Mumbai", "age_band": "18-24"},
    {"id": 2, "segment": "Family co-viewers", "city": "Bengaluru", "age_band": "25-34"},
    {"id": 3, "segment": "Premium subscribers", "city": "Delhi", "age_band": "35-44"},
    {"id": 4, "segment": "Weekend binge watchers", "city": "Hyderabad", "age_band": "25-34"},
    {"id": 5, "segment": "Regional explorers", "city": "Pune", "age_band": "18-24"},
    {"id": 6, "segment": "Critic-led viewers", "city": "Chennai", "age_band": "35-44"},
]


def write_csv(name: str, rows: list[dict]) -> None:
    path = CSV_DIR / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_watch_activity() -> list[dict]:
    rng = random.Random(42)
    base = datetime(2026, 4, 1, 10, 0, 0)
    weights = {1: 1.65, 2: 1.2, 3: 1.05, 4: 0.45, 5: 0.65, 6: 0.9}
    rows = []
    row_id = 1
    for day in range(30):
        for movie in MOVIES:
            for viewer in VIEWERS:
                multiplier = weights[movie["id"]]
                views = max(1, int(rng.randint(1, 5) * multiplier))
                for _ in range(views):
                    rows.append(
                        {
                            "id": row_id,
                            "movie_id": movie["id"],
                            "viewer_id": viewer["id"],
                            "watched_at": (base + timedelta(days=day, hours=rng.randint(0, 12))).isoformat(),
                            "watch_minutes": rng.randint(35, 130),
                            "completed": rng.random() < (0.82 if movie["id"] != 4 else 0.48),
                            "revenue": round(rng.uniform(2.5, 9.0) * multiplier, 2),
                        }
                    )
                    row_id += 1
    return rows


def generate_reviews() -> list[dict]:
    return [
        {"id": 1, "movie_id": 1, "rating": 4.7, "sentiment": "positive", "comment": "Strong rewatch intent and social buzz."},
        {"id": 2, "movie_id": 2, "rating": 4.2, "sentiment": "positive", "comment": "Dark Orbit performs well with sci-fi fans."},
        {"id": 3, "movie_id": 3, "rating": 4.0, "sentiment": "positive", "comment": "Last Kingdom has loyal drama audience."},
        {"id": 4, "movie_id": 4, "rating": 2.8, "sentiment": "negative", "comment": "Comedy timing feels stale to younger segments."},
        {"id": 5, "movie_id": 5, "rating": 3.5, "sentiment": "neutral", "comment": "Stable catalog performance."},
        {"id": 6, "movie_id": 6, "rating": 3.8, "sentiment": "positive", "comment": "Sports fans engage around weekends."},
    ]


def generate_marketing_spend() -> list[dict]:
    return [
        {"id": 1, "movie_id": 1, "channel": "Social", "spend": 900000, "campaign_month": "2026-04"},
        {"id": 2, "movie_id": 2, "channel": "Influencer", "spend": 650000, "campaign_month": "2026-04"},
        {"id": 3, "movie_id": 3, "channel": "Search", "spend": 420000, "campaign_month": "2026-04"},
        {"id": 4, "movie_id": 4, "channel": "Display", "spend": 500000, "campaign_month": "2026-04"},
        {"id": 5, "movie_id": 6, "channel": "Sports partnerships", "spend": 380000, "campaign_month": "2026-04"},
    ]


def generate_regional_performance() -> list[dict]:
    return [
        {"id": 1, "movie_id": 1, "city": "Mumbai", "engagement_score": 91.5, "month": "2026-04"},
        {"id": 2, "movie_id": 1, "city": "Bengaluru", "engagement_score": 88.2, "month": "2026-04"},
        {"id": 3, "movie_id": 2, "city": "Delhi", "engagement_score": 79.3, "month": "2026-04"},
        {"id": 4, "movie_id": 3, "city": "Hyderabad", "engagement_score": 73.4, "month": "2026-04"},
        {"id": 5, "movie_id": 4, "city": "Pune", "engagement_score": 41.8, "month": "2026-04"},
        {"id": 6, "movie_id": 6, "city": "Chennai", "engagement_score": 68.1, "month": "2026-04"},
    ]


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf(path: Path, title: str, lines: list[str]) -> None:
    text_commands = ["BT", "/F1 14 Tf", "72 760 Td", f"({pdf_escape(title)}) Tj", "/F1 10 Tf"]
    for line in lines:
        text_commands.append("0 -18 Td")
        text_commands.append(f"({pdf_escape(line[:105])}) Tj")
    text_commands.append("ET")
    stream = "\n".join(text_commands)

    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
        "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        f"5 0 obj\n<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream\nendobj\n",
    ]

    content = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(content.encode("utf-8")))
        content += obj
    xref_at = len(content.encode("utf-8"))
    content += f"xref\n0 {len(objects) + 1}\n"
    content += "0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n"
    content += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
    path.write_text(content, encoding="utf-8")


def generate_pdfs() -> None:
    reports = {
        "quarterly_executive_report.pdf": [
            "Stellar Run is the strongest 2025 title by revenue, repeat viewing, and completion rate.",
            "The title is trending because social clips, sci-fi audience overlap, and positive reviews reinforced one another.",
            "Leadership should extend the campaign and cross-promote Dark Orbit to the same audience cluster.",
        ],
        "campaign_performance_summary.pdf": [
            "Social and influencer campaigns performed better than broad display campaigns in April 2026.",
            "Comedy spend on Laugh Track underperformed because completion rate and sentiment were both weak.",
            "Recommended action: reduce broad display spend and test creator-led comedy positioning before scaling.",
        ],
        "content_roadmap.pdf": [
            "The 2025 slate should prioritize sci-fi, drama, and sports content for retention-led growth.",
            "Comedy needs sharper concepts, smaller pilots, and earlier audience testing.",
            "Stellar Run spin-off content can support next-quarter engagement goals.",
        ],
        "policy_guidelines.pdf": [
            "Internal analytics responses must cite approved SQL, CSV, or PDF sources.",
            "The assistant must not reveal secrets, credentials, raw private files, or unrestricted database contents.",
            "Leadership recommendations must be grounded in retrieved evidence and tool outputs.",
        ],
        "audience_behavior_report.pdf": [
            "Mumbai and Bengaluru produced the strongest regional engagement in April 2026.",
            "Gen Z streamers and weekend binge watchers showed the highest responsiveness to sci-fi campaigns.",
            "Audience segments prefer short social previews before committing to full-length titles.",
        ],
    }
    for filename, lines in reports.items():
        write_simple_pdf(PDF_DIR / filename, filename.replace("_", " ").replace(".pdf", "").title(), lines)


def main() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    write_csv("movies.csv", MOVIES)
    write_csv("viewers.csv", VIEWERS)
    write_csv("watch_activity.csv", generate_watch_activity())
    write_csv("reviews.csv", generate_reviews())
    write_csv("marketing_spend.csv", generate_marketing_spend())
    write_csv("regional_performance.csv", generate_regional_performance())
    generate_pdfs()

    print(f"Generated CSV data in {CSV_DIR}")
    print(f"Generated PDF reports in {PDF_DIR}")


if __name__ == "__main__":
    main()
