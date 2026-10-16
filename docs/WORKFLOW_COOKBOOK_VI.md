# Dùng HiringSignal vào công việc thật

[Bắt đầu với nhóm AI/Data, sáu tin và bản nháp newsletter](FIRST_RUN_VI.md)
hoặc xem [hướng dẫn tiếng Anh](FIRST_RUN.md). Ví dụ mới dùng nhóm công ty có
sẵn; bạn vẫn có thể tự nhập watchlist như quy trình dưới đây.

## Gom tin cho website việc làm hoặc newsletter

Khách phù hợp là người làm newsletter, website việc làm hoặc theo dõi tuyển
dụng ở một nhóm công ty. Chọn `companyGroup` và `rolePreset` có sẵn, hoặc tự
nhập board của các công ty muốn theo dõi. Actor không tìm mọi công ty hoặc mọi
việc làm trên internet.

1. Mở Actor, chọn nhóm công ty hoặc nhập `boards`, đặt giới hạn nhỏ trước.
2. Dùng `includeTitleKeywords` cho các từ như `engineer`, `data`; thêm
   `excludeTitleKeywords` nếu cần loại các vị trí không phù hợp.
3. Chạy rồi xem dataset: tiêu đề, địa điểm, mô tả, link việc làm và nguồn.
4. Kiểm tra `DIAGNOSTICS` trước khi dùng số tin để so sánh các công ty: board bị
   lỗi hoặc chạm giới hạn không đại diện cho toàn bộ nhu cầu tuyển dụng.
5. Xuất CSV cho bảng tính, hoặc lấy dataset JSON qua API để cập nhật website.

`newsletter.md` là bản nháp Markdown từ các tin thực sự đã lưu để bạn kiểm tra
và chỉnh sửa. Actor không tự đăng newsletter; thứ tự theo nguồn, không phải
tin mới nhất trước. Dùng `hiringsignal catalog` trên CLI hoặc xem
`EMPLOYER_CATALOG` trong Output để kiểm tra danh sách chọn sẵn và từ khóa preset.

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
