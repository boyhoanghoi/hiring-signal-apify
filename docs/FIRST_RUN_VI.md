# Tạo danh sách việc AI/Data đầu tiên

Hướng dẫn này dành cho người làm newsletter hoặc website việc làm theo ngách.
HiringSignal đọc các bảng tuyển dụng công khai đã chọn, lọc tin rồi xuất dữ
liệu và bản nháp Markdown để bạn kiểm tra trước khi đăng.

## 1. Chạy thử với giới hạn nhỏ

Mở [HiringSignal trên Apify](https://apify.com/reliable_quatrain/greenhouse-lever-ashby-jobs-hiring-signal),
chuyển sang JSON input và thay toàn bộ đầu vào bằng:

```json
{
  "companyGroup": "ai",
  "rolePreset": "data-ai",
  "maxJobs": 6,
  "maxJobsPerBoard": 2,
  "knownJobIds": []
}
```

Xem tab Pricing và đặt giới hạn chi tiêu nhỏ phù hợp với ước tính Apify hiển
thị trước khi chạy. Với giá Actor đang cấu hình, sáu tin thực sự được lưu tạo
**$0.009 phí sự kiện job-saved**. Đây là phép tính phí sự kiện, không cam kết
luôn có sáu kết quả hay bao gồm toàn bộ phí hạ tầng.

`ai` là danh sách công ty chọn sẵn có phạm vi giới hạn. Actor không tìm mọi
công ty AI trên internet. Nếu giữ `boards` từ đầu vào cũ, các board đó chạy
trước và được gộp với nhóm chọn sẵn. Hãy thay toàn bộ input như ví dụ nếu chỉ
muốn dùng nhóm AI. Số tin và khả năng truy cập nguồn có thể thay đổi; ít hơn
sáu tin hoặc không có tin phù hợp đều có thể là kết quả hợp lệ.

## 2. Đọc kết quả và chuẩn bị nội dung

- **Dataset / jobs:** xem tiêu đề, tên hiển thị công ty, địa điểm và link ứng
  tuyển. Mở tin gốc để kiểm tra điều kiện đang có hiệu lực.
- **newsletter.md:** bản nháp danh sách việc bằng Markdown, chỉ gồm các tin đã
  thực sự lưu. Bạn có thể chỉnh sửa rồi dùng trong newsletter của mình.
- **results.csv:** nhập vào bảng tính hoặc quy trình cập nhật website việc làm.
  JSON dùng cho chương trình tích hợp.
- **SUMMARY / DIAGNOSTICS:** kiểm tra nguồn lỗi, giới hạn và mức độ bao phủ.
  Sáu tin đã lưu không có nghĩa các công ty đó chỉ có tổng cộng sáu vị trí.
- **EMPLOYER_CATALOG:** xem danh sách công ty, mã board và từ khóa lọc vai trò
  mà phiên bản này cung cấp.
- **KNOWN_JOB_IDS:** giữ lại mảng JSON này cho lần chạy sau.

Thứ tự bản nháp theo nguồn, không phải tin mới nhất trước. Mã chưa từng lưu
có thể thuộc một tin cũ. Remote chỉ dựa vào trường rõ ràng từ nguồn, không
đảm bảo ứng viên ở Việt Nam hay mọi quốc gia đều được tuyển. Đọc điều kiện
địa lý và quyền làm việc trên tin gốc trước khi chia sẻ hoặc ứng tuyển.

## 3. Lần sau bỏ qua mã đã lưu

Lấy nguyên mảng trong `KNOWN_JOB_IDS` của lần đầu và dán vào `knownJobIds` ở
lần tiếp theo. Mẫu sau dùng chuỗi minh họa; **phải thay bằng mảng thực tế**:

```json
{
  "companyGroup": "ai",
  "rolePreset": "data-ai",
  "maxJobs": 6,
  "maxJobsPerBoard": 2,
  "knownJobIds": ["dan-jobKey-da-luu-thu-nhat-vao-day", "dan-jobKey-tiep-theo-vao-day"]
}
```

Các mã đã truyền vào bị bỏ qua trước khi lưu và tính phí. Với giới hạn nhỏ,
lần sau có thể lấy thêm tin khác còn tồn tại từ lần trước; điều đó không chứng
minh công ty vừa đăng việc mới. Tin đã thấy cũng không được đọc lại để phát
hiện chỉnh sửa. Không dùng việc mã chưa biết để gắn nhãn "vừa đăng".

Mỗi lần chạy trả về hợp của mã cũ và tin thực sự lưu mới, giữ tối đa 10.000 mã.
Khi danh sách đầy, `knownJobIdsTruncated` báo mã cũ bị bỏ; các mã bị bỏ có thể
xuất hiện lại. Nếu tự động hóa, bạn phải lưu mảng trả về rồi truyền sang lần
chạy sau. Chỉ đặt lịch với một input cố định sẽ không tự cập nhật trạng thái.

## 4. Đổi nhóm công ty và loại việc

`companyGroup` nhận `none`, `ai`, `developer-tools`, `fintech` hoặc `all`.
`rolePreset` nhận `all`, `data-ai`, `engineering`, `product-design` hoặc
`sales-marketing`. Bộ lọc vai trò dùng từ/cụm từ xác định trong tiêu đề, không
phân tích độ phù hợp của ứng viên hay tự hiểu mọi mô tả việc làm.

Nếu đã có danh sách riêng, chọn `companyGroup: "none"` và truyền `boards`, ví
dụ `greenhouse:stripe` hoặc `ashby:ashby`. Nếu chọn cả nhóm và `boards`, Actor
gộp các board không trùng, board tự nhập chạy trước; tổng tối đa 30 board.
Các bộ lọc bổ sung kết hợp với preset bằng AND. Trong từng danh sách từ khóa
hoặc địa điểm, chỉ cần khớp một chuỗi; điều kiện loại trừ luôn được ưu tiên.

Hãy xem dữ liệu trước rồi mới thêm giới hạn địa điểm/remote. `remoteOnly: true`
loại tin hybrid và không rõ trạng thái; feed danh sách của Greenhouse thường
không có trường remote rõ ràng. `publishedAfter` loại tin không biết ngày đăng.
Ngày cập nhật không bị dùng thay ngày đăng; Lever thường thiếu ngày đăng công
khai, còn ngày của Ashby mang nghĩa lần công bố gần nhất.

## Chạy bằng Python trên máy

Mở terminal tại thư mục dự án trên Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[actor]"
.\.venv\Scripts\python.exe -m hiringsignal catalog
.\.venv\Scripts\python.exe -m hiringsignal run --input examples/ai-data-newsletter.json --output output
```

Mở `output/newsletter.md`, `output/results.csv`, `output/diagnostics.json` và
`output/known_job_ids.json`. Chạy lần sau với danh sách mã đã lưu:

```powershell
.\.venv\Scripts\python.exe -m hiringsignal run --input examples/ai-data-newsletter.json --previous-ids output/known_job_ids.json --output output-next
```

`--previous-ids` đọc mảng JSON đã xuất và gộp với `knownJobIds` trong input.
Tổng danh sách đầu vào vẫn phải nằm trong giới hạn 10.000 mã; CLI không tự
âm thầm bỏ mã để vượt bước kiểm tra. Lần sau nữa đọc
`output-next/known_job_ids.json` và ghi sang thư mục kết quả khác.

Sau khi kích hoạt môi trường ảo, có thể dùng `hiringsignal catalog` và
`hiringsignal run ...` trực tiếp. Chạy CLI trên máy không phát sinh sự kiện
tính phí Apify, nhưng vẫn dùng tài nguyên máy và gửi yêu cầu tới các feed nguồn.

## Trước khi dùng thực tế

Kiểm tra tin gốc còn nhận ứng tuyển, điều kiện địa lý và quyền sử dụng nội dung.
Actor không suy ra tin đã đóng từ sự vắng mặt, không đo toàn bộ nhu cầu tuyển
dụng bằng số tin đã lưu và không bảo đảm có doanh thu cho người vận hành.
Actor không nộp đơn, gửi email hay tự đăng newsletter. Xem
[mô tả sản phẩm đầy đủ](../.actor/README.md) để hiểu các trường và giới hạn.
