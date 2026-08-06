from __future__ import annotations


import json
from datetime import datetime, UTC

from core.config import load_settings
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.testset import build_test_set
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_phase1_report

def main() -> None:
    settings = load_settings()
    run_date = datetime.now(UTC)
    
    print("1. Loading or fetching raw records...")
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)
        
    source_summary = {
        "fetched": len(records),
        "clean": 0
    }
        
    print("2. Cleaning data...")
    df = build_clean_dataframe(records, run_date)
    source_summary["clean"] = len(df)
    
    print("3. Saving clean CSV/JSON...")
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    df.to_json(settings.paths.clean_json, orient="records", indent=2, force_ascii=False)
    
    print("4. Building Chroma index...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    
    print("5. Generating/loading evaluation set...")
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(df, settings.paths.eval_testset)
            
    print("6. Evaluating...")
    metrics_bundle = evaluate_pipeline(
        settings, 
        index, 
        settings.paths.eval_testset, 
        settings.paths.baseline_metrics, 
        settings.paths.baseline_answers
    )
    
    print("7. Running quality checks and freshness report...")
    quality = run_data_quality_checks(df, settings, "baseline_quality")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    
    print("8. Generating phase 1 report...")
    generate_phase1_report(settings.paths.baseline_report, source_summary, metrics_bundle.summary, quality, freshness)
    
    print("Phase 1 complete! Report generated at:", settings.paths.baseline_report)
