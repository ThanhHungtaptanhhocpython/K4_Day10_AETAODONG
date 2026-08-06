import pandas as pd
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))
from observability.quality import run_data_quality_checks
from core.config import load_settings

def test_run_data_quality_checks_pass():
    settings = load_settings()
    df = pd.DataFrame([
        {"paper_id": "1", "title": "A Title", "summary": "A valid summary with enough words to pass the test.", "age_days": 10},
        {"paper_id": "2", "title": "B Title", "summary": "Another valid summary with enough words to pass the test.", "age_days": 10}
    ])
    
    quality = run_data_quality_checks(df, settings, "test_quality")
    assert quality["passed"] is True
    assert quality["null_paper_ids"] == 0
    assert quality["duplicate_paper_ids"] == 0
    assert quality["empty_titles"] == 0
    assert quality["short_summaries"] == 0

def test_run_data_quality_checks_fail_short_summary():
    settings = load_settings()
    df = pd.DataFrame([
        {"paper_id": "1", "title": "A Title", "summary": "Short", "age_days": 10}
    ])
    
    quality = run_data_quality_checks(df, settings, "test_quality_fail")
    assert quality["passed"] is True
    assert quality["short_summaries"] == 1
