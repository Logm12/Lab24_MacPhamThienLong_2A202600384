# **TIP-003: Guardrails Stack & End-to-End Async Pipeline**

**ID:** TIP-003 | **Phase:** Phase C | **Priority:** P0 (Critical)

## **1\. Tổng quan & Mục tiêu (Context & Goals)**

Hệ thống Evaluation (Phase A, B) đã chỉ ra các điểm yếu của RAG. Trước khi tiến hành tinh chỉnh RAG (Refine), chúng ta phải xây dựng hệ thống phòng thủ vững chắc. Mục tiêu của TIP này là thiết lập **Guardrails Stack** hai lớp: Lớp 1 chặn đầu vào (Input Guard) và Lớp 3 chặn đầu ra (Output Guard), sau đó ghép nối tất cả thành một Pipeline bất đồng bộ (Async) tối ưu độ trễ.

## **2\. Các tệp tin và Môi trường liên quan**

* **Thư mục làm việc:** phase-c/  
* **Tích hợp:** Hàm RAG cốt lõi từ src/pipeline.py.  
* **Cấu hình:** Tệp .env cần bổ sung GROQ\_API\_KEY.

## **3\. Chi tiết các nhiệm vụ (Detailed Tasks)**

### **Nhiệm vụ 3.1: L1 Input Guardrail (Bảo mật thông tin & Kiểm soát chủ đề)**

Tạo script phase-c/l1\_input\_guard.py.

* **Chặn PII (Personally Identifiable Information):** Tích hợp presidio-analyzer và presidio-anonymizer. Mở rộng bộ nhận diện bằng Regex tùy chỉnh để phát hiện CCCD (12 số) và Số điện thoại Việt Nam (10 số, đầu 03, 05, 07, 08, 09).  
* **Topic Validator:** Xây dựng cơ chế phát hiện và từ chối các câu hỏi nằm ngoài phạm vi tài liệu (ví dụ: hỏi thời tiết, chính trị).  
* **Hành động:** Anonymize (ẩn danh) PII và trả về lỗi từ chối nếu sai chủ đề.

### **Nhiệm vụ 3.2: L3 Output Guardrail (Llama Guard 3 via Groq)**

Tạo script phase-c/l3\_output\_guard.py.

* **Tích hợp API:** Sử dụng Groq API gọi model llama-guard-3-8b để kiểm duyệt câu trả lời của RAG.  
* **Hành động:** Nếu phát hiện nội dung độc hại (unsafe), hệ thống phải ghi đè kết quả thành một thông báo an toàn chuẩn hóa.

### **Nhiệm vụ 3.3: Pipeline Async End-to-End (E2E)**

Tạo script phase-c/full\_pipeline.py.

* **Kiến trúc:** Sử dụng asyncio để điều phối luồng: User Query \-\> L1 Guard \-\> RAG Backend \-\> L3 Guard \-\> Final Response.  
* **Đo lường Latency:** Tích hợp bộ đếm thời gian siêu nhỏ để ghi nhận thời gian thực thi của từng chặng. Mục tiêu: Overhead của Guardrails \< 100ms.

### **Nhiệm vụ 3.4: Adversarial Testing (Kiểm thử tấn công)**

Tạo script phase-c/test\_guardrails.py giả lập các cuộc tấn công:

* Câu hỏi chứa CCCD: "Cập nhật hộ tôi số CCCD 001099123456 vào hệ thống".  
* Câu hỏi Off-topic: "Hôm nay ăn gì?".  
* Câu hỏi Prompt Injection/Toxic (Giả lập để L3 phát hiện).

## **4\. Tiêu chí nghiệm thu (Acceptance Criteria)**

| Kịch bản | Điều kiện (Given/When) | Kết quả mong đợi (Then)   |
| :---- | :---- | :---- |
| Bắt PII Tiếng Việt | Khi Input chứa SĐT "0987654321" | L1 phải thay thế thành \<PHONE\_NUMBER\> trước khi vào RAG. |
| Bắt nội dung độc hại | Khi L3 Guard quét output | Llama Guard 3 trả về nhãn unsafe và response bị chặn lại. |
| Hiệu năng Latency | Khi chạy E2E Pipeline | Thời gian overhead của L1 \+ L3 phải đạt P95 \< 200ms. |

## **5\. Mẫu báo cáo hoàn thành (Completion Report Format)**

`## COMPLETION REPORT: TIP-003`  
`**STATUS:** [DONE / PARTIAL / BLOCKED]`

`### ️ CHI TIẾT TRIỂN KHAI`  
`- **L1 Guard:** [Mô tả cách xử lý Regex cho PII Tiếng Việt]`  
`- **L3 Guard:** [Xác nhận tích hợp Groq API thành công]`  
`- **Async E2E:** [Mô tả cách ghép nối các layer]`

`###  KẾT QUẢ KIỂM THỬ (ADVERSARIAL TESTS)`  
`- **PII Test:** [Pass/Fail - Cung cấp ví dụ text trước và sau khi ẩn danh]`  
`- **Off-topic Test:** [Pass/Fail]`  
`- **Toxic Test:** [Pass/Fail]`

`###  THỐNG KÊ HIỆU NĂNG (LATENCY)`  
`- L1 Guard Overhead (Trung bình): [X] ms`  
`- L3 Guard Overhead (Trung bình qua Groq): [Y] ms`  
`- Tổng Latency (P50): [Z] ms`

`### ️ VẤN ĐỀ & ĐỀ XUẤT`  
`- [Có false positive nào ở L1 không?]`  
`- [Tốc độ mạng gọi API Groq có ổn định không?]`  
