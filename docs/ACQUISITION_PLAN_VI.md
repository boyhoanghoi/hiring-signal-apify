# Tìm khách đầu tiên cho HiringSignal

Người cần thử trước là người đang quản lý newsletter AI/Data hoặc website việc
làm chuyên ngành và phải gom tin thủ công. Dữ liệu có link ứng tuyển, xuất được
CSV/Markdown và có cách bỏ qua tin đã lấy là phần họ có thể dùng ngay.

## Demo có thể đưa cho người dùng

1. Mở [Actor](https://apify.com/reliable_quatrain/greenhouse-lever-ashby-jobs-hiring-signal),
   dùng [input sáu tin](../examples/ai-data-newsletter.json).
2. Mở `newsletter.md`, đối chiếu vài tin với trang tuyển dụng gốc; tải CSV.
3. Chạy lại với `KNOWN_JOB_IDS` từ lần đầu để xem các mã đã lấy được bỏ qua.
   Kết quả chưa thấy trước đây không đồng nghĩa tin vừa được đăng.
4. Ghi lại công ty/nghề/địa điểm họ cần nhưng chưa tìm được; bổ sung dựa trên
   nhu cầu cụ thể thay vì chỉ tăng số Actor.

[Hướng dẫn tiếng Việt](FIRST_RUN_VI.md) và [bản nháp giới thiệu](LAUNCH_POSTS.md)
đã sẵn để chia sẻ. Dùng ảnh `assets/launch/jobs-finder.png` và nói rõ bạn là
người làm công cụ. Chọn nơi cho phép giới thiệu sản phẩm; phản hồi câu hỏi có
liên quan và tôn trọng quy định cộng đồng.

## Việc làm trong một tuần

| Bước | Việc cụ thể | Dấu hiệu cần quan sát |
| --- | --- | --- |
| Chuẩn bị | Đọc demo, kiểm tra link, tải icon và ảnh minh họa | Người mới hiểu input và mở được kết quả |
| Giới thiệu | Đăng một bài có demo ở kênh phù hợp của bạn | Có người đúng nhu cầu mở Actor |
| Dùng thử | Mời ba người đang gom tin tự thử, nếu họ đồng ý | Họ lấy được tin dùng được, biết lỗi ở đâu |
| Chỉnh sửa | Sửa trở ngại lặp lại: nguồn thiếu, lọc sai, CSV khó nhập | Giảm thao tác thủ công trong workflow thật |
| Theo dõi | Hỏi người đã thử có dùng lại trong kỳ newsletter tiếp theo | Lượt quay lại và lượt chạy có doanh thu thực |

Đây là kế hoạch kiểm chứng, không phải dự báo sẽ có ba khách hoặc doanh thu.
Chưa có bài đăng hay tin nhắn nào được gửi thay bạn.

## Đọc đúng số liệu

- Insights → Acquisition: nguồn truy cập và mức sử dụng nếu nền tảng có dữ liệu.
- Insights → Monetization: người trả phí và Profit. Lượt tự thử không chứng minh
  có khách trả tiền.
- Insights → Payouts: khoản nhận tiền sau khi đủ điều kiện của Apify.

Giá hiện cấu hình là $1.50/1.000 tin được lưu sau bộ lọc. **1.000 tin không phải
1.000 khách**; một người có thể lấy nhiều tin và chạy lại. Số tiền nhận thực còn
phụ thuộc cơ chế chia sẻ doanh thu, chi phí và điều kiện thanh toán. Mục tiêu
kiểm chứng tiếp theo là một lượt chạy tạo doanh thu từ khách thật.
