# Nhóm thực hiện K4 Track 3A

Tên nhóm: {{Tên nhóm}}

Repo chung: {{Link repo}}

Người nộp (theo thông tin đã cung cấp): Chu Minh Quân — 2A202602709.

Ngày lab/deadline áp dụng: {{Ngày giờ theo thông báo lớp}} — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: {{Commit SHA}}

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Chu Minh Quân | 2A202602709 | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 2 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 3 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |

Người tích hợp/chạy batch/nộp link: {{Họ tên, công việc và bằng chứng}}.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows; CPython 3.11.0 trong `.venv311`; MSVC C++ Build
Tools đã được cài đặt. Phiên bản Windows cụ thể chưa được ghi nhận.
Virtualenv/dependencies/imports: `.venv311`; kiểm tra gần nhất:
`python -m pytest tests/ -m "not integration" -q --tb=short` — 106 passed,
3 deselected. `pip check` sạch ở lần kiểm tra môi trường trước.
Models/Qdrant/50 answers đã chuẩn bị: chat smoke tests generation/judge và
RAGAS một mẫu thành công với Nemotron trên endpoint cấu hình; BGE-M3 local
trả embedding 1024 chiều; Qdrant health check thành công. M5 đặt `local` mode
cho 107 chunks. **Không tạo được `answers_50q.json`**: upstream báo hết quota
free model 50 requests/ngày; cần chờ reset hoặc có quota hợp lệ. Hai PDF scan
không có text layer bị bỏ qua, chưa OCR.
NeMo `RailsConfig.from_path` parse config thành công; full `LLMRails` run chưa
được xác minh vì quota đã hết. Không suy ra full-runtime tương thích từ unit
tests hoặc config parse.

## INDIVIDUAL

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### ChuMinhQuan-2A202602709

- Phần được giao và phần thực tế đã làm: {{Nhiệm vụ, file/hàm, mục đích}}.
- Bằng chứng: {{Commit/PR và artifacts/reports liên quan}}.
- Cách kiểm tra: {{Unit mock hoặc live experiment, lệnh và kết quả}}.
- Điều đã học: {{Khái niệm và cách thể hiện trong bài}}.
- Giới hạn/cách xử lý: {{Vấn đề và kiểm chứng}}.
- Nguồn/AI hỗ trợ nếu có: {{Công cụ, phạm vi, cách tự kiểm chứng}}.

## Cập nhật sau khi nộp

{{Ghi phiên bản nộp; nếu sửa sau deadline, ghi commit/thời điểm/lý do và thông báo
coach cho phép áp dụng bản cập nhật. Nếu không có cập nhật, ghi rõ không có.}}
