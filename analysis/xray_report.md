# X-Ray Technical Report: Quyết định Kỹ Thuật và Cơ Sở Thiết Kế

**Người lập báo cáo:** Mạc Phạm Thiên Long - 2A202600384  
**Phạm vi:** Phân tích nội bộ & Giải trình cho Hội đồng Giám khảo  

Báo cáo này áp dụng X-Ray Protocol để mổ xẻ 3 quyết định kiến trúc then chốt được đưa ra trong quá trình phát triển Hệ thống RAG và Guardrails Stack, lý giải tính phù hợp thực tiễn thay vì đi theo giải pháp mẫu thông thường.

---

## 1. Vấn đề Tự phục hồi Kiến trúc (Resilience Architecture)

**Quyết định:** Chuyển đổi cơ chế lưu trữ Qdrant từ Docker Container sang Chế độ Local Persistence (Tệp tin cục bộ).

### Bối cảnh
Trong quá trình triển khai Phase B, hệ thống gặp sự cố từ chối kết nối cổng 6333 do Docker Desktop không được khởi động trên máy chủ vật lý. Việc khởi động lại Docker có thể mất thời gian và không ổn định trên các môi trường máy tính cá nhân khác nhau.

### Cơ sở lý giải
- Sử dụng `QdrantClient(path="local_db_dir")` cho phép Qdrant chạy nhúng (embedded), không cần duy trì Docker daemon.
- **Tính đồng nhất:** Mã lệnh không đổi, chỉ thay đổi URL/Port thành Path.
- **Tính gọn nhẹ:** Dữ liệu được lưu trữ trực tiếp trong thư mục dự án, dễ dàng sao lưu và di chuyển qua môi trường Lab khác.

---

## 2. Tối ưu hóa Ưu tiên Nhận diện (Detection Pre-scan Logic)

**Quyết định:** Chèn lớp Regex Việt Nam chuyên dụng trước khi chuyển văn bản cho Microsoft Presidio Engine.

### Bối cảnh
Ban đầu khi sử dụng Presidio mặc định, chuỗi số CCCD 12 số thường bị thuật toán quốc tế nhận nhầm là `DATE_TIME` hoặc số tài khoản ngân hàng Mỹ. Tương tự, nhiều từ vựng tiếng Việt bình thường lại bị nhận định sai thành `PERSON` (Tên người) hoặc `ORGANIZATION`.

### Giải pháp áp dụng (Kaizen)
1. **Phân tầng mức độ ưu tiên:** Sử dụng thư viện `re` của Python quét và ẩn danh CCCD (12 số) và Số điện thoại (prefix 03/05/07/08/09) **trước** khi đưa vào Presidio.
2. **Lọc loại nhiễu (Denied Types):** Cấu hình loại bỏ các trường thông tin không cần thiết trên văn bản tiếng Việt (như US_SSN, US_BANK) để giảm tối đa tỷ lệ False Positive.

---

## 3. Cập nhật Trí tuệ An toàn Mới nhất (Safety Engine Upgrade)

**Quyết định:** Nâng cấp từ `llama-guard-3-8b` lên `openai/gpt-oss-safeguard-20b`.

### Bối cảnh
Trong quá trình vận hành thực tế, Groq thông báo ngừng hỗ trợ (Decommissioned) phiên bản Llama Guard 3. Các truy vấn gọi đến bị trả về lỗi mã 400.

### Hành động & Lợi ích
Hệ thống được cập nhật để áp dụng phiên bản kiểm duyệt chuyên biệt mới nhất thông qua giao thức tin nhắn (messages API) của Groq. Mặc dù đòi hỏi viết lại cấu trúc Payload gửi đi, quyết định này mang lại:
- **Độ ổn định dài hạn:** Không phụ thuộc vào các API Preview sắp bị thay thế.
- **Khả năng phát hiện ngữ cảnh:** Mô hình 20B mới cho khả năng suy luận về độ an toàn cao hơn, nhận định chính xác các sắc thái tinh vi của hướng dẫn độc hại.

---

## 4. Kết luận

Việc chuyển hướng từ một hệ thống mang tính lý thuyết thuần túy sang một hệ thống có khả năng tự thích ứng lỗi (Local Qdrant fallback) và xử lý tùy biến ngôn ngữ bản địa (VN Pre-scan) đã giúp nâng cao chỉ số tin cậy của sản phẩm khi đưa vào bàn giao. 
Các quyết định trên đều nhắm đến một hệ thống có độ ổn định cao nhất dưới điều kiện tài nguyên tối thiểu.
