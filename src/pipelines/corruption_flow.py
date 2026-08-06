from __future__ import annotations

import pandas as pd

from core.config import load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Corruption -> evaluate -> repair -> compare flow."""
    settings = load_settings()
    require_llm_credentials(settings)
    paths = settings.paths

    if not paths.baseline_metrics.exists():
        raise FileNotFoundError(
            f"Missing baseline metrics at {paths.baseline_metrics}. Run phase 1 first."
        )
    if not paths.clean_csv.exists():
        raise FileNotFoundError(f"Missing cleaned baseline CSV at {paths.clean_csv}. Run phase 1 first.")
    if not paths.eval_testset.exists():
        raise FileNotFoundError(f"Missing evaluation set at {paths.eval_testset}. Run phase 1 first.")
    if not paths.raw_records_json.exists():
        raise FileNotFoundError(f"Missing raw records at {paths.raw_records_json}. Run phase 1 first.")

    baseline_metrics = read_json(paths.baseline_metrics)
    baseline_df = pd.read_csv(paths.clean_csv).fillna("")

    corrupted_df = corrupt_clean_dataframe(baseline_df, paths.corruption_log)
    write_csv(corrupted_df, paths.corrupted_clean_csv)
    write_json(paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))

    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings=settings,
        embeddings_output_path=paths.corrupted_embeddings_json,
    )
    corrupted_eval = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.corrupted_metrics,
        answers_output_path=paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(
        corrupted_df,
        settings=settings,
        report_name="corrupted_quality",
    )
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings=settings,
        report_path=paths.quality_dir / "corrupted_freshness_report.json",
    )

    # Repair from the raw source snapshot, then clean again.
    raw_records = load_raw_records(paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=now_utc())
    write_csv(repaired_df, paths.repaired_clean_csv)
    write_json(paths.repaired_clean_json, repaired_df.to_dict(orient="records"))

    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings=settings,
        embeddings_output_path=paths.repaired_embeddings_json,
    )
    repaired_eval = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.repaired_metrics,
        answers_output_path=paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(
        repaired_df,
        settings=settings,
        report_name="repaired_quality",
    )
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings=settings,
        report_path=paths.quality_dir / "repaired_freshness_report.json",
    )

    generate_corruption_report(
        report_path=paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval.summary,
        repaired_metrics=repaired_eval.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    print("Corruption flow completed.")
    print(f"Corrupted metrics: {paths.corrupted_metrics}")
    print(f"Repaired metrics: {paths.repaired_metrics}")
    print(f"Comparison report: {paths.comparison_report}")


if __name__ == "__main__":
    main()
