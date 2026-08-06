import argparse
import sys
from pathlib import Path

# Add src to python path so we can import modules
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from pipelines.phase1 import main as run_phase1
from pipelines.corruption_flow import main as run_phase2

def main():
    parser = argparse.ArgumentParser(description="AITC Day 10 - Data Pipeline CLI")
    parser.add_argument(
        "--run", 
        type=str, 
        choices=["phase1", "phase2", "all"], 
        required=True,
        help="Chọn tiến trình để chạy: phase1 (Baseline), phase2 (Corruption) hoặc all."
    )
    
    args = parser.parse_args()
    
    if args.run in ["phase1", "all"]:
        print("\n" + "="*50)
        print("STARTING PHASE 1: BASELINE PIPELINE")
        print("="*50)
        run_phase1()
        
    if args.run in ["phase2", "all"]:
        print("\n" + "="*50)
        print("STARTING PHASE 2: CORRUPTION FLOW")
        print("="*50)
        run_phase2()

if __name__ == "__main__":
    main()
