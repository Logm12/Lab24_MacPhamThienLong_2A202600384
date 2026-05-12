import os
import sys
import json
from openai import OpenAI

# Ensure project root imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import OPENAI_API_KEY

sys.stdout.reconfigure(encoding='utf-8')
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Bạn là một hệ thống chấm điểm QA khắt khe.
Nhiệm vụ của bạn là chấm điểm độ chính xác và hữu ích của Câu trả lời (Answer) dựa trên Câu hỏi (Question) và Ngữ cảnh hỗ trợ (Context).

Tiêu chí chấm điểm (Thang 1-5):
1 - Rất tệ: Câu trả lời sai hoàn toàn, hoặc nói không tìm thấy trong khi Context CÓ thông tin.
2 - Tệ: Câu trả lời chứa một chút thông tin đúng nhưng lan man, mơ hồ hoặc sai trọng tâm.
3 - Khá: Câu trả lời có thông tin đúng, đáp ứng được yêu cầu cơ bản nhưng chưa hoàn chỉnh.
4 - Tốt: Câu trả lời đầy đủ, chính xác dựa trên Context, bố cục dễ hiểu.
5 - Xuất sắc: Câu trả lời cực kỳ chính xác, trực tiếp trả lời câu hỏi, súc tích, không thừa thãi.

BẠN PHẢI TRẢ VỀ DUY NHẤT MỘT ĐỐI TƯỢNG JSON VỚI SCHEMA:
{
    "score": [int từ 1 đến 5],
    "reasoning": "[Giải thích ngắn gọn trong 1 câu tại sao cho điểm này]"
}
"""

def call_absolute_scorer(question: str, contexts: list[str], response: str) -> dict:
    ctx_str = "\n".join([f"- {c}" for c in contexts])
    prompt = f"Question: {question}\n\nContext:\n{ctx_str}\n\nAnswer: {response}\n\nKết quả JSON:"
    
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
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"score": 1, "reasoning": f"API Error: {e}"}

def main():
    print(" Initializing Absolute Scorer (LLM Rubric 1-5)")
    ragas_path = os.path.join(PROJECT_ROOT, "reports", "ragas_report.json")
    
    if not os.path.exists(ragas_path):
        print(" Error: ragas_report.json not found!")
        return

    with open(ragas_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    details = data.get("details", [])
    print(f" Found {len(details)} responses to score.")

    results = []
    total_score = 0
    
    for idx, item in enumerate(details):
        q = item.get("user_input", "")
        ctx = item.get("retrieved_contexts", [])
        ans = item.get("response", "")
        
        print(f"  [{idx+1}/{len(details)}] Scoring: {q[:40]}...")
        
        rating = call_absolute_scorer(q, ctx, ans)
        score = int(rating.get("score", 1))
        reason = rating.get("reasoning", "")
        
        print(f"    -> Score: {score}/5")
        
        total_score += score
        
        # Store comprehensive structure
        results.append({
            "id": idx + 1,
            "question": q,
            "contexts": ctx,
            "answer": ans,
            "llm_score": score,
            "llm_reasoning": reason
        })

    avg_score = total_score / len(details) if details else 0
    
    out_path = os.path.join(PROJECT_ROOT, "reports", "absolute_scores.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "⭐"*20)
    print(f" Scored {len(details)} items.")
    print(f" Average Absolute Score: {avg_score:.2f} / 5.0")
    print(f" Saved scores to: reports/absolute_scores.json")
    print("⭐"*20)

if __name__ == "__main__":
    main()
