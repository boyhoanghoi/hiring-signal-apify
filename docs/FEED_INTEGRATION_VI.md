# Xuất feed cho website việc làm và newsletter

Mỗi lần chạy có thêm hai file: `jobs.rss` theo RSS 2.0 và `jobs.feed.json`
theo JSON Feed 1.1. Mở tab **Output** của lần chạy để tải; CLI lưu hai file
bên cạnh `results.csv`. Các file chỉ chứa tin đã lưu thành công sau bộ lọc,
danh sách mã cũ và giới hạn chi phí. Xuất thêm định dạng không tạo thêm
phí sự kiện Actor.

Ví dụ lấy các tin Data/AI có loại hợp đồng toàn thời gian được nguồn ghi rõ:

```json
{
  "companyGroup": "ai",
  "rolePreset": "data-ai",
  "employmentTypes": ["full-time"],
  "maxJobs": 6,
  "maxJobsPerBoard": 2
}
```

`employmentTypes` nhận `full-time`, `part-time`, `contract`, `temporary`,
`internship`, `freelance`, `apprenticeship`, `unknown`. Danh sách rỗng không
lọc loại hợp đồng. Công cụ chỉ chuẩn hóa nhãn rõ ràng do Lever/Ashby cung cấp;
không đoán từ tiêu đề hay nội dung. Nhãn thiếu hoặc mơ hồ là `unknown`.
Greenhouse thường thiếu trường này nên có thể bị loại khi chỉ chọn `full-time`.

Để tích hợp vào website của bạn:

1. Chạy thử nhỏ và kiểm tra `SUMMARY`, `DIAGNOSTICS`, đường dẫn ứng tuyển.
2. Nhập file feed vào hệ thống hỗ trợ đúng định dạng tương ứng.
3. Dùng `items[].id` của JSON Feed hoặc `guid` của RSS làm khóa chống trùng.
4. Nếu cần một địa chỉ đăng ký feed cố định, workflow của bạn phải đưa file
   lên hosting và cập nhật sau mỗi lần chạy thành công. Đây là file của từng
   lần chạy, chưa phải dịch vụ feed tự cập nhật. Không đưa API token vào URL công khai.
5. Muốn lấy tiếp tin chưa lưu, giữ `KNOWN_JOB_IDS` rồi truyền vào lần chạy sau.
   Feed mới chỉ có tin của lần đó; hãy gộp vào kho lưu trữ của bạn. Không xóa
   tin cũ chỉ vì nó vắng mặt trong một lần xuất.

Mỗi mô tả feed lấy tối đa 2.000 ký tự từ mô tả nguồn và có báo rút gọn.
Dataset JSON vẫn giữ giới hạn mô tả 12.000 ký tự. Ngày quan sát không được
thay vào ngày đăng bị thiếu; ngày Ashby là lần công bố gần nhất. Thứ tự là
thứ tự nguồn, không bảo đảm mới nhất đứng đầu. Remote không bảo đảm nhận
ứng viên từ mọi quốc gia.

Nếu mọi nguồn đã thử đều lỗi, lần chạy báo thất bại và vẫn lưu chẩn đoán,
file rỗng cùng danh sách mã cũ. Nguồn chạy thành công nhưng không có tin
hoặc không khớp bộ lọc vẫn là kết quả hợp lệ. Không có tin được lưu thì
không phát sinh sự kiện `job-saved`; chi phí hạ tầng vẫn có thể tồn tại.

Xem thêm [hướng dẫn tích hợp tiếng Anh](FEED_INTEGRATION.md).
