# Individual Reflection — Lab 18

**Tên:** Mạc Phạm Thiên Long
**Module phụ trách:** Module 1 tới Module 5

---

## 1. Đóng góp kỹ thuật

- Module đã implement: M1 (Chunking), M2 (Hybrid Search), M3 (Rerank), M4 (Evaluation), M5 (Enrichment).
- Các hàm/class chính đã viết: `SemanticChunker`, `HybridSearch`, `CrossEncoderReranker`, `evaluate_ragas`, `enrich_chunks`.
- Số tests pass: 37/37 .

## 2. Kiến thức học được

- Khái niệm mới nhất: Em đã hiểu sâu hơn về hybrid search kết hợp giữa BM25 và dense search thông qua thuật toán RRF. Em cũng học được cách làm giàu dữ liệu (enrichment) bằng HyQA và contextual prepend để cải thiện khả năng truy hồi.
- Điều bất ngờ nhất: Reranking bằng cross-encoder tốn nhiều tài nguyên hơn em nghĩ nhưng hiệu quả mang lại cho độ chính xác là rất rõ rệt.
- Kết nối với bài giảng (slide nào): Liên quan chặt chẽ đến slide về Enrichment Pipeline và Retrieval & Augment.

## 3. Khó khăn & Cách giải quyết

- Khó khăn lớn nhất: Việc đồng bộ hóa các thư viện như ragas và qdrant-client trên môi trường  gặp nhiều lỗi về encoding và version API.
- Cách giải quyết: Em đã phải research thư viện, sử dụng kỹ thuật kiểm tra method trực tiếp trên object và cài đặt explicit các provider cho RAGAS để đảm bảo tính ổn định.
- Thời gian debug: Khoảng 3-4 tiếng cho toàn bộ các module.

## 4. Nếu làm lại

- Sẽ làm khác điều gì: Em sẽ tối ưu hóa phần enrichment pipeline bằng cách xử lý bất đồng bộ (async) hoàn toàn để giảm thời gian xử lý ban đầu.
- Module nào muốn thử tiếp: Em muốn thử nghiệm thêm các kỹ thuật Multi-vector retrieval và GraphRAG.

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|---------------|
| Hiểu bài giảng | 4 |
| Code quality | 4 |
| Teamwork | 5 |
| Problem solving | 4 |
