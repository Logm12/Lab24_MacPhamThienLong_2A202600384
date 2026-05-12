import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Setup root path environment for correct imports
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from tqdm import tqdm
    from rich.console import Console
    from rich.table import Table
    
    from src.pipeline import build_pipeline, run_query
    
    # Ragas integration
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError as e:
    print(f" ImportError: {e}")
    print("Please install dependencies first.")
    sys.exit(1)

def run_evaluation():
    """
    Loads synthetic test set, drives them through local RAG pipeline,
    computes RAGAS metrics and outputs styled table + validated JSON report.
    """
    # Ensure safe encoding to prevent crash on legacy Windows shell (Poka-Yoke)
    sys.stdout.reconfigure(encoding='utf-8')
    
    console = Console()
    console.rule("[bold cyan]️  RAGAS System Integration & Evaluation ️[/]")
    
    load_dotenv(dotenv_path=ROOT_DIR / ".env")
    
    # Paths config
    testset_path = CURRENT_DIR / "testset.json"
    reports_dir = ROOT_DIR / "reports"
    report_file = reports_dir / "ragas_report.json"
    
    # 1. Load data verification (Poka-Yoke)
    if not testset_path.exists():
        console.print(f"[bold red]️ FAILED:[/] testset.json missing at {testset_path}.")
        console.print(" Run [bold white]python phase-a/generate_testset.py[/] before running eval.")
        sys.exit(1)

    with open(testset_path, encoding="utf-8") as f:
        test_cases = json.load(f)
    
    console.print(f" Successfully imported [bold yellow]{len(test_cases)}[/] test cases.")

    # 2. Scaffold Pipeline Components
    console.print("\n[magenta]️ Step 1: Instantiating RAG pipeline (indexing and model loading)...[/]")
    start_build = time.time()
    try:
        search_sys, rerank_sys = build_pipeline()
        build_dur = time.time() - start_build
        console.print(f" Pipeline hydrated in {build_dur:.2f}s")
    except Exception as ex:
        console.print(f"[bold red] Critical Pipeline Error:[/] {ex}")
        sys.exit(1)

    # 3. Pass Queries Through Live Pipe
    console.print("\n[magenta] Step 2: Flowing queries through Live System...[/]")
    
    prepared_data = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": []
    }

    # UX: tqdm with a custom color per requirements
    for row in tqdm(test_cases, desc="Passing through RAG", unit="q", colour="#00FF00"):
        # Robust key finding in synthetic set schemas
        question = row.get("question") or row.get("user_input")
        reference = row.get("ground_truth") or row.get("reference")
        
        if not question:
            continue
            
        try:
            # Actual system inference
            ans, context_list = run_query(question, search_sys, rerank_sys)
            
            prepared_data["question"].append(question)
            prepared_data["answer"].append(ans)
            prepared_data["contexts"].append(context_list)
            prepared_data["ground_truth"].append(reference if reference else "")
        except Exception as loop_ex:
             console.print(f"\n[dim yellow]Skipped faulty query: {question[:40]} - {loop_ex}[/]")
    
    # 4. Execute Ragas Core
    console.print("\n[magenta] Step 3: Executing Ragas scoring computation...[/]")
    
    if not prepared_data["question"]:
        console.print("[bold red]Fatal: No valid responses received to evaluate![/]")
        sys.exit(1)
        
    raw_ds = Dataset.from_dict(prepared_data)
    
    try:
        results = evaluate(
            raw_ds,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.0),
            embeddings=OpenAIEmbeddings()
        )
    except Exception as ragas_ex:
        console.print(f"[bold red]Evaluation Suite Crashed:[/] {ragas_ex}")
        sys.exit(1)

    # Clean result data via pandas
    df_results = results.to_pandas()
    mean_scores = df_results.mean(numeric_only=True).to_dict()

    # 5. UI Table Output (Rich Framework)
    table = Table(
        title="RAG SYSTEM PERFORMANCE SUMMARY", 
        show_lines=True,
        border_style="blue"
    )
    
    table.add_column("Ragas Metric", style="bold white")
    table.add_column("Average Score", justify="right")
    
    # Extract metrics cleanly with defaults in case mapping keys shifted
    f_score = mean_scores.get("faithfulness", 0.0)
    ar_score = mean_scores.get("answer_relevancy", 0.0)
    cp_score = mean_scores.get("context_precision", 0.0)
    cr_score = mean_scores.get("context_recall", 0.0)

    def color_val(val):
        if val >= 0.8:
            return f"[bold green]{val:.4f}[/]"
        if val >= 0.6:
            return f"[yellow]{val:.4f}[/]"
        return f"[bold red]{val:.4f}[/]"

    table.add_row("Faithfulness", color_val(f_score))
    table.add_row("Answer Relevancy", color_val(ar_score))
    table.add_row("Context Precision", color_val(cp_score))
    table.add_row("Context Recall", color_val(cr_score))
    
    console.print("\n")
    console.print(table)
    console.print("\n")

    # 6. Write outputs conforming to validated repository schema (from check_lab.py)
    reports_dir.mkdir(exist_ok=True)
    
    validated_report_structure = {
        "aggregate": {
            "faithfulness": float(f_score),
            "answer_relevancy": float(ar_score),
            "context_precision": float(cp_score),
            "context_recall": float(cr_score)
        },
        "num_questions": len(prepared_data["question"]),
        # Including original dataset rows for tracing (failure_analysis will consume this)
        "details": df_results.to_dict(orient="records")
    }
    
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(validated_report_structure, f, ensure_ascii=False, indent=2)
        console.print(f" [bold green]Exported Final Report to:[/] {report_file}")
    except Exception as io_ex:
        console.print(f"[bold red]Save Error:[/] {io_ex}")

    console.rule("[bold blue]Evaluation End[/]")

if __name__ == "__main__":
    run_evaluation()
