# Blueprint CI/CD cho RAG và guardrails

Nhóm: K4-L3-DAY24-ChuMinhQuan-Eval-Guard

Người phụ trách: Chu Minh Quân — 2A202602709.

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: 2026-10-12T10:21:18.464230+00:00; guard models: kr/deepseek-3.2.
Models generation/evaluator/judge từ A/B: Generation: deepseek-3.2; Evaluator: BAAI/bge-m3 và kr/deepseek-3.2; Judge: kr/deepseek-3.2.

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

### Luồng xử lý dữ liệu (Data Flow) và Cơ chế Bảo vệ:
1. **Tầng 1 - Presidio PII Scanner:** Đầu vào của người dùng trước tiên đi qua Presidio Analyzer với các bộ nhận diện Regex tùy biến cho thực thể Việt Nam (`VN_CCCD`, `VN_PHONE`) cùng các nhận diện mặc định (`EMAIL_ADDRESS`, `PHONE_NUMBER`). Nếu phát hiện PII tiêm nhiễm trong truy vấn, hệ thống dừng sớm (short-circuit), ghi log bảo mật và trả thông báo từ chối.
2. **Tầng 2 - NeMo Input Rails:** Nếu không có PII độc hại, input được kiểm tra qua Colang 1.0 và LLM self-check input rail để phát hiện prompt injection, jailbreak (DAN), hoặc các yêu cầu ngoài phạm vi nội quy công ty (off-topic như giải toán, nấu ăn). Nếu vi phạm, yêu cầu bị chặn ngay lập tức.
3. **Tầng 3 - RAG Retrieval & Generation:** Truy vấn hợp lệ được chuyển đến Hybrid Search (BM25 + Qdrant Dense Vector) kết hợp Cross-Encoder Reranker để tìm top-k contexts phù hợp nhất và sinh câu trả lời bằng LLM.
4. **Tầng 4 - NeMo Output Rails:** Câu trả lời sinh ra được đối chiếu qua self-check output rail nhằm kiểm tra rò rỉ dữ liệu cá nhân của người khác, lộ mật khẩu quản trị, hoặc nội dung không an toàn. Nếu phát hiện vi phạm, hệ thống tiến hành ẩn/thay thế bằng thông điệp an toàn (`[REDACTED]`).
5. **Quản lý Secrets và Fallback:** Tất cả API keys và tokens (`OPENAI_API_KEY`) được lưu trữ trong biến môi trường hoặc Secret Manager, không commit vào kho mã nguồn. Trong trường hợp dịch vụ LLM bị gián đoạn hoặc quá tải (HTTP 429/503), pipeline kích hoạt cơ chế retry với exponential backoff hoặc chuyển sang extractive fallback từ top contexts.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2;
phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 9.89 | 12.06 | 13.25 | Hoạt động cực nhanh trên CPU (<15ms) |
| NeMo input | 931.26 | 2179.70 | 2235.65 | Bottleneck chính do gọi LLM qua mạng |
| Input guard sequential | 940.53 | 2190.04 | 2246.72 | Vượt ngưỡng ngân sách đề xuất |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế/budget_ok: P95 = 2190.04 ms; budget_ok: False.

### Phân tích Bottleneck và Kế hoạch Tối ưu:
- **Phân tích:** Presidio chạy bằng regex và spaCy trên CPU nội bộ nên độ trễ P95 chỉ đạt 12.06 ms (rất nhỏ, chiếm <1% tổng thời gian). Ngược lại, NeMo input guard phụ thuộc hoàn toàn vào round-trip gọi LLM qua mạng Internet (`kr/deepseek-3.2`), dẫn đến P95 lên tới 2179.70 ms và làm toàn bộ tầng guard đầu vào vượt ngưỡng 500ms.
- **Kế hoạch giải quyết:** Trong kiến trúc production thực tế, tầng guardrail đầu vào cần thay thế bằng mô hình local nhỏ được tối ưu hóa riêng biệt (ví dụ: mô hình phân loại intent/jailbreak bằng DeBERTa/BERT nội bộ hoặc vLLM on-premise) nhằm cắt giảm độ trễ mạng xuống dưới 100ms, đảm bảo P95 toàn hệ thống đạt dưới 300ms.

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu.
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng 4/4.
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.

### Thiết kế Automated Quality Gate Script:
Đề xuất tích hợp job kiểm tra chất lượng tự động trong GitHub Actions workflow. Job sẽ chạy các bước kiểm tra thực nghiệm và trả về mã thoát khác 0 nếu bất kỳ tiêu chí nào không đạt:
```bash
# Lệnh thực thi quality gates trong quy trình CI:
python scripts/run_experiments.py --phase a --live
python scripts/run_experiments.py --phase b --live
python scripts/run_experiments.py --phase c --live --latency-samples 20
python scripts/check_lab.py --with-tests
```
Nếu bất kỳ assertion hoặc schema check nào thất bại, runner trả về exit code 1, ngăn chặn việc merge pull request vào nhánh chính. Hiện tại đây là đề xuất blueprint thiết kế, chưa kích hoạt tự động trên remote workflow server.

## Monitoring và cải tiến

### Hệ thống Giám sát Vận hành (Production Monitoring):
- **Chỉ số theo dõi liên tục:** Tỷ lệ vi phạm PII theo giờ, tỷ lệ chặn input (blocking rate), độ trễ P50/P95/P99 theo từng tầng guard, và điểm phản hồi từ người dùng cuối (thumbs up/down).
- **Cảnh báo bất thường (Alerting thresholds):** Kích hoạt cảnh báo PagerDuty/Slack nếu tỷ lệ chặn input tăng đột biến vượt quá 15% trong 10 phút (dấu hiệu tấn công DoS hoặc false positive trên diện rộng), hoặc khi độ trễ P95 vượt ngưỡng 1000ms.
- **Xử lý False Positives:** Lưu vết log truy vấn bị chặn (đã được băm/ẩn thông tin nhạy cảm) để kỹ sư bảo mật và chuyên gia chính sách nhân sự định kỳ gán nhãn lại hàng tuần, cập nhật từ khóa whitelist cho regex Presidio.
- **Giới hạn bộ dữ liệu:** Bộ dữ liệu kiểm thử hiện tại gồm 50 câu hỏi RAG, 20 câu adversarial, 8 câu clean và 4 câu output. Kích thước này đủ để đánh giá baseline ban đầu nhưng cần được mở rộng liên tục bằng dữ liệu thật trong vận hành.

### Thống kê thực nghiệm chính:
RAGAS mean/worst distribution: multi_hop với mean 0.7053 (factual đạt 0.8484).
Cohen’s κ: 1.00.
Attacks passed: 15/20; clean false_positive_rate: 0.00.

### 4 Đề xuất cải tiến cụ thể:
1. **Nâng cấp Chunking & Reranking:** Mở rộng `RERANK_TOP_K` từ 3 lên 5 và bổ sung tóm tắt metadata bằng M5 enrichment đầy đủ để cải thiện điểm `context_recall` của nhóm câu hỏi multi-hop từ 0.65 lên trên 0.80.
2. **Triển khai Guard Model On-Premise:** Đưa mô hình phân loại intent nhỏ (như Llama-Guard hoặc FastText/DeBERTa) về chạy local nhằm giảm P95 latency của NeMo input từ 2190ms xuống dưới 200ms.
3. **Mở rộng nhận diện PII đặc thù doanh nghiệp:** Thêm recognizer cho mã định danh nhân viên nội bộ (Employee ID: format `NV-[0-9]{5}`) và số tài khoản ngân hàng để tăng cường độ phủ bảo mật.
4. **Cơ chế Active Learning cho LLM Judge:** Thu thập các cặp câu trả lời có độ bất đồng cao giữa Pass 1 và Pass 2 để chuyên viên nhân sự gán nhãn thủ công, dùng làm bộ dữ liệu few-shot calibration định kỳ cho judge prompt.
