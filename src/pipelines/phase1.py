from __future__ import annotations

from core.config import load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Baseline pipeline end-to-end."""
    settings = load_settings()
    require_llm_credentials(settings)
    paths = settings.paths

    raw_path = paths.raw_records_json
    if raw_path.exists() and not settings.refresh_source:
        records = load_raw_records(raw_path)
    else:
        records = fetch_source_records(settings)

    clean_df = build_clean_dataframe(records, run_date=now_utc())
    if clean_df.empty:
        raise RuntimeError("Cleaning produced an empty dataframe. Check source records and filters.")

    write_csv(clean_df, paths.clean_csv)
    write_json(paths.clean_json, clean_df.to_dict(orient="records"))

    index = LocalEmbeddingIndex.build(clean_df, settings=settings, embeddings_output_path=paths.embeddings_json)

    if paths.eval_testset.exists() and not settings.refresh_test_set:
        test_set = read_json(paths.eval_testset)
    else:
        test_set = build_test_set(clean_df, paths.eval_testset)

    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.baseline_metrics,
        answers_output_path=paths.baseline_answers,
    )

    quality = run_data_quality_checks(clean_df, settings=settings, report_name="baseline_quality")
    freshness = build_freshness_report(clean_df, settings=settings, report_path=paths.freshness_report)

    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_record_count": len(records),
        "clean_record_count": int(len(clean_df)),
        "embedding_model": settings.embedding_model,
        "collection_name": settings.baseline_collection_name,
        "test_set_size": len(test_set),
    }
    generate_phase1_report(
        report_path=paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    # Lightweight agent smoke demo on a few questions.
    demo_answers = []
    try:
        agent = build_agent(settings=settings, index=index)
        demo_questions = [item["question"] for item in test_set[:3]]
        for question in demo_questions:
            try:
                demo_answers.append({"question": question, "answer": run_agent_question(agent, question)})
            except Exception as exc:  # pragma: no cover
                demo_answers.append({"question": question, "answer": "", "error": str(exc)})
    except Exception as exc:  # pragma: no cover
        demo_answers = [{"error": f"Agent demo skipped: {exc}"}]
    write_json(paths.demo_answers, demo_answers)

    print("Phase 1 baseline completed.")
    print(f"Clean records: {len(clean_df)}")
    print(f"Metrics: {paths.baseline_metrics}")
    print(f"Report: {paths.baseline_report}")


if __name__ == "__main__":
    main()
