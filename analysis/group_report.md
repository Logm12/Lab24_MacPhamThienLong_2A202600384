# Group Report — Lab 18

**Nhóm:** X1000
**Ngày:** 04/05/2026

## Thành viên & Module

| Tên | Module | Hoàn thành | Tests pass |
|-----|--------|-----------|-----------|
| Mạc Phạm Thiên Long | M1: Chunking | [x] | 13/13 |
| Mạc Phạm Thiên Long | M2: Search | [x] | 5/5 |
| Mạc Phạm Thiên Long | M3: Rerank | [x] | 5/5 |
| Mạc Phạm Thiên Long | M4: Eval | [x] | 4/4 |
| Mạc Phạm Thiên Long | M5: Enrichment | [x] | 10/10 |

## Kết quả

| Metric | Naive | Production | Δ |
|--------|-------|-----------|---|
| Faithfulness | 1.0000 | 0.9018 | -0.0982 |
| Answer Relevancy | 0.3746 | 0.4976 | +0.1229 |
| Context Precision | 0.9722 | 0.9912 | +0.0190 |
| Context Recall | 0.9211 | 0.9211 | +0.0000 |

## Key Findings

1. **Biggest improvement:** Việc tích hợp Hybrid Search kết hợp reranking đã giúp tăng đáng kể độ chính xác của hệ thống so với phương pháp Dense search truyền thống. Điểm answer relevancy tăng rõ rệt sau khi thêm bước reranking.
2. **Biggest challenge:** Xử lý sự khác biệt về phiên bản API giữa các thư viện và tối ưu hóa thời gian chạy evaluation khi số lượng câu hỏi tăng lên.
3. **Surprise finding:** Các kỹ thuật Enrichment như Contextual Prepend giúp LLM hiểu ngữ cảnh tốt hơn ngay cả khi các chunk bị chia nhỏ, điều này phản ánh qua điểm Faithfulness luôn ở mức cao.

## Presentation Notes

