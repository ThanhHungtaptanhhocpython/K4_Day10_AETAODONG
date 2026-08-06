from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _parse_date(value: str) -> datetime | None:
    text = normalize_whitespace(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _build_text_for_embedding(row: dict) -> str:
    parts = [
        f"Title: {row['title']}",
        f"Authors: {row['authors_joined']}" if row["authors_joined"] else "",
        f"Categories: {row['categories_joined']}" if row["categories_joined"] else "",
        f"Published: {row['published']}" if row["published"] else "",
        f"Summary: {row['summary']}",
    ]
    return "\n".join(part for part in parts if part)


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    run_date_utc = run_date if run_date.tzinfo else run_date.replace(tzinfo=UTC)
    rows: list[dict] = []

    for record in records:
        title = normalize_whitespace(record.title)
        summary = normalize_whitespace(record.summary)
        authors = [normalize_whitespace(author) for author in record.authors if normalize_whitespace(author)]
        categories = [
            normalize_whitespace(category) for category in record.categories if normalize_whitespace(category)
        ]
        if not record.paper_id or not title or not summary:
            continue

        published_raw = record.published or record.updated
        published_dt = _parse_date(published_raw)
        published = published_dt.date().isoformat() if published_dt else ""
        updated_dt = _parse_date(record.updated) or published_dt
        updated = updated_dt.date().isoformat() if updated_dt else ""
        age_days = (run_date_utc.date() - published_dt.date()).days if published_dt else None

        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)
        row = {
            "paper_id": record.paper_id.lower(),
            "title": title,
            "summary": summary,
            "authors": authors,
            "categories": categories,
            "primary_category": normalize_whitespace(record.primary_category) or (
                categories[0] if categories else "uncategorized"
            ),
            "published": published,
            "updated": updated,
            "abs_url": normalize_whitespace(record.abs_url),
            "pdf_url": normalize_whitespace(record.pdf_url),
            "comment": normalize_whitespace(record.comment),
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "summary_chars": len(summary),
            "age_days": age_days,
        }
        row["text_for_embedding"] = _build_text_for_embedding(row)
        if len(row["text_for_embedding"].strip()) < 40:
            continue
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df[df["summary_chars"] >= 40].copy()
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True], na_position="last")
    df = df.reset_index(drop=True)
    return df
