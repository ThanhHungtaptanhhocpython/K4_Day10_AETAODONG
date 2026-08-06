from __future__ import annotations


import json
import pandas as pd
from datetime import datetime, UTC

from core.config import load_settings
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report

def main() -> None:
    settings = load_settings()
    run_date = datetime.now(UTC)
    
    print("1. Loading baseline metrics and clean dataset...")
    with open(settings.paths.baseline_metrics, "r", encoding="utf-8") as f:
        baseline_metrics = json.load(f)
    df = pd.read_csv(settings.paths.clean_csv)
    
    print("2. Creating corrupted dataframe...")
    corrupted_df = corrupt_clean_dataframe(df, settings.paths.corruption_log)
    
    print("3. Saving corrupted artifacts...")
    settings.paths.corrupted_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    corrupted_df.to_csv(settings.paths.corrupted_clean_csv, index=False)
    corrupted_df.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2, force_ascii=False)
    
    print("4. Rebuilding index and evaluating (Corrupted)...")
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    corrupted_bundle = evaluate_pipeline(
        settings, 
        corrupted_index, 
        settings.paths.eval_testset, 
        settings.paths.corrupted_metrics, 
        settings.paths.corrupted_answers
    )
    
    print("5. Running quality checks/freshness on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted_quality")
    corrupted_freshness = build_freshness_report(corrupted_df, settings, settings.paths.quality_dir / "corrupted_freshness_report.json")
    
    print("6. Repairing from raw records...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date)
    settings.paths.repaired_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    repaired_df.to_csv(settings.paths.repaired_clean_csv, index=False)
    repaired_df.to_json(settings.paths.repaired_clean_json, orient="records", indent=2, force_ascii=False)
    
    print("7. Rebuilding index and evaluating (Repaired)...")
    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)
    repaired_bundle = evaluate_pipeline(
        settings, 
        repaired_index, 
        settings.paths.eval_testset, 
        settings.paths.repaired_metrics, 
        settings.paths.repaired_answers
    )
    
    print("8. Running quality checks/freshness on repaired data...")
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired_quality")
    repaired_freshness = build_freshness_report(repaired_df, settings, settings.paths.quality_dir / "repaired_freshness_report.json")
    
    print("9. Generating comparison report...")
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_bundle.summary,
        repaired_bundle.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness
    )
    
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent / "script"))
    try:
        from visualize import visualize_metrics
        print("10. Generating metrics chart...")
        visualize_metrics()
    except Exception as e:
        print(f"Failed to generate metrics chart: {e}")
        
    print("Phase 2 complete! Comparison report generated at:", settings.paths.comparison_report)
