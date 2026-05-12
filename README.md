# Production RAG Pipeline With Guardrails Stack

**Môn học:** AICB-P2T3 · Production RAG  
**Sinh viên thực hiện:** Mạc Phạm Thiên Long - 2A202600384  
**Dự án:** Xây dựng hệ thống RAG phục vụ chính sách nội bộ tích hợp kiểm duyệt đa tầng (L1 - Input Guard / L3 - Output Guard).

---

## Tổng quan

Dự án này là phiên bản hoàn thiện của hệ thống Question-Answering dựa trên Retrieval-Augmented Generation (RAG), nhắm mục tiêu áp dụng vào sản phẩm thực tế. Hệ thống được bao bọc bởi các lớp bảo vệ PII (Thông tin định danh cá nhân), lọc chủ đề ngoài lề (Off-topic filter), và kiểm duyệt nội dung độc hại (Content moderation) qua API Groq.

## Quick Start (Chạy nhanh trong 5 phút)

### 1. Cài đặt Môi trường
Hệ thống hỗ trợ chạy hoàn toàn Local mà không phụ thuộc bắt buộc vào Docker.

```bash
git clone https://github.com/Logm12/Lab24_MacPhamThienLong_2A202600384.git
cd Lab24_MacPhamThienLong_2A202600384
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Cấu hình API Keys
Tạo file `.env` tại thư mục gốc dựa trên mẫu `.env.example` và điền các mã khóa sau:
```ini
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...
GROQ_API_KEY=gsk_...
```

### 3. Chạy E2E Pipeline thử nghiệm
Chạy trực tiếp script pipeline kết hợp bảo vệ 2 đầu:
```bash
python phase-c/full_pipeline.py
```

---

## Cấu trúc Thư mục Dự án

```text
Lab24_MacPhamThienLong_2A202600384/
├── README.md                    # Tài liệu hướng dẫn chính
├── requirements.txt             # Thư viện phụ thuộc
├── config.py                    # Cấu hình chung hệ thống
│
├── data/                        # Dữ liệu văn bản mẫu (.pdf / .md)
│
├── src/                         # Lõi hệ thống RAG
│   ├── m1_chunking.py           # Cắt nhỏ văn bản phân cấp
│   ├── m2_search.py             # Tìm kiếm lai (Hybrid Search)
│   ├── m3_rerank.py             # Tái sắp xếp (Cohere/Cross-Encoder)
│   └── pipeline.py              # Ghép nối các module RAG cơ bản
│
├── phase-a/                     # Thử nghiệm Giai đoạn A: Eval baseline
├── phase-b/                     # Thử nghiệm Giai đoạn B: LLM-as-Judge
├── phase-c/                     # Thử nghiệm Giai đoạn C: Guardrails
│   ├── l1_input_guard.py        # Lọc đầu vào PII + Topic
│   ├── l3_output_guard.py       # Lọc đầu ra qua Groq AI
│   └── full_pipeline.py         # Tổng hợp toàn trình bất đồng bộ (Async)
│
├── analysis/                    # Báo cáo và thiết kế kiến trúc
│   ├── blueprint.md             # Sơ đồ Mermaid và SLO
│   └── xray_report.md           # Phân tích quyết định thiết kế
│
└── local_qdrant_db/             # CSDL Vector cục bộ (Tự động khởi tạo)
```

---

## Báo cáo Thực nghiệm và Kiểm thử

- **Phase A & B Evaluation:** Các báo cáo chấm điểm tự động và so sánh Pairwise (Naive vs Production) nằm trong thư mục `reports/`. Điểm số Absolute Scorer đạt trung bình 2.15/5.0 do hệ thống tuân thủ tiêu chí an toàn tuyệt đối.
- **Phase C Adversarial Tests:** Chạy `python phase-c/test_guardrails.py` để kiểm chứng 13 tình huống tấn công, bao gồm lộ lọt CCCD, số điện thoại, hỏi thời tiết ngoài lề, hoặc kích động nguy hiểm.

---

## Xử lý sự cố (Troubleshooting)

### 1. Lỗi kết nối Groq API
**Triệu chứng:** Thời gian chờ kéo dài hoặc API báo lỗi `Empty response`.  
**Khắc phục:** Đây có thể do thời gian Warm-up mô hình lần đầu tại server Groq (khoảng 2-3 giây). Lần truy vấn tiếp theo sẽ trở về mức 300ms bình thường. Vui lòng kiểm tra lại kết nối Internet.

### 2. Không nhận diện được thư viện Presidio / Spacy
**Triệu chứng:** Lỗi `ModuleNotFoundError` hoặc `IOError` khi tải model ngôn ngữ.  
**Khắc phục:** Hãy chắc chắn đã chạy dòng lệnh `python -m spacy download en_core_web_sm` sau khi đã `pip install`.

### 3. Về Docker Qdrant
Hệ thống được cấu hình mặc định sử dụng `local_qdrant_db` lưu trữ dưới dạng tệp tin để tối ưu hóa tốc độ cài đặt. Không yêu cầu bạn phải khởi động Docker Daemon.

---

## Bản Quyền
Dự án được xây dựng như bài nộp chính thức cho khóa học AICB-P2T3. 
Người nộp bài: **Mạc Phạm Thiên Long**
