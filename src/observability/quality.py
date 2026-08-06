from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tao bo data quality checks."""
    checks: list[dict[str, Any]] = []

    def add_check(name: str, success: bool, details: str) -> None:
        checks.append({"name": name, "success": success, "details": details})

    row_count = int(len(df))
    add_check(
        "row_count_positive",
        row_count > 0,
        f"Found {row_count} rows.",
    )

    if row_count == 0:
        report = {
            "report_name": report_name,
            "success": False,
            "failed_checks": ["row_count_positive"],
            "checks": checks,
        }
        write_json(settings.paths.quality_dir / f"{report_name}.json", report)
        return report

    null_paper_ids = int(df["paper_id"].isna().sum() + (df["paper_id"].astype(str).str.strip() == "").sum())
    add_check(
        "paper_id_not_null",
        null_paper_ids == 0,
        f"Null/blank paper_id count: {null_paper_ids}",
    )

    unique_ids = int(df["paper_id"].nunique(dropna=True))
    add_check(
        "paper_id_unique",
        unique_ids == row_count,
        f"Unique paper_id count: {unique_ids}/{row_count}",
    )

    null_titles = int(df["title"].isna().sum() + (df["title"].astype(str).str.strip() == "").sum())
    add_check(
        "title_not_null",
        null_titles == 0,
        f"Null/blank title count: {null_titles}",
    )

    short_summaries = int((df["summary"].astype(str).str.len() < 40).sum()) if "summary" in df.columns else row_count
    add_check(
        "summary_min_length",
        short_summaries == 0,
        f"Summaries shorter than 40 chars: {short_summaries}",
    )

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"].fillna(10**9) > settings.freshness_threshold_days).sum())
        add_check(
            "freshness_threshold",
            stale_rows == 0,
            f"Stale rows older than {settings.freshness_threshold_days} days: {stale_rows}",
        )
    else:
        add_check("freshness_threshold", False, "Missing age_days column.")

    empty_embeddings = (
        int((df["text_for_embedding"].astype(str).str.strip() == "").sum())
        if "text_for_embedding" in df.columns
        else row_count
    )
    add_check(
        "text_for_embedding_present",
        empty_embeddings == 0,
        f"Empty text_for_embedding rows: {empty_embeddings}",
    )

    failed = [check["name"] for check in checks if not check["success"]]
    report = {
        "report_name": report_name,
        "success": len(failed) == 0,
        "failed_checks": failed,
        "row_count": row_count,
        "checks": checks,
    }
    write_json(settings.paths.quality_dir / f"{report_name}.json", report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tong hop freshness report."""
    if df.empty or "published" not in df.columns:
        payload = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": int(len(df)),
            "freshness_threshold_days": settings.freshness_threshold_days,
            "is_fresh": False,
        }
        write_json(report_path, payload)
        return payload

    published = pd.to_datetime(df["published"], errors="coerce", utc=True)
    latest = published.max()
    oldest = published.min()
    if "age_days" in df.columns:
        stale_rows = int((df["age_days"].fillna(10**9) > settings.freshness_threshold_days).sum())
    else:
        stale_rows = int(len(df))

    payload = {
        "latest_published": None if pd.isna(latest) else latest.date().isoformat(),
        "oldest_published": None if pd.isna(oldest) else oldest.date().isoformat(),
        "stale_rows": stale_rows,
        "total_rows": int(len(df)),
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": stale_rows == 0 and int(len(df)) > 0,
    }
    write_json(report_path, payload)
    return payload
