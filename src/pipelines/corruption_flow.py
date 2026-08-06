from __future__ import annotations

from datetime import datetime

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def _load_clean_dataframe(settings):
    """Doc clean dataset baseline tu JSON snapshot thanh dataframe."""
    import pandas as pd

    rows = read_json(settings.paths.clean_json)
    return pd.DataFrame(rows)


def _test_set_paper_ids(settings) -> list[str]:
    """Lay danh sach paper_id xuat hien trong frozen test set."""
    test_set = read_json(settings.paths.eval_testset)
    ids: list[str] = []
    for item in test_set:
        for pid in item.get("ground_truth_doc_ids", []):
            if pid not in ids:
                ids.append(pid)
    return ids


def _evaluate_state(settings, df, embeddings_path, metrics_path, answers_path, quality_name, freshness_path):
    """Rebuild index tu df, evaluate tren frozen test set, chay quality/freshness."""
    index = LocalEmbeddingIndex.build(df, settings, embeddings_path)
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=metrics_path,
        answers_output_path=answers_path,
    )
    quality = run_data_quality_checks(df, settings, report_name=quality_name)
    freshness = build_freshness_report(df, settings, freshness_path)
    return bundle.summary, quality, freshness


def main() -> None:
    """Corruption -> evaluate -> repair -> compare flow (Pha 2)."""
    settings = load_settings()
    paths = settings.paths

    # 0. Yeu cau baseline da chay xong.
    if not paths.baseline_metrics.exists() or not paths.clean_json.exists():
        raise RuntimeError(
            "Baseline artifacts missing. Run script/run_phase1.py truoc khi chay corruption flow."
        )
    baseline_metrics = read_json(paths.baseline_metrics)

    # 1. Load clean baseline + xac dinh target paper_id nam trong frozen test set.
    clean_df = _load_clean_dataframe(settings)
    target_ids = _test_set_paper_ids(settings)
    print(f"[corruption] Baseline clean rows: {len(clean_df)} | test-set papers: {len(target_ids)}")

    # 2. Tao corrupted dataframe (dam bao dung trung test-set papers).
    corrupted_df = corrupt_clean_dataframe(clean_df, paths.corruption_log, target_paper_ids=target_ids)
    freshness_cols = ["authors", "categories"]
    write_csv(corrupted_df.drop(columns=freshness_cols, errors="ignore"), paths.corrupted_clean_csv)
    write_json(paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    print(f"[corruption] Corrupted rows: {len(corrupted_df)} -> {paths.corrupted_clean_csv}")

    # 3. Rebuild index + evaluate corrupted state.
    print("[corruption] Evaluating CORRUPTED state...")
    corrupted_metrics, corrupted_quality, corrupted_freshness = _evaluate_state(
        settings,
        corrupted_df,
        paths.corrupted_embeddings_json,
        paths.corrupted_metrics,
        paths.corrupted_answers,
        "corrupted_quality",
        paths.freshness_report.parent / "freshness_report_corrupted.json",
    )

    # 4. REPAIR: chay lai cleaning tu raw records (nguon dang tin cay), khong sua tay.
    print("[repair] Rebuilding clean data from raw records...")
    raw_records = load_raw_records(paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=now_utc())
    write_csv(repaired_df.drop(columns=freshness_cols, errors="ignore"), paths.repaired_clean_csv)
    write_json(paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"[repair] Repaired rows: {len(repaired_df)} -> {paths.repaired_clean_csv}")

    # 5. Rebuild index + evaluate repaired state.
    print("[repair] Evaluating REPAIRED state...")
    repaired_metrics, repaired_quality, repaired_freshness = _evaluate_state(
        settings,
        repaired_df,
        paths.repaired_embeddings_json,
        paths.repaired_metrics,
        paths.repaired_answers,
        "repaired_quality",
        paths.freshness_report.parent / "freshness_report_repaired.json",
    )

    # 6. Comparison report doi chieu ba trang thai.
    generate_corruption_report(
        report_path=paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"[compare] Comparison report -> {paths.comparison_report}")

    # Console summary 3 trang thai.
    def _row(label, m, q, f):
        return (
            f"  {label:10s} hit={m['retrieval_hit_rate']:.3f} f1={m['mean_token_f1']:.3f} "
            f"judge={m['mean_judge_score']:.2f} quality={'PASS' if q['success'] else 'FAIL'} "
            f"fresh={'FRESH' if f['is_fresh'] else 'STALE'}"
        )

    print("\n[compare] Three-state comparison:")
    # Baseline quality/freshness khong load lai o day; chi in metrics baseline.
    print(
        f"  {'baseline':10s} hit={baseline_metrics['retrieval_hit_rate']:.3f} "
        f"f1={baseline_metrics['mean_token_f1']:.3f} judge={baseline_metrics['mean_judge_score']:.2f}"
    )
    print(_row("corrupted", corrupted_metrics, corrupted_quality, corrupted_freshness))
    print(_row("repaired", repaired_metrics, repaired_quality, repaired_freshness))


if __name__ == "__main__":
    main()
