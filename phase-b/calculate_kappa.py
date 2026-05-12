import os
import sys
import json
import numpy as np
from sklearn.metrics import cohen_kappa_score

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

sys.stdout.reconfigure(encoding='utf-8')

def interpret_kappa(kappa: float) -> str:
    if kappa <= 0:
        return "No Agreement (Đồng thuận Ngẫu nhiên/Kém)"
    elif kappa <= 0.2:
        return "Slight Agreement (Đồng thuận Rất thấp)"
    elif kappa <= 0.4:
        return "Fair Agreement (Đồng thuận Trung bình thấp)"
    elif kappa <= 0.6:
        return "Moderate Agreement (Đồng thuận Trung bình)"
    elif kappa <= 0.8:
        return "Substantial Agreement (Đồng thuận Cao)"
    else:
        return "Almost Perfect Agreement (Đồng thuận Tuyệt đối)"

def main():
    print(" CALIBRATION STATS: COHEN'S KAPPA")
    print("=" * 40)
    
    path = os.path.join(PROJECT_ROOT, "reports", "human_labels.json")
    
    if not os.path.exists(path):
        print(" Error: human_labels.json not found! Run human_cli.py first.")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not data:
        print(" Dataset is empty.")
        return

    y_llm = [item.get("llm_score") for item in data]
    y_human = [item.get("human_score") for item in data]

    print(f" Loaded {len(y_llm)} aligned samples.")
    print(f" LLM Scores   : {y_llm}")
    print(f" Human Scores : {y_human}")

    # Calculate kappa
    try:
        # Force labels list to represent entire Likert domain for robustness
        score = cohen_kappa_score(y_llm, y_human, labels=[1, 2, 3, 4, 5])
        print("\n" + "-"*40)
        print(f" COHEN'S KAPPA: {score:.4f}")
        print(f" Interpretation: {interpret_kappa(score)}")
        print("-" * 40)
    except Exception as e:
        print(f" Error computing metrics: {e}")

if __name__ == "__main__":
    main()
