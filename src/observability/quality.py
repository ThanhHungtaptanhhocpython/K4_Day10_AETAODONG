from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import now_utc, write_json

MIN_ROWS = 5
MIN_SUMMARY_CHARS = 100


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"check": name, "success": bool(passed), **details}


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run a battery of data-quality expectations over the cleaned dataframe.

    Each check reports a boolean ``success`` plus supporting numbers. The whole
    report is written to ``data/quality/<report_name>.json`` and returned.
    """
    total_rows = int(len(df))
    checks: list[dict[str, Any]] = []

    # 1. Row count.
    checks.append(
        _check(
            "row_count",
            total_rows >= MIN_ROWS,
            {"rows": total_rows, "min_rows": MIN_ROWS},
        )
    )

    # 2. paper_id not null and unique.
    if total_rows and "paper_id" in df:
        null_ids = int(df["paper_id"].isna().sum() + (df["paper_id"].astype(str).str.strip() == "").sum())
        duplicate_ids = int(df["paper_id"].duplicated().sum())
    else:
        null_ids = total_rows
        duplicate_ids = 0
    checks.append(
        _check(
            "paper_id_not_null",
            null_ids == 0,
            {"null_paper_ids": null_ids},
        )
    )
    checks.append(
        _check(
            "paper_id_unique",
            duplicate_ids == 0,
            {"duplicate_paper_ids": duplicate_ids},
        )
    )

    # 3. title not null.
    if total_rows and "title" in df:
        null_titles = int(df["title"].isna().sum() + (df["title"].astype(str).str.strip() == "").sum())
    else:
        null_titles = total_rows
    checks.append(
        _check(
            "title_not_null",
            null_titles == 0,
            {"null_titles": null_titles},
        )
    )

    # 4. summary length.
    if total_rows and "summary" in df:
        short_summaries = int((df["summary"].astype(str).str.len() < MIN_SUMMARY_CHARS).sum())
    else:
        short_summaries = total_rows
    checks.append(
        _check(
            "summary_min_length",
            short_summaries == 0,
            {"short_summaries": short_summaries, "min_chars": MIN_SUMMARY_CHARS},
        )
    )

    # 5. freshness via age_days.
    threshold = settings.freshness_threshold_days
    if total_rows and "age_days" in df:
        stale_rows = int((df["age_days"] > threshold).sum())
    else:
        stale_rows = total_rows
    checks.append(
        _check(
            "freshness_age_days",
            stale_rows == 0,
            {"stale_rows": stale_rows, "threshold_days": threshold},
        )
    )

    passed = sum(1 for c in checks if c["success"])
    report = {
        "report_name": report_name,
        "generated_at": now_utc().isoformat(),
        "total_rows": total_rows,
        "checks_total": len(checks),
        "checks_passed": passed,
        "checks_failed": len(checks) - passed,
        "success": passed == len(checks),
        "checks": checks,
    }

    output_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(output_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarize dataset freshness (latest/oldest published, stale count)."""
    threshold = settings.freshness_threshold_days
    total_rows = int(len(df))

    if total_rows and "published" in df:
        published = pd.to_datetime(df["published"], errors="coerce")
        published = published.dropna()
        latest = published.max()
        oldest = published.min()
        latest_published = latest.date().isoformat() if pd.notna(latest) else None
        oldest_published = oldest.date().isoformat() if pd.notna(oldest) else None
    else:
        latest_published = None
        oldest_published = None

    stale_rows = int((df["age_days"] > threshold).sum()) if total_rows and "age_days" in df else total_rows
    max_age = int(df["age_days"].max()) if total_rows and "age_days" in df else None

    payload = {
        "generated_at": now_utc().isoformat(),
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "threshold_days": threshold,
        "max_age_days": max_age,
        "is_fresh": total_rows > 0 and stale_rows == 0,
    }
    write_json(report_path, payload)
    return payload
