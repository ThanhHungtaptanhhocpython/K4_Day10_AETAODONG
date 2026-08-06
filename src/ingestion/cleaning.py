from __future__ import annotations

from datetime import datetime
import re

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord

# Cleaning rules (bat buoc): drop rac (title trong hoac summary < 100 ky tu),
# strip XML/HTML tags, gop authors/categories bang dau phay, chuan hoa ngay va
# tinh age_days, tao text_for_embedding dang "Title: ... | Authors: ... | Summary: ...".
MIN_SUMMARY_CHARS = 100

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(value: str) -> str:
    """Remove XML/HTML tags (e.g. <jats:p>, <b>) and collapse whitespace."""
    if not value:
        return ""
    return normalize_whitespace(_TAG_RE.sub(" ", value))


def _parse_date(value: str) -> pd.Timestamp | None:
    if not value:
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed


def _build_embedding_text(title: str, authors: str, summary: str) -> str:
    return f"Title: {title} | Authors: {authors} | Summary: {summary}"


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a dataframe ready for embedding + observability.

    Produces one row per valid paper with normalized text fields, freshness
    fields (``published``, ``age_days``) and a ``text_for_embedding`` column.
    """
    run_ts = pd.Timestamp(run_date)
    if run_ts.tzinfo is None:
        run_ts = run_ts.tz_localize("UTC")

    rows: list[dict] = []
    for record in records:
        # Strip any XML/HTML tags from title and summary before length checks.
        title = _strip_tags(record.title)
        summary = _strip_tags(record.summary)
        paper_id = normalize_whitespace(record.paper_id)
        # Drop rac: khong co title hoac summary qua ngan (< 100 ky tu).
        if not paper_id or not title or len(summary) < MIN_SUMMARY_CHARS:
            continue

        published_ts = _parse_date(record.published)
        if published_ts is None:
            continue
        updated_ts = _parse_date(record.updated) or published_ts

        authors = [normalize_whitespace(a) for a in record.authors if normalize_whitespace(a)]
        categories = [normalize_whitespace(c) for c in record.categories if normalize_whitespace(c)]
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)

        age_days = max(0, int((run_ts - published_ts).days))

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "authors_joined": authors_joined,
                "categories": categories,
                "categories_joined": categories_joined,
                "primary_category": normalize_whitespace(record.primary_category) or "uncategorized",
                "published": published_ts.date().isoformat(),
                "updated": updated_ts.date().isoformat(),
                "age_days": age_days,
                "summary_chars": len(summary),
                "abs_url": normalize_whitespace(record.abs_url),
                "pdf_url": normalize_whitespace(record.pdf_url),
                "text_for_embedding": _build_embedding_text(title, authors_joined, summary),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset="paper_id", keep="first")
    # Newest papers first so downstream code and reports are deterministic.
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df
