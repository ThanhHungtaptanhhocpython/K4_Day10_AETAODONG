from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


import json

def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    row_count = len(df)
    
    if row_count > 0:
        null_paper_ids = df["paper_id"].isnull().sum()
        duplicate_paper_ids = df["paper_id"].duplicated().sum()
        null_titles = df["title"].isnull().sum()
        empty_titles = (df["title"].str.strip() == "").sum()
        short_summaries = (df["summary"].str.len() < 20).sum()
        stale_rows = (df["age_days"] > settings.freshness_threshold_days).sum()
    else:
        null_paper_ids = duplicate_paper_ids = null_titles = empty_titles = short_summaries = stale_rows = 0
    
    passed = True
    if row_count == 0 or null_paper_ids > 0 or duplicate_paper_ids > 0 or null_titles > 0 or empty_titles > 0:
        passed = False
        
    result = {
        "passed": passed,
        "row_count": int(row_count),
        "null_paper_ids": int(null_paper_ids),
        "duplicate_paper_ids": int(duplicate_paper_ids),
        "null_titles": int(null_titles),
        "empty_titles": int(empty_titles),
        "short_summaries": int(short_summaries),
        "stale_rows": int(stale_rows)
    }
    
    report_file = settings.paths.quality_dir / f"{report_name}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    return result


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    if df.empty:
        result = {
            "is_fresh": False,
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0
        }
    else:
        latest = df["published"].max()
        oldest = df["published"].min()
        stale_rows = (df["age_days"] > settings.freshness_threshold_days).sum()
        total_rows = len(df)
        is_fresh = stale_rows == 0
        
        result = {
            "is_fresh": bool(is_fresh),
            "latest_published": str(latest),
            "oldest_published": str(oldest),
            "stale_rows": int(stale_rows),
            "total_rows": int(total_rows)
        }
        
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    return result
