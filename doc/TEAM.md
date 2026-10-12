# Nhóm thực hiện K4 Track 3A

Tên nhóm: K4-L3-DAY24-ChuMinhQuan-Eval-Guard

Repo chung: https://github.com/quanchu14104/K4-Track-3A-2A202602709-ChuMinhQuan-Day24-Eval-Guard

Người nộp (theo thông tin đã cung cấp): Chu Minh Quân — 2A202602709.

Ngày lab/deadline áp dụng: 12/10/2026 — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: 99a4cf7

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Chu Minh Quân | 2A202602709 | Toàn bộ bài lab: module m1-m5, Phase A (RAGAS), Phase B (LLM Judge), Phase C (Guardrails), chạy thực nghiệm sinh 4 artifacts và hoàn thiện 3 báo cáo | Commit 99a4cf7; artifacts answers_50q.json, ragas_50q.json, judge_results.json, guard_results.json |

Người tích hợp/chạy batch/nộp link: Chu Minh Quân — tích hợp toàn bộ pipeline, chạy batch setup sinh 50 answers và thực nghiệm 3 phase, kiểm tra đạt toàn bộ test và nộp link repo.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11; CPython 3.11.0 trong `.venv311`; MSVC C++ Build
Tools đã được cài đặt đầy đủ.
Virtualenv/dependencies/imports: Môi trường ảo `.venv311`; kiểm tra toàn bộ
`python -m pytest tests/ -q` đạt 106 passed, 3 deselected; `pip check` sạch.
Models/Qdrant/50 answers đã chuẩn bị:
- Qdrant vector database đang hoạt động trên localhost:6333, collection lab24_production.
- Embedding BGE-M3 local trả vector 1024 chiều.
- Endpoint LLM 9Router tương thích OpenAI hoạt động ổn định với mô hình `kr/deepseek-3.2`.
- Đã sinh hoàn chỉnh `artifacts/answers_50q.json` gồm 50 câu trả lời từ RAG pipeline (20 factual, 20 multi_hop, 10 adversarial).
- M5 enrichment thực thi chế độ local deterministic trên 107 chunks tài liệu.
- NeMo Guardrails cấu hình với `ChatOpenAI` provider tích hợp mượt mà với Colang 1.0 rails.

## INDIVIDUAL

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### ChuMinhQuan-2A202602709

- Phần được giao và phần thực tế đã làm: Phụ trách toàn bộ bài lab. Tích hợp 5 module RAG từ Day 18 (m1_chunking, m2_search, m3_rerank, m4_eval, m5_enrichment). Hoàn thành toàn bộ các hàm TODO trong Phase A (phân nhóm câu hỏi, chạy 4 metrics RAGAS, lọc bottom 10 và lập ma trận chẩn đoán lỗi), Phase B (pairwise LLM judge 2 lượt đảo vị trí, phát hiện position và verbosity bias, calibration 0/1 với 10 nhãn người, tính hệ số Cohen's Kappa), và Phase C (Presidio PII regex scanner cho CCCD/SĐT/Email, NeMo input/output rails, đo latency P50/P95/P99). Sinh đầy đủ 4 artifacts thực nghiệm và viết 3 báo cáo kỹ thuật.
- Bằng chứng: Commit 99a4cf7 trên GitHub; 4 file kết quả thực nghiệm trong `artifacts/` (answers_50q.json, ragas_50q.json, judge_results.json, guard_results.json); và 3 báo cáo chi tiết trong `doc/reports/` (failure_clusters.md, bias_report.md, blueprint.md).
- Cách kiểm tra: Kiểm tra tự động bằng lệnh `python -m pytest tests/ -q` (106 passed); chạy batch thực nghiệm live cho cả 3 phase bằng `python scripts/run_experiments.py`; kiểm tra độ hợp lệ của toàn bộ submission bằng `python scripts/check_lab.py --with-tests`.
- Điều đã học: Nắm vững phương pháp đánh giá định lượng RAG thông qua bộ 4 chỉ số RAGAS (faithfulness, answer_relevancy, context_precision, context_recall); hiểu cơ chế hoạt động và cách triệt tiêu thiên lệch (position/verbosity bias) của LLM-as-a-Judge bằng kỹ thuật swap-and-average; đo lường độ tin cậy bằng Cohen's Kappa; thiết kế hệ thống phòng thủ đa tầng kết hợp Presidio PII và NeMo Guardrails để ngăn chặn prompt injection, jailbreak và rò rỉ dữ liệu nhạy cảm.
- Giới hạn/cách xử lý: Độ trễ P95 của tầng NeMo input guard còn cao do gọi API mô hình LLM qua mạng internet; đã phân tích nguyên nhân và đề xuất phương án thay thế bằng mô hình phân loại intent nhỏ on-premise trong báo cáo blueprint.
- Nguồn/AI hỗ trợ nếu có: Sử dụng công cụ AI coding assistant để hỗ trợ rà soát cấu trúc mã nguồn, cấu hình endpoint proxy 9Router và debug tương thích; toàn bộ thử nghiệm và số liệu đều được chạy thực tế trên máy tính cá nhân.

## Cập nhật sau khi nộp

Bản nộp chính thức trước hạn deadline ngày 12/10/2026; không có cập nhật bổ sung nào sau hạn nộp.
