import os

data_dir = "data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

samples = {
    "sample_01.md": """# Quy định về Nghỉ phép năm

Nhân viên chính thức được hưởng 12 ngày nghỉ phép năm cho mỗi năm làm việc đầy đủ. 
Đối với nhân viên có thâm niên từ 5 năm trở lên, cứ mỗi 5 năm thâm niên sẽ được cộng thêm 1 ngày nghỉ phép.
Nhân viên thử việc không được nghỉ phép năm nhưng được hưởng các ngày nghỉ lễ theo quy định.
Việc đăng ký nghỉ phép phải được thực hiện qua hệ thống HR Portal trước ít nhất 3 ngày làm việc.""",

    "sample_02.md": """# Quy định Làm việc từ xa (Work from Home)

Công ty cho phép nhân viên làm việc từ xa tối đa 2 ngày mỗi tuần, tùy thuộc vào tính chất công việc và sự đồng ý của quản lý trực tiếp.
Nhân viên phải đảm bảo có kết nối internet ổn định và luôn sẵn sàng phản hồi tin nhắn/cuộc gọi trong giờ làm việc.
Chi phí điện nước và internet tại nhà do nhân viên tự chi trả.
Thiết bị làm việc (laptop) do công ty cung cấp phải được bảo quản cẩn thận.""",

    "sample_03.md": """# Quy định về Bảo hiểm và Phúc lợi

Tất cả nhân viên chính thức được đóng Bảo hiểm xã hội, Bảo hiểm y tế và Bảo hiểm thất nghiệp theo mức lương thực tế.
Ngoài ra, công ty cung cấp gói bảo hiểm sức khỏe cao cấp (PVI) cho nhân viên và người thân sau 2 năm công tác.
Thưởng tháng lương thứ 13 được chi trả vào dịp Tết Nguyên Đán cho nhân viên làm việc đủ 12 tháng.
Nhân viên được hỗ trợ chi phí ăn trưa và gửi xe hàng tháng.""",
}

for filename, content in samples.items():
    with open(os.path.join(data_dir, filename), "w", encoding="utf-8") as f:
        f.write(content)

print(f"Created {len(samples)} sample markdown files in {data_dir}")
