from __future__ import annotations

from typing import Any

from core.utils import write_text


def _metric_line(metrics: dict[str, Any]) -> str:
    return (
        f"- retrieval_hit_rate: {metrics.get('retrieval_hit_rate')}\n"
        f"- mean_token_f1: {metrics.get('mean_token_f1')}\n"
        f"- judge_accuracy: {metrics.get('judge_accuracy')}\n"
        f"- mean_judge_score: {metrics.get('mean_judge_score')}\n"
        f"- samples: {metrics.get('samples')}"
    )


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viet markdown report cho baseline phase."""
    failed = ", ".join(quality.get("failed_checks") or []) or "none"
    content = f"""# Phase 1 Baseline Report

## Source summary

- Source API: {source_summary.get('source_api')}
- Query: {source_summary.get('source_query')}
- Filter: {source_summary.get('source_filter')}
- Raw records: {source_summary.get('raw_record_count')}
- Clean records: {source_summary.get('clean_record_count')}
- Embedding model: {source_summary.get('embedding_model')}
- Collection: {source_summary.get('collection_name')}

## Evaluation metrics

{_metric_line(metrics)}

## Data quality

- Overall success: {quality.get('success')}
- Failed checks: {failed}
- Row count: {quality.get('row_count')}

## Freshness

- Latest published: {freshness.get('latest_published')}
- Oldest published: {freshness.get('oldest_published')}
- Stale rows: {freshness.get('stale_rows')} / {freshness.get('total_rows')}
- Threshold days: {freshness.get('freshness_threshold_days')}
- Is fresh: {freshness.get('is_fresh')}
"""
    write_text(report_path, content.strip() + "\n")


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
    """Viet markdown report so sanh baseline/corrupted/repaired."""

    def delta(before: Any, after: Any) -> str:
        try:
            return f"{float(after) - float(before):+.4f}"
        except (TypeError, ValueError):
            return "n/a"

    content = f"""# Corruption Comparison Report

## Metrics comparison

| Metric | Baseline | Corrupted | Repaired | Delta corrupted | Delta repaired |
| --- | ---: | ---: | ---: | ---: | ---: |
| retrieval_hit_rate | {baseline_metrics.get('retrieval_hit_rate')} | {corrupted_metrics.get('retrieval_hit_rate')} | {repaired_metrics.get('retrieval_hit_rate')} | {delta(baseline_metrics.get('retrieval_hit_rate'), corrupted_metrics.get('retrieval_hit_rate'))} | {delta(baseline_metrics.get('retrieval_hit_rate'), repaired_metrics.get('retrieval_hit_rate'))} |
| mean_token_f1 | {baseline_metrics.get('mean_token_f1')} | {corrupted_metrics.get('mean_token_f1')} | {repaired_metrics.get('mean_token_f1')} | {delta(baseline_metrics.get('mean_token_f1'), corrupted_metrics.get('mean_token_f1'))} | {delta(baseline_metrics.get('mean_token_f1'), repaired_metrics.get('mean_token_f1'))} |
| judge_accuracy | {baseline_metrics.get('judge_accuracy')} | {corrupted_metrics.get('judge_accuracy')} | {repaired_metrics.get('judge_accuracy')} | {delta(baseline_metrics.get('judge_accuracy'), corrupted_metrics.get('judge_accuracy'))} | {delta(baseline_metrics.get('judge_accuracy'), repaired_metrics.get('judge_accuracy'))} |
| mean_judge_score | {baseline_metrics.get('mean_judge_score')} | {corrupted_metrics.get('mean_judge_score')} | {repaired_metrics.get('mean_judge_score')} | {delta(baseline_metrics.get('mean_judge_score'), corrupted_metrics.get('mean_judge_score'))} | {delta(baseline_metrics.get('mean_judge_score'), repaired_metrics.get('mean_judge_score'))} |

## Data quality

- Corrupted success: {corrupted_quality.get('success')} (failed: {', '.join(corrupted_quality.get('failed_checks') or []) or 'none'})
- Repaired success: {repaired_quality.get('success')} (failed: {', '.join(repaired_quality.get('failed_checks') or []) or 'none'})

## Freshness

- Corrupted stale rows: {corrupted_freshness.get('stale_rows')} / {corrupted_freshness.get('total_rows')} (is_fresh={corrupted_freshness.get('is_fresh')})
- Repaired stale rows: {repaired_freshness.get('stale_rows')} / {repaired_freshness.get('total_rows')} (is_fresh={repaired_freshness.get('is_fresh')})

## Interpretation

- Corruption is expected to reduce retrieval/answer quality and increase quality/freshness failures.
- Repair from raw source should restore metrics closer to the baseline and clear intentional data defects.
"""
    write_text(report_path, content.strip() + "\n")
