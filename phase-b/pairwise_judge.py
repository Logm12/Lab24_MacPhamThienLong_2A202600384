import os
import sys
import json
import time
import csv
from openai import OpenAI

# Ensure project root imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import build_pipeline, run_query
from config import OPENAI_API_KEY

# Ensure output is safe for Windows emojis/unicode
sys.stdout.reconfigure(encoding='utf-8')

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Bạn là một chuyên gia đánh giá hệ thống Trả lời câu hỏi (QA Expert).
Nhiệm vụ của bạn là so sánh hai câu trả lời (Trả lời A và Trả lời B) dựa trên Câu hỏi được đưa ra.
Tiêu chí chấm:
1. Tính chính xác (Faithfulness) so với thực tế.
2. Độ hữu ích, súc tích và định dạng đẹp.
Nếu một câu trả lời cung cấp đúng và đầy đủ hơn, hãy chọn nó. Nếu cả hai tương đương, hãy chọn 'Tie'.

BẠN PHẢI TRẢ VỀ KẾT QUẢ DUY NHẤT LÀ MỘT ĐỐI TƯỢNG JSON VỚI SCHEMA SAU:
{
    "winner": "A" | "B" | "Tie",
    "reasoning": "Giải thích ngắn gọn lý do trong 1 câu."
}
"""

def call_llm_judge(question: str, ans_a: str, ans_b: str) -> dict:
    """Invokes OpenAI API to judge between response A and response B."""
    prompt = f"Câu hỏi: {question}\n\nTrả lời A: {ans_a}\n\nTrả lời B: {ans_b}\n\nKết quả JSON:"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.0
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"  [Error calling LLM]: {e}")
        return {"winner": "Tie", "reasoning": f"Error: {e}"}

def build_fast_pipeline():
    """
    Hybrid Solution following Poka-Yoke & Kaizen:
    Handles local offline mode by instantly building a minimal local index 
    skipping expensive M5 calls, ensuring queries work without external Docker.
    """
    print("\n Building Fully Isolated Local RAG Environment...")
    from src.m1_chunking import load_documents, chunk_hierarchical
    from src.m2_search import HybridSearch
    from src.m3_rerank import CrossEncoderReranker

    print("[1/3] Loading & chunking source documents...")
    docs = load_documents()
    all_chunks = []
    for doc in docs:
        parents, children = chunk_hierarchical(doc["text"], metadata=doc["metadata"])
        for child in children:
            all_chunks.append({"text": child.text, "metadata": {**child.metadata, "parent_id": child.parent_id}})
    print(f"  -> Generated {len(all_chunks)} raw chunks.")

    print("[2/3] Initializing local index (BM25 + Dense)...")
    search = HybridSearch()
    # This will create collections in local_qdrant_db automatically
    search.index(all_chunks)
    print("  -> Local index popuated successfully.")

    print("[3/3] Loading offline reranker...")
    reranker = CrossEncoderReranker()
    
    return search, reranker

def main():
    print(" Starting Pairwise LLM-as-Judge Procedure")
    
    naive_path = os.path.join(PROJECT_ROOT, "reports", "naive_baseline_report.json")
    if not os.path.exists(naive_path):
        print(f" Error: {naive_path} not found!")
        return
        
    with open(naive_path, 'r', encoding='utf-8') as f:
        naive_data = json.load(f)
        
    items = naive_data.get("details", [])
    if not items:
        print(" No details found in naive baseline report.")
        return

    print(f" Loaded {len(items)} baseline samples.")

    # Use Fast initialization
    search, reranker = build_fast_pipeline()
    
    results = []
    production_wins = 0
    naive_wins = 0
    ties = 0

    print("\n️  Starting Judging Loop...")
    for idx, item in enumerate(items):
        q = item.get("question", "")
        naive_ans = item.get("answer", "")
        
        print(f"  [{idx+1}/{len(items)}] Query: {q[:40]}...")
        
        # 1. Get live production answer
        prod_ans, _ = run_query(q, search, reranker)
        
        # 2. Call LLM Judge (Round 1: A = Prod, B = Naive)
        print(f"    -> Swap Round 1 (Prod vs Naive)...")
        r1 = call_llm_judge(q, prod_ans, naive_ans)
        
        # 3. Call LLM Judge (Round 2: A = Naive, B = Prod) - Flip positions to counter Bias
        print(f"    -> Swap Round 2 (Naive vs Prod)...")
        r2 = call_llm_judge(q, naive_ans, prod_ans)
        
        # Aggregate Winner based on "Production System" context
        # In R1: Prod is A, Naive is B.
        w1 = r1.get("winner")
        # In R2: Naive is A, Prod is B.
        w2 = r2.get("winner")
        
        final_winner = "Tie"
        
        # Normalize rounds back to production view
        # Score mapping: Production = +1, Naive = -1, Tie = 0
        score1 = 1 if w1 == "A" else (-1 if w1 == "B" else 0)
        score2 = 1 if w2 == "B" else (-1 if w2 == "A" else 0)
        
        final_score = score1 + score2
        
        if final_score > 0:
            final_winner = "Production"
            production_wins += 1
        elif final_score < 0:
            final_winner = "Naive"
            naive_wins += 1
        else:
            final_winner = "Tie"
            ties += 1
            
        print(f"     Result: {final_winner}")
        
        results.append({
            "question": q,
            "naive_answer": naive_ans,
            "production_answer": prod_ans,
            "r1_winner": w1,
            "r1_reason": r1.get("reasoning", ""),
            "r2_winner": w2,
            "r2_reason": r2.get("reasoning", ""),
            "final_winner": final_winner
        })

    # Write to CSV
    out_csv = os.path.join(PROJECT_ROOT, "reports", "pairwise_results.csv")
    keys = results[0].keys()
    with open(out_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
        
    print("\n" + "="*40)
    print(" FINAL PAIRWISE STATS")
    print("="*40)
    print(f" Production Wins : {production_wins}")
    print(f"️  Naive Wins      : {naive_wins}")
    print(f" Ties            : {ties}")
    print(f" Report saved to: reports/pairwise_results.csv")
    print("="*40)

if __name__ == "__main__":
    main()
