# **TIP-001: RAGAS Evaluation & Automation**

**ID:** TIP-001 | **Phase:** Phase A | **Priority:** P0 (Critical)

## **1\. Tổng quan & Mục tiêu (Context & Goals)**

Mục tiêu của gói công việc (TIP) này là thiết lập nền tảng đánh giá (baseline evaluation) cho hệ thống RAG hiện tại. Thợ thi công (Builder) sẽ chịu trách nhiệm xây dựng bộ dữ liệu kiểm thử tổng hợp chất lượng cao và thực hiện khung đánh giá RAGAS để đo lường hiệu suất hiện tại của hệ thống trước khi tiến hành các bước tối ưu hóa hoặc bảo vệ (Guardrails).

## **2\. Các tệp tin và Môi trường liên quan**

* **Backend:** src/pipeline.py \- Chứa hàm cốt lõi run\_query.  
* **Dữ liệu nguồn:** Thư mục data/ \- Chứa các tài liệu PDF/Markdown để sinh câu hỏi.  
* **Cấu hình:** Tệp .env \- Phải chứa OPENAI\_API\_KEY hợp lệ.

## **3\. Chi tiết các nhiệm vụ (Detailed Tasks)**

### **Nhiệm vụ 3.1: Sinh bộ dữ liệu kiểm thử tổng hợp (Synthetic Test Set)**

Thợ thi công cần tạo script phase-a/generate\_testset.py sử dụng TestsetGenerator của Ragas kết hợp với model gpt-4o-mini.

* **Số lượng:** Sinh chính xác **50 câu hỏi**.  
* **Phân bổ loại câu hỏi:** 50% Simple (Đơn giản), 25% Reasoning (Suy luận), 25% Multi-context (Đa ngữ cảnh).  
* **Đầu ra:** Lưu trữ tại phase-a/testset.json.

### **Nhiệm vụ 3.2: Thực thi đo lường chỉ số RAGAS**

Tạo script phase-a/run\_eval.py để kết nối bộ dữ liệu kiểm thử với logic RAG thực tế.

* **Tích hợp:** Import hàm run\_query từ src.pipeline.  
* **Chỉ số đánh giá:** Thực hiện tính toán 4 chỉ số: *Faithfulness, Answer Relevancy, Context Precision, Context Recall*.  
* **Đầu ra:** Báo cáo chi tiết lưu tại reports/ragas\_report.json.

### **Nhiệm vụ 3.3: Phân tích lỗi và Dọn dẹp hệ thống (Failure Analysis & Cleanup)**

Tạo script phase-a/analyze\_failures.py để phân cụm các mẫu có điểm số thấp (\< 0.5) nhằm xác định nguyên nhân gốc rễ.  
**Giao thức dọn dẹp (Cleanup Protocol):** Triển khai hàm tự động xóa toàn bộ các tệp/thư mục rác như .cache, \_\_pycache\_\_, .tmp, và các tệp log tạm thời sau khi hoàn tất quy trình.

## **4\. Tiêu chí nghiệm thu (Acceptance Criteria)**

| Kịch bản | Điều kiện (Given/When) | Kết quả mong đợi (Then)   |
| :---- | :---- | :---- |
| Kiểm thử Backend | Khi chạy run\_eval.py | Hệ thống phải truy vấn thành công 50 câu hỏi và lưu báo cáo JSON. |
| Kiểm thử Frontend (CLI) | Người dùng quan sát Terminal | Phải hiển thị thanh tiến trình (tqdm) và bảng tổng kết kết quả có màu sắc rõ ràng. |
| Dọn dẹp hệ thống | Sau khi kết thúc script | Không còn bất kỳ tệp \_\_pycache\_\_ hay tệp tạm nào tồn tại trong thư mục dự án. |

## **5\. Mẫu báo cáo hoàn thành (Completion Report Format)**

Thợ thi công bắt buộc phải sử dụng mẫu sau để báo cáo kết quả:

\#\# COMPLETION REPORT: TIP-001  
\*\*STATUS:\*\* \[DONE / PARTIAL / BLOCKED\]

\#\#\# ️ CHI TIẾT TRIỂN KHAI  
\- \*\*Tệp tin đã tạo:\*\* \[Danh sách đường dẫn\]  
\- \*\*Logic cốt lõi:\*\* \[Giải thích cách tích hợp với src/pipeline.py\]  
\- \*\*Frontend/CLI:\*\* \[Mô tả trải nghiệm giao diện dòng lệnh\]

\#\#\#  KẾT QUẢ KIỂM THỬ  
\- \*\*Backend Test:\*\* \[Số lượng mẫu, thời gian thực thi\]  
\- \*\*Frontend Test:\*\* \[Trạng thái hiển thị thanh tiến trình, bảng tổng kết\]  
\- \*\*Cleanup:\*\* \[Xác nhận đã dọn dẹp tệp rác\]

\#\#\#  TỔNG KẾT CHỈ SỐ (AVG)  
\- Faithfulness: \[Score\]  
\- Answer Relevancy: \[Score\]  
\- Context Precision: \[Score\]  
\- Context Recall: \[Score\]

\#\#\# ️ VẤN ĐỀ & ĐỀ XUẤT  
\- \[Lỗi phát sinh hoặc điểm cần lưu ý cho Phase B\]  
