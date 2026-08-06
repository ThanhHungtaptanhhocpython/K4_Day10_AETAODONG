import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from core.config import load_settings

def visualize_metrics():
    settings = load_settings()
    
    # Load metrics
    try:
        with open(settings.paths.baseline_metrics, "r") as f:
            baseline = json.load(f)
        with open(settings.paths.corrupted_metrics, "r") as f:
            corrupted = json.load(f)
        with open(settings.paths.repaired_metrics, "r") as f:
            repaired = json.load(f)
    except FileNotFoundError:
        print("Metrics files not found. Please run corruption_flow.py first.")
        return

    metrics_to_plot = ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy"]
    labels = ["Hit Rate", "Token F1", "Judge Accuracy"]
    
    baseline_vals = [baseline.get(m, 0) for m in metrics_to_plot]
    corrupted_vals = [corrupted.get(m, 0) for m in metrics_to_plot]
    repaired_vals = [repaired.get(m, 0) for m in metrics_to_plot]
    
    x = np.arange(len(labels))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    rects1 = ax.bar(x - width, baseline_vals, width, label='Baseline', color='#2ca02c')
    rects2 = ax.bar(x, corrupted_vals, width, label='Corrupted', color='#d62728')
    rects3 = ax.bar(x + width, repaired_vals, width, label='Repaired', color='#1f77b4')
    
    ax.set_ylabel('Scores (0-1)')
    ax.set_title('RAG Evaluation Metrics Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.1)
    ax.legend(loc='upper right')
    
    # Add values on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
                        
    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    
    fig.tight_layout()
    
    output_path = settings.paths.comparison_report.parent / "metrics_chart.png"
    plt.savefig(output_path, dpi=300)
    print(f"Chart saved to {output_path}")

if __name__ == "__main__":
    visualize_metrics()
