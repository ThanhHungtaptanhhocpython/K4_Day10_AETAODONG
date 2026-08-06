import pandas as pd
from datetime import datetime, UTC
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import PaperRecord

def test_build_clean_dataframe():
    raw_records = [
        PaperRecord(
            paper_id="1",
            title="<html>Test Title</html>",
            summary="<p>Test Abstract with more than 20 characters.</p>",
            published="2024-01-01",
            abs_url="http://example.com/abs/1",
            pdf_url="http://example.com/pdf/1",
            authors=["Author 1"],
            categories=["cs.AI"],
            primary_category="cs.AI",
            updated="2024-01-02",
            comment=""
        )
    ]
    
    run_date = datetime(2024, 1, 10, tzinfo=UTC)
    df = build_clean_dataframe(raw_records, run_date)
    
    assert len(df) == 1
    assert df.loc[0, "paper_id"] == "1"
    assert df.loc[0, "title"] == "Test Title"
    assert df.loc[0, "summary"] == "Test Abstract with more than 20 characters."
    assert df.loc[0, "age_days"] == 9
    assert "Title: Test Title" in df.loc[0, "text_for_embedding"]

