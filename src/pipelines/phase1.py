from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def _load_or_fetch_records(settings):
    raw_path = settings.paths.raw_records_json
    if settings.refresh_source or not raw_path.exists():
        print("[phase1] Fetching records from Crossref...")
        return fetch_source_records(settings)
    print(f"[phase1] Loading cached raw records from {raw_path}")
    return load_raw_records(raw_path)


def _load_or_build_test_set(df, settings):
    test_path = settings.paths.eval_testset
    if settings.refresh_test_set or not test_path.exists():
        print("[phase1] Building evaluation test set...")
        return build_test_set(df, test_path)
    print(f"[phase1] Reusing existing test set at {test_path}")
    from core.utils import read_json

    return read_json(test_path)


def main() -> None:
    """Run the baseline phase-1 pipeline end-to-end on clean data."""
    settings = load_settings()

    # 1-2. Load or fetch raw records.
    records = _load_or_fetch_records(settings)
    print(f"[phase1] {len(records)} raw records available.")

    # 3-4. Clean and persist.
    df = build_clean_dataframe(records, run_date=now_utc())
    if df.empty:
        raise RuntimeError("Cleaned dataframe is empty; check ingestion/cleaning steps.")
    write_csv(df.drop(columns=["authors", "categories"], errors="ignore"), settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))
    print(f"[phase1] Cleaned {len(df)} papers -> {settings.paths.clean_csv}")

    # 5. Build the Chroma embedding index.
    print("[phase1] Building embedding index (ChromaDB)...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)

    # 6. Build or load the evaluation set.
    test_set = _load_or_build_test_set(df, settings)
    print(f"[phase1] Evaluation set has {len(test_set)} questions.")

    # 7. Evaluate the pipeline.
    print("[phase1] Evaluating pipeline...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # 8. Data quality + freshness.
    print("[phase1] Running data quality checks and freshness report...")
    quality = run_data_quality_checks(df, settings, report_name="baseline_quality")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)

    # 9. Markdown report.
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "records_fetched": len(records),
        "records_clean": int(len(df)),
        "embedding_model": settings.embedding_model,
        "collection": settings.baseline_collection_name,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"[phase1] Report written to {settings.paths.baseline_report}")

    # 10. Small agent demo on a couple of sample questions.
    demo = []
    for item in test_set[:3]:
        result = answer_question(item["question"], settings=settings, index=index)
        demo.append(
            {
                "question": item["question"],
                "answer": result.answer,
                "retrieved_doc_ids": result.retrieved_doc_ids,
            }
        )
    write_json(settings.paths.demo_answers, demo)

    # Console summary.
    print("\n[phase1] Baseline metrics:")
    for key in ("samples", "retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        if key in bundle.summary:
            print(f"  - {key}: {bundle.summary[key]}")
    print(f"[phase1] Data quality: {'PASS' if quality['success'] else 'FAIL'}")
    print(f"[phase1] Freshness: {'FRESH' if freshness['is_fresh'] else 'STALE'}")


if __name__ == "__main__":
    main()
