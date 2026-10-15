# Dùng HiringSignal vào công việc thật

## Gom tin cho website việc làm hoặc newsletter

Khách phù hợp là người đã có danh sách công ty muốn theo dõi. Actor đọc board
của các công ty đó; không tự tìm mọi công ty hoặc mọi việc làm trên internet.

1. Mở Actor, nhập các board trong `boards` và đặt giới hạn nhỏ trước.
2. Dùng `includeTitleKeywords` cho các từ như `engineer`, `data`; thêm
   `excludeTitleKeywords` nếu cần loại các vị trí không phù hợp.
3. Chạy rồi xem dataset: tiêu đề, địa điểm, mô tả, link việc làm và nguồn.
4. Kiểm tra `DIAGNOSTICS` trước khi dùng số tin để so sánh các công ty: board bị
   lỗi hoặc chạm giới hạn không đại diện cho toàn bộ nhu cầu tuyển dụng.
5. Xuất CSV cho bảng tính, hoặc lấy dataset JSON qua API để cập nhật website.

`remoteOnly` chỉ giữ tin có trường remote rõ ràng từ nguồn. Tin ghi remote
không đồng nghĩa được làm việc từ mọi quốc gia. Khi lọc `publishedAfter`, tin
không có ngày đăng đáng tin sẽ bị loại; ngày cập nhật không bị đổi thành ngày đăng.

## Lần sau chỉ lấy mã tin chưa lưu

Sau lần chạy thành công, mở Output và lấy JSON từ `KNOWN_JOB_IDS`. Truyền nguyên
mảng đó vào `knownJobIds` ở đầu vào lần tiếp theo. Các mã đã có sẽ bị bỏ qua
trước khi lưu hoặc tính phí.

Với n8n/Make hoặc chương trình riêng, quy trình là: đọc mảng mã đã lưu → gọi
Actor → lấy dataset và `KNOWN_JOB_IDS` mới → lưu kết quả → thay mảng mã cũ bằng
mảng mới. Lưu trạng thái trong nơi bạn quản lý; chỉ gắn lịch chạy cùng một input
cố định sẽ không tự cập nhật mảng này.

Mảng có giới hạn 10.000 mã gần nhất; xem `knownJobIdsTruncated` trong SUMMARY.
Tin cũ ngoài cửa sổ đó có thể xuất hiện lại. Đây là cách bỏ qua mã đã lưu,
không phải theo dõi chỉnh sửa của tin hoặc xác định tin đã đóng.

## Hiểu đơn vị tính phí

Một kết quả là một tin được chuẩn hóa, qua bộ lọc và thực sự được lưu, không
phải một người dùng. Một khách có thể xử lý nhiều tin trong một lần chạy.
Không tính sự kiện cho board lỗi/rỗng, mã đã biết hoặc tin bị bộ lọc loại.
Giá đang có hiệu lực phải xem tại Pricing của Actor.
