# Đánh giá LLM Judge Phase B

Nhóm: K4-L3-DAY24-ChuMinhQuan-Eval-Guard

Người phụ trách: Chu Minh Quân — 2A202602709.

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T10:04:41.250213+00:00.
Models generation/judge: Generation: deepseek-3.2; Judge: kr/deepseek-3.2.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

| ID | Ứng viên A / B | Thắng lượt 1 | Thắng lượt 2 (quy về A/B) | Người thắng chung cuộc | Nhất quán vị trí | Điểm lượt 1 / lượt 2 | Lý do chính |
|---|---|---|---|---|---|---|---|
| 1 | A: Dựa trên ngữ cảnh, nhân viên được nghỉ **3 ng...<br>B: Nhân viên được nghỉ 3 ngày làm việc có lương ... | B | B | B | Có | A:0.8, B:1.0 / A:0.8, B:1.0 | Answer B matches reference exactly on content and concisenes... |
| 5 | A: Dựa trên context, quy trình phê duyệt đơn hàn...<br>B: Cần Giám đốc phòng ban phê duyệt.... | A | A | A | Có | A:0.7, B:0.0 / A:1.0, B:0.0 | Reference nói đơn >50 triệu cần CEO phê duyệt. Answer_A đúng... |
| 12 | A: Dựa trên ngữ cảnh, thưởng Tết tối thiểu cho n...<br>B: Nhân viên được thưởng Tết tối thiểu 1 tháng l... | A | A | A | Có | A:1.0, B:0.7 / A:0.9, B:0.7 | A trích dẫn chính xác mức thưởng tối thiểu và điều kiện 'từ ... |
| 21 | A: Dựa trên context, một nhân viên Senior có 9 n...<br>B: Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm ni... | B | B | B | Có | A:0.7, B:1.0 / A:0.8, B:1.0 | Câu trả lời B chính xác và đầy đủ, khớp hoàn toàn với refere... |
| 41 | A: Theo Chính sách nghỉ phép năm Phiên bản 2024 ...<br>B: Nhân viên được nghỉ 12 ngày phép năm.... | A | A | A | Có | A:1.0, B:0.0 / A:1.0, B:0.0 | Câu trả lời A chính xác khi nêu số ngày theo chính sách hiện... |

Position bias count/rate: 0 / 0.00 (0%).
Verbosity win rate: 0.60 (60%); decisive cases: 5.

### Phân tích thiên lệch và tính nhất quán:
- **Position Consistency:** Toàn bộ 5/5 cặp câu hỏi đều cho kết quả nhất quán giữa 2 lượt hoán đổi (Pass 1: A vs B, Pass 2: B vs A). Tỷ lệ position bias là 0%, cho thấy mô hình `kr/deepseek-3.2` với temperature=0 có khả năng bám sát reference ground-truth mà không phụ thuộc vào việc câu trả lời xuất hiện ở vị trí đầu hay sau.
- **Verbosity Win Rate:** Trong 5 trường hợp quyết định, có 3 trường hợp câu trả lời dài hơn giành chiến thắng (tỷ lệ 60%). Phân tích chi tiết nội dung cho thấy ở các câu ID 5, 12, 41, ứng viên A thắng vì cung cấp đầy đủ căn cứ điều khoản cụ thể (chính sách hiện hành v2024, phân cấp phê duyệt thẩm quyền) chứ không chỉ đơn thuần vì độ dài câu chữ. Ngược lại ở câu ID 21, ứng viên B ngắn hơn nhưng súc tích và đúng trọng tâm nên vẫn giành chiến thắng áp đảo.

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json;
không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference.
Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

| Câu ID | Model Answer đánh giá | Nhãn Judge (0/1) | Nhãn Human (0/1) | Đối chiếu | Lập luận của Judge |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi k... | 1 | 1 | Khớp | Câu trả lời chính xác theo reference, đủ ý thiết yếu về số ngày (... |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | 0 | Khớp | Answer sai so với reference: reference yêu cầu Tổng Giám đốc (CEO... |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | 1 | Khớp | Answer chính xác theo reference: đối tượng là nhân viên chính thứ... |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). ... | 1 | 1 | Khớp | Câu trả lời đúng về cả số ngày phép (18 ngày, gồm 15 cơ bản và 3 ... |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | 1 | Khớp | Answer đúng nội dung chính: nhân viên nghỉ trước hạn cam kết (8 t... |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu... | 0 | 0 | Khớp | Answer sai về quyền phê duyệt (thiếu Kế toán trưởng) và tính sai ... |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | 1 | Khớp | Answer chính xác tổng phụ cấp tháng (1.500.000 VNĐ) và số ngày ph... |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | 0 | Khớp | Câu trả lời (12 ngày) sử dụng phiên bản chính sách cũ (v2023) đã ... |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phả... | 1 | 1 | Khớp | Answer chính xác theo reference: khẳng định nhân viên thử việc kh... |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | 0 | Khớp | Reference rõ ràng cấm sử dụng VPN cá nhân (NordVPN, ExpressVPN), ... |

Cohen’s κ: 1.00.
Observed/chance agreement và diễn giải: Độ tương đồng quan sát (Observed Agreement) đạt 10/10 (100.0%); Chance Agreement đạt 50.0% (với 5 nhãn 1 và 5 nhãn 0 phân bố đều); do đó hệ số Cohen's Kappa đạt mức tuyệt đối 1.00 (hoàn toàn đồng thuận). Điều này minh chứng prompt binary calibration đã hướng dẫn giám khảo LLM bám sát các tiêu chuẩn khắt khe về tính đúng đắn, không bỏ sót điều kiện tiên quyết và tuân thủ đúng phiên bản hiệu lực.

## Giới hạn và cách dùng judge

- **Mô hình và Prompting:** Quá trình đánh giá sử dụng mô hình `kr/deepseek-3.2` với temperature=0. Prompt yêu cầu trả định dạng JSON nghiêm ngặt và giải thích lý do cụ thể trước khi cho điểm.
- **Quy mô mẫu:** Kích thước mẫu thử nghiệm gồm 5 cặp so sánh pairwise và 10 mẫu nhãn binary chuẩn hóa từ con người. Mặc dù hệ số Kappa đạt 1.00 trên tập dữ liệu này, việc áp dụng vào môi trường production quy mô lớn vẫn cần thận trọng vì phân bố câu hỏi thực tế đa dạng hơn rất nhiều.
- **Khuyến nghị vận hành:** Không xem LLM Judge là chân lý tuyệt đối thay thế con người. Trong quy trình CI/CD và QA thực tế, LLM Judge nên được sử dụng làm bộ lọc tự động tầng 1 để cảnh báo các câu trả lời có nguy cơ hallucination hoặc vi phạm chính sách; các trường hợp điểm số biên (marginal score) hoặc câu trả lời có độ rủi ro cao vẫn cần con người kiểm duyệt định kỳ (Human-in-the-loop).
