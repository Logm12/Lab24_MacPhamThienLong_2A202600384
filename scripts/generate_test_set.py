import os
import json
import glob
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_corpus():
    docs = []
    for fp in glob.glob("data/*.md"):
        with open(fp, "r", encoding="utf-8") as f:
            docs.append(f.read())
    return "\n\n".join(docs)

def generate_test_cases(corpus, n=20):
    prompt = f"""Dựa trên nội dung các quy định sau đây, hãy tạo {n} cặp câu hỏi và câu trả lời (ground truth) để kiểm tra hệ thống RAG.
Đảm bảo các câu hỏi đa dạng, bao gồm cả câu hỏi trực tiếp và câu hỏi suy luận nhẹ.
Trả về kết quả dưới định dạng JSON là một list các object có key là "question" và "ground_truth".

Nội dung quy định:
{corpus}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Bạn là một chuyên gia về nhân sự và AI. Hãy trả về CHỈ định dạng JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    data = json.loads(content)
    # The LLM might wrap it in a root key like "test_cases"
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], list):
                return data[key]
    return data

if __name__ == "__main__":
    corpus = load_corpus()
    print("Generating 20 test cases...")
    test_cases = generate_test_cases(corpus, 20)
    
    with open("test_set.json", "w", encoding="utf-8") as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(test_cases)} test cases to test_set.json")
