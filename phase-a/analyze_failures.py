import sys
import json
import shutil
from pathlib import Path

# Context roots
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent

# Hardened Global configuration for legacy console drivers
sys.stdout.reconfigure(encoding='utf-8')

def cleanup_protocol():
    """
    Executes secure sanitation of workspace by automatically purging:
    __pycache__, .cache, temp files, and dangling logs.
    (Implements 'Giao thức dọn dẹp' requirement).
    """
    print("\n" + "" * 20)
    print(" INITIATING AUTOMATIC SYSTEM CLEANUP ")
    print("   Locating artifacts for purge...")

    purge_targets = [
        "**/__pycache__",
        "**/.pytest_cache",
        "**/.cache",
        "**/.ruff_cache",
        "**/.ipynb_checkpoints",
        "**/.tmp",
        "**/*.log",
        "**/tmp_*",
    ]
    
    removed_directories = 0
    removed_files = 0

    # Safely traverse all project subdirs
    for target_pattern in purge_targets:
        # Use rglob to dynamically search recursively safely
        for path_found in ROOT_DIR.rglob(target_pattern):
            # Guard against accidentally removing the main folder or core assets
            if "data" in path_found.parts or "src" == path_found.name:
                continue 

            try:
                if path_found.is_dir():
                    shutil.rmtree(path_found, ignore_errors=True)
                    removed_directories += 1
                elif path_found.is_file():
                    path_found.unlink(missing_ok=True)
                    removed_files += 1
            except Exception:
                pass # Ignore permission locked files

    print(" Sanitization Complete!")
    print(f"   Removed {removed_directories} caches and {removed_files} file artifacts.")
    print("" * 20 + "\n")

def analyze_failures():
    """
    Filters exported report for underperforming queries (<0.5) and outputs summary.
    Applies heuristic cleanup for known environment artifact bloating.
    """
    
    report_file = ROOT_DIR / "reports" / "ragas_report.json"
    
    print("\n" + "="*60)
    print("  RAGAS FAILURE ANALYSIS ENGINE")
    print("="*60)

    if not report_file.exists():
        print(f" Warning: Could not load source report at {report_file}.")
        print("   Ensure you have executed 'phase-a/run_eval.py' beforehand.")
        # As confirmed by user feedback, triggering cleanup protocol even on skipped audit
        cleanup_protocol()
        return

    try:
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(" Fatal: Report JSON corrupted.")
        cleanup_protocol()
        sys.exit(1)

    details_grid = data.get("details", [])
    if not details_grid:
        print("️ No individual question trace logs found in report payload.")
        cleanup_protocol()
        return

    # Filtering algorithm for clustered low scores
    fail_cluster = []
    threshold = 0.50

    for record in details_grid:
        bad_metrics = []
        # Target the core standard ragas outputs
        for metric_name in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            raw_val = record.get(metric_name)
            if raw_val is None:
                continue
            
            try:
                val = float(raw_val)
                if val < threshold:
                     bad_metrics.append((metric_name, val))
            except (ValueError, TypeError):
                continue
        
        if bad_metrics:
            fail_cluster.append({
                "q": record.get("question", record.get("user_input", "N/A")),
                "fails": bad_metrics,
                "ans": record.get("answer", record.get("response", "No Response"))
            })

    # Formatting the Cluster Report Output
    print(f"\n SCAN SUMMARY: Found [ {len(fail_cluster)} ] queries tracking below acceptable thresholds (< 0.50).\n")
    
    if not fail_cluster:
         print(" CRITICAL ALERT: No failures detected! System operating cleanly.")
    else:
         # Listing top samples formatted
         for idx, entry in enumerate(fail_cluster[:10], 1):
             print(f" Alert #{idx}")
             print(f"   • Prompt: \"{entry['q'][:85]}...\"")
             for m_name, val in entry["fails"]:
                 print(f"      Failed: {m_name:<18} | Score: {val:.4f}")
             print("")
         
         if len(fail_cluster) > 10:
             print(f"... and {len(fail_cluster) - 10} more suppressed for brevity.")

    print("-" * 60)
    # Automated cascading cleanup hook ordered by the user
    cleanup_protocol()

if __name__ == "__main__":
    analyze_failures()
