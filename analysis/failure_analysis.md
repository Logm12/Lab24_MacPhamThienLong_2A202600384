# Failure Analysis — Lab 18

**Nhóm:** X1000
**Thành viên:** Mạc Phạm Thiên Long

## RAGAS Scores

| Metric | Naive Baseline | Production | Δ |
|--------|---------------|------------|---|
| Faithfulness | 1.0000 | 0.9018 | -0.0982 |
| Answer Relevancy | 0.3746 | 0.4976 | +0.1229 |
| Context Precision | 0.9722 | 0.9912 | +0.0190 |
| Context Recall | 0.9211 | 0.9211 | +0.0000 |

## Bottom-5 Failures

### #1
- **Question:** Nhân viên có làm việc từ xa thì có được nghỉ phép không?
- **Expected:** Nhân viên làm việc từ xa vẫn được hưởng các ngày nghỉ phép như quy định.
- **Got:** Không tìm thấy thông tin.
- **Worst metric:** context_recall (0.0)
- **Error Tree:** Output sai (Không tìm thấy) -> Context sai (Recall=0) -> Query OK? -> Root cause: Retrieval failure (Thiếu các chunk liên quan trong kết quả trả về).
- **Suggested fix:** Em đề xuất kiểm tra lại quá trình indexing hoặc tăng số lượng chunk (top_k) được lấy ra ở bước retrieval.

### #2
- **Question:** Nhân viên có phải đăng ký nghỉ lễ không?
- **Expected:** Nhân viên thử việc không phải đăng ký nghỉ phép năm nhưng được hưởng các ngày nghỉ lễ theo quy định.
- **Got:** Không tìm thấy thông tin.
- **Worst metric:** faithfulness (0.0)
- **Error Tree:** Output sai -> Context đúng (Recall=1.0) -> Query OK? -> Root cause: LLM bị hallucination hoặc không trích xuất được thông tin từ ngữ cảnh dù đã có sẵn.
- **Suggested fix:** Em sẽ thử điều chỉnh lại prompt để hướng dẫn LLM trích xuất thông tin chi tiết hơn từ ngữ cảnh được cung cấp.

### #3
- **Question:** Nhân viên thử việc có được hưởng bảo hiểm không?
- **Expected:** Không có thông tin cụ thể trong quy định...
- **Got:** Không tìm thấy thông tin.
- **Worst metric:** answer_relevancy (0.0)
- **Error Tree:** Output đúng về mặt ý nghĩa nhưng điểm Relevancy thấp do câu trả lời quá ngắn gọn so với ground truth.
- **Suggested fix:** Em có thể cải thiện prompt để LLM trả lời đầy đủ hơn, giải thích rõ là thông tin này không có trong quy định thay vì chỉ trả về một câu ngắn.

### #4
- **Question:** Ai sẽ quyết định việc nhân viên có thể làm việc từ xa hay không?
- **Expected:** Việc làm việc từ xa phụ thuộc vào tính chất công việc và sự đồng ý của quản lý trực tiếp.
- **Got:** Quản lý trực tiếp sẽ quyết định việc nhân viên có thể làm việc từ xa hay không.
- **Worst metric:** answer_relevancy (0.0)
- **Error Tree:** Output đúng nhưng điểm số thấp do sự khác biệt về cách diễn đạt giữa câu trả lời của LLM và ground truth.
- **Suggested fix:** Đây có thể là vấn đề của metric Answer Relevancy khi so sánh hai câu có cùng ý nghĩa nhưng khác từ ngữ. Em có thể tinh chỉnh lại ground truth để bao quát hơn.

### #5
- **Question:** Nhân viên có thâm niên 7 năm sẽ được hưởng bao nhiêu ngày nghỉ phép năm?
- **Expected:** Nhân viên có thâm niên từ 5 năm trở lên sẽ được cộng thêm 1 ngày nghỉ phép, do đó tổng cộng sẽ là 13 ngày.
- **Got:** 13 ngày (nhưng tính toán sai các bước trung gian).
- **Worst metric:** faithfulness (0.33)
- **Error Tree:** Output đúng kết quả cuối nhưng các bước lập luận trong ngữ cảnh bị sai lệch so với tài liệu gốc.
- **Suggested fix:** Em nên sử dụng CoT (Chain of Thought) trong prompt để giúp LLM tính toán chính xác hơn dựa trên các con số cụ thể trong tài liệu.

## Nếu có thêm 1 giờ
- Em sẽ tập trung vào việc tinh chỉnh Prompt template để tăng cường khả năng trích xuất thông tin của LLM, giúp cải thiện điểm faithfulness và answer relevancy.
- Em cũng muốn thử nghiệm thêm kỹ thuật Query rewriting để xử lý các câu hỏi có ngôn ngữ tự nhiên phức tạp hơn.
