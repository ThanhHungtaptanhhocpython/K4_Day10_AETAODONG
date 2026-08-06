from __future__ import annotations

from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    content = f"""# Phase 1: Baseline Pipeline Report

## Source Summary
- Provider: Crossref
- Total Records Fetched: {source_summary.get('fetched', 0)}
- Clean Records: {source_summary.get('clean', 0)}

## Evaluation Metrics
- Hit Rate: {metrics.get('retrieval_hit_rate', 0):.4f}
- Token F1: {metrics.get('mean_token_f1', 0):.4f}
- Judge Accuracy: {metrics.get('judge_accuracy', 0):.4f}
- Mean Judge Score: {metrics.get('mean_judge_score', 0):.4f}

## Data Quality
- Passed: {quality.get('passed', False)}
- Row Count: {quality.get('row_count', 0)}
- Null Paper IDs: {quality.get('null_paper_ids', 0)}
- Duplicate Paper IDs: {quality.get('duplicate_paper_ids', 0)}
- Empty Titles: {quality.get('empty_titles', 0)}
- Short Summaries: {quality.get('short_summaries', 0)}

## Data Freshness
- Is Fresh: {freshness.get('is_fresh', False)}
- Oldest Published: {freshness.get('oldest_published', '')}
- Latest Published: {freshness.get('latest_published', '')}
- Stale Rows: {freshness.get('stale_rows', 0)}
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    content = f"""# Phase 2: Corruption and Repair Comparison Report

## Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| Hit Rate | {baseline_metrics.get('retrieval_hit_rate', 0):.4f} | {corrupted_metrics.get('retrieval_hit_rate', 0):.4f} | {repaired_metrics.get('retrieval_hit_rate', 0):.4f} |
| Token F1 | {baseline_metrics.get('mean_token_f1', 0):.4f} | {corrupted_metrics.get('mean_token_f1', 0):.4f} | {repaired_metrics.get('mean_token_f1', 0):.4f} |
| Judge Accuracy | {baseline_metrics.get('judge_accuracy', 0):.4f} | {corrupted_metrics.get('judge_accuracy', 0):.4f} | {repaired_metrics.get('judge_accuracy', 0):.4f} |
| Mean Judge Score | {baseline_metrics.get('mean_judge_score', 0):.4f} | {corrupted_metrics.get('mean_judge_score', 0):.4f} | {repaired_metrics.get('mean_judge_score', 0):.4f} |

## Quality & Freshness (Corrupted)
- Quality Passed: {corrupted_quality.get('passed', False)} (Short summaries: {corrupted_quality.get('short_summaries', 0)}, Empty titles: {corrupted_quality.get('empty_titles', 0)}, Duplicates: {corrupted_quality.get('duplicate_paper_ids', 0)})
- Is Fresh: {corrupted_freshness.get('is_fresh', False)} (Stale rows: {corrupted_freshness.get('stale_rows', 0)})

## Quality & Freshness (Repaired)
- Quality Passed: {repaired_quality.get('passed', False)} (Short summaries: {repaired_quality.get('short_summaries', 0)}, Empty titles: {repaired_quality.get('empty_titles', 0)}, Duplicates: {repaired_quality.get('duplicate_paper_ids', 0)})
- Is Fresh: {repaired_freshness.get('is_fresh', False)} (Stale rows: {repaired_freshness.get('stale_rows', 0)})
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
