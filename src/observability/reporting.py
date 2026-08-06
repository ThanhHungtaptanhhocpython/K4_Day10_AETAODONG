from __future__ import annotations

from typing import Any

from core.utils import now_utc, write_text


def _fmt(value: Any, digits: int = 4) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}" if isinstance(value, float) else str(value)
    return str(value)


def _quality_lines(quality: dict[str, Any]) -> list[str]:
    lines = [
        f"- Overall: **{'PASS' if quality.get('success') else 'FAIL'}** "
        f"({quality.get('checks_passed', 0)}/{quality.get('checks_total', 0)} checks passed)",
        "",
        "| Check | Result | Details |",
        "| --- | --- | --- |",
    ]
    for check in quality.get("checks", []):
        details = {k: v for k, v in check.items() if k not in {"check", "success"}}
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        result = "PASS" if check.get("success") else "FAIL"
        lines.append(f"| {check.get('check')} | {result} | {detail_str} |")
    return lines


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a markdown baseline report covering source, metrics, quality, freshness."""
    lines: list[str] = []
    lines.append("# Phase 1 - Baseline Report")
    lines.append("")
    lines.append(f"_Generated at {now_utc().isoformat()}_")
    lines.append("")

    lines.append("## Data Source")
    lines.append("")
    for key, value in source_summary.items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")

    lines.append("## Evaluation Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    for key in ("samples", "retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        if key in metrics:
            lines.append(f"| {key} | {_fmt(metrics[key])} |")
    ragas = metrics.get("ragas")
    if isinstance(ragas, dict) and "skipped" not in ragas and "error" not in ragas:
        for key, value in ragas.items():
            lines.append(f"| ragas.{key} | {_fmt(value)} |")
    lines.append("")

    lines.append("## Data Quality")
    lines.append("")
    lines.extend(_quality_lines(quality))
    lines.append("")

    lines.append("## Freshness")
    lines.append("")
    lines.append(f"- Status: **{'FRESH' if freshness.get('is_fresh') else 'STALE'}**")
    lines.append(f"- Latest published: {freshness.get('latest_published')}")
    lines.append(f"- Oldest published: {freshness.get('oldest_published')}")
    lines.append(
        f"- Stale rows: {freshness.get('stale_rows')} / {freshness.get('total_rows')} "
        f"(threshold {freshness.get('threshold_days')} days)"
    )
    lines.append(f"- Max age (days): {freshness.get('max_age_days')}")
    lines.append("")

    write_text(report_path, "\n".join(lines) + "\n")


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
    """Write a markdown report comparing baseline / corrupted / repaired states."""

    def metric_row(name: str, key: str) -> str:
        b = baseline_metrics.get(key)
        c = corrupted_metrics.get(key)
        r = repaired_metrics.get(key)
        delta_corrupt = (c - b) if isinstance(b, (int, float)) and isinstance(c, (int, float)) else None
        recovery = (r - c) if isinstance(c, (int, float)) and isinstance(r, (int, float)) else None
        dc = f"{delta_corrupt:+.4f}" if delta_corrupt is not None else "-"
        rc = f"{recovery:+.4f}" if recovery is not None else "-"
        return f"| {name} | {_fmt(b)} | {_fmt(c)} | {_fmt(r)} | {dc} | {rc} |"

    lines: list[str] = []
    lines.append("# Phase 2 - Corruption / Repair Comparison Report")
    lines.append("")
    lines.append(f"_Generated at {now_utc().isoformat()}_")
    lines.append("")
    lines.append(
        "So sanh ba trang thai tren **cung mot frozen test set**. "
        "`Δ corruption` = corrupted − baseline; `Δ recovery` = repaired − corrupted."
    )
    lines.append("")

    lines.append("## Metrics")
    lines.append("")
    lines.append("| Metric | Baseline | Corrupted | Repaired | Δ corruption | Δ recovery |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    lines.append(metric_row("retrieval_hit_rate", "retrieval_hit_rate"))
    lines.append(metric_row("mean_token_f1", "mean_token_f1"))
    lines.append(metric_row("judge_accuracy", "judge_accuracy"))
    lines.append(metric_row("mean_judge_score", "mean_judge_score"))
    lines.append("")

    lines.append("## Data Quality & Freshness")
    lines.append("")
    lines.append("| Signal | Corrupted | Repaired |")
    lines.append("| --- | --- | --- |")
    lines.append(
        f"| Quality checks | {'PASS' if corrupted_quality.get('success') else 'FAIL'} "
        f"({corrupted_quality.get('checks_passed', 0)}/{corrupted_quality.get('checks_total', 0)}) "
        f"| {'PASS' if repaired_quality.get('success') else 'FAIL'} "
        f"({repaired_quality.get('checks_passed', 0)}/{repaired_quality.get('checks_total', 0)}) |"
    )
    lines.append(
        f"| Freshness | {'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE'} "
        f"(stale {corrupted_freshness.get('stale_rows')}/{corrupted_freshness.get('total_rows')}) "
        f"| {'FRESH' if repaired_freshness.get('is_fresh') else 'STALE'} "
        f"(stale {repaired_freshness.get('stale_rows')}/{repaired_freshness.get('total_rows')}) |"
    )
    lines.append("")

    lines.append("## Failed Quality Checks (Corrupted)")
    lines.append("")
    failed = [c for c in corrupted_quality.get("checks", []) if not c.get("success")]
    if failed:
        lines.append("| Check | Details |")
        lines.append("| --- | --- |")
        for check in failed:
            details = {k: v for k, v in check.items() if k not in {"check", "success"}}
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            lines.append(f"| {check.get('check')} | {detail_str} |")
    else:
        lines.append("_Khong co check nao fail o trang thai corrupted._")
    lines.append("")

    lines.append("## Conclusion")
    lines.append("")
    lines.append(
        "- **Corruption → impact:** so sanh cot `Δ corruption`; gia tri am cho thay "
        "data xau lam giam chat luong agent va/hoac quality/freshness."
    )
    lines.append(
        "- **Repair → recovery:** so sanh cot `Δ recovery`; gia tri duong cho thay "
        "repair tu raw source phuc hoi lai chat luong. Repaired duoc tao bang cach "
        "re-run cleaning tu `data/raw/`, khong sua tay ket qua."
    )
    lines.append("")

    write_text(report_path, "\n".join(lines) + "\n")
