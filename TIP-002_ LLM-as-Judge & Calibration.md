# **TIP-002: LLM-as-Judge & Calibration**

**ID:** TIP-002 | **Phase:** Phase B | **Priority:** P0 (Critical)

## **1\. Tổng quan & Mục tiêu (Context & Goals)**

Sau khi đã có các chỉ số RAGAS cơ bản từ Phase A, Phase B tập trung vào việc xây dựng một hệ thống đánh giá "thông minh" hơn bằng cách sử dụng LLM làm giám khảo (LLM-as-Judge). Mục tiêu là thiết lập quy trình so sánh cặp (Pairwise), chấm điểm tuyệt đối (Absolute) và quan trọng nhất là đo lường sự đồng thuận giữa AI và Con người (Calibration).

## **2\. Các tệp tin và Môi trường liên quan**

* **Thư mục làm việc:** phase-b/  
* **Dữ liệu đầu vào:** reports/ragas\_report.json (Kết quả từ Phase A) và dữ liệu từ hệ thống Naive Baseline (nếu có).  
* **Cấu hình:** Tệp .env với OPENAI\_API\_KEY.

## **3\. Chi tiết các nhiệm vụ (Detailed Tasks)**

### **Nhiệm vụ 3.1: Xây dựng Pipeline So sánh cặp (Pairwise Judge)**

Tạo script phase-b/pairwise\_judge.py sử dụng gpt-4o-mini để so sánh câu trả lời của hệ thống RAG hiện tại với hệ thống Baseline.

* **Cơ chế chống Bias:** Thực hiện cơ chế "Swap-and-Average" (đổi vị trí Model A và B giữa hai lần gọi) để loại bỏ thiên kiến vị trí (position bias).  
* **Đầu ra:** Tệp reports/pairwise\_results.csv chứa kết quả thắng/thua/hòa.

### **Nhiệm vụ 3.2: Chấm điểm tuyệt đối (Absolute Scoring)**

Tạo script phase-b/absolute\_scorer.py để đánh giá câu trả lời trên thang điểm 1-5 dựa trên một bộ Rubric chi tiết (ví dụ: Độ chính xác, Văn phong, Sự hữu ích).

* **Yêu cầu:** LLM phải đưa ra lý do (Reasoning) cho mỗi mức điểm.

### **Nhiệm vụ 3.3: Công cụ CLI cho Con người gán nhãn (Human Calibration CLI)**

Phát triển một giao diện dòng lệnh (CLI) tương tác tại phase-b/human\_cli.py.

* **Chức năng:** Hiển thị ngẫu nhiên 10 mẫu (Câu hỏi, Ngữ cảnh, Câu trả lời). Người dùng nhập điểm trực tiếp từ bàn phím.  
* **Đầu ra:** Lưu kết quả vào reports/human\_labels.csv.

### **Nhiệm vụ 3.4: Tính toán độ đồng thuận (Cohen's Kappa)**

Tạo script phase-b/calculate\_kappa.py sử dụng scikit-learn để tính toán chỉ số Cohen's Kappa giữa điểm của LLM và điểm của Con người từ 10 mẫu trên.

## **4\. Tiêu chí nghiệm thu (Acceptance Criteria)**

| Kịch bản | Điều kiện (Given/When) | Kết quả mong đợi (Then)   |
| :---- | :---- | :---- |
| Đánh giá AI | Khi chạy pairwise\_judge.py | Hệ thống phải tự động đảo vị trí Model và trả về kết quả trung bình không bị bias. |
| Tương tác CLI | Người dùng chạy human\_cli.py | CLI hiển thị rõ ràng thông tin mẫu và ghi nhận input của người dùng vào tệp CSV. |
| Báo cáo Calibration | Khi chạy calculate\_kappa.py | Phải in ra chỉ số Cohen's Kappa và nhận xét về mức độ tin cậy của Judge. |
| Dọn dẹp hệ thống | Sau khi kết thúc script | Xóa sạch các tệp JSON rác, tệp cached API. |

## **5\. Mẫu báo cáo hoàn thành (Completion Report Format)**

`## COMPLETION REPORT: TIP-002`  
`**STATUS:** [DONE / PARTIAL / BLOCKED]`

`### ️ CHI TIẾT TRIỂN KHAI`  
`- **Tệp tin đã tạo:** [Danh sách đường dẫn]`  
`- **Kỹ thuật Judge:** [Mô tả prompt và cơ chế swap-and-average]`  
`- **Frontend/CLI:** [Mô tả trải nghiệm người dùng khi chấm điểm 10 mẫu]`

`###  KẾT QUẢ KIỂM THỬ`  
`- **Backend Test:** [Xác nhận logic tính toán Kappa, lưu CSV]`  
`- **Frontend Test:** [Xác nhận CLI không lỗi font, bắt input chuẩn]`  
`- **Cleanup:** [Xác nhận đã dọn dẹp các tệp cached API]`

`###  KẾT QUẢ CALIBRATION`  
`- Cohen's Kappa Score: [Score]`  
`- Mức độ đồng thuận: [Slight/Moderate/Substantial/Perfect]`  
`- Tỷ lệ thắng của RAG so với Baseline: [%]`

`### ️ VẤN ĐỀ & ĐỀ XUẤT`  
`- [Các bias phát hiện được (Length bias, Position bias...)]`  
`- [Đề xuất cải thiện Prompt cho Judge]`  
