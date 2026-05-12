import os
import sys
import json
import random

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

sys.stdout.reconfigure(encoding='utf-8')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print(" RAG Human Labeling CLI Tool")
    print("-" * 40)
    
    source_path = os.path.join(PROJECT_ROOT, "reports", "absolute_scores.json")
    
    if not os.path.exists(source_path):
        print(" Pre-requisite missing: Run 'python phase-b/absolute_scorer.py' first to generate candidates.")
        return

    with open(source_path, 'r', encoding='utf-8') as f:
        all_samples = json.load(f)
        
    if len(all_samples) < 10:
        print(f"️ Only found {len(all_samples)} samples. Using all of them.")
        selected = all_samples
    else:
        # Deterministic random seed to make automation/repeatability reliable
        random.seed(42)
        selected = random.sample(all_samples, 10)

    print(f" Selected {len(selected)} random samples for human verification.")
    print("Press Enter to start...")
    input()

    final_dataset = []

    for i, item in enumerate(selected):
        clear_screen()
        print(f" SAMPLE [{i+1} / {len(selected)}]")
        print("=" * 60)
        print(f" QUESTION:\n{item['question']}")
        print("-" * 60)
        print(f" CONTEXT SNIPPET:\n{str(item['contexts'])[:400]}...")
        print("-" * 60)
        print(f" SYSTEM ANSWER:\n{item['answer']}")
        print("=" * 60)
        print("\nRUBRIC: 1(Fail) - 2(Poor) - 3(Okay) - 4(Good) - 5(Perfect)")
        
        while True:
            try:
                human_in = input(" Enter your score (1-5): ").strip()
                if not human_in:
                    continue
                val = int(human_in)
                if 1 <= val <= 5:
                    break
                else:
                    print("️ Must be between 1 and 5.")
            except ValueError:
                print("️ Please enter a numeric value (1,2,3,4,5).")
        
        # Add user input and capture pair
        entry = {
            "id": item.get("id"),
            "question": item.get("question"),
            "llm_score": item.get("llm_score"),
            "human_score": val
        }
        final_dataset.append(entry)
        print(f"\n Saved. Moving to next...")
        
    out_path = os.path.join(PROJECT_ROOT, "reports", "human_labels.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)
        
    print("\n Calibration data collection complete!")
    print(f" Saved to: reports/human_labels.json")

if __name__ == "__main__":
    main()
