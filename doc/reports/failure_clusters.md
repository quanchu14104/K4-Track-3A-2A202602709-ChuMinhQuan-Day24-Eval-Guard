# Phân tích lỗi Phase A

Nhóm: {{Tên nhóm}}

Người phụ trách: Chu Minh Quân — 2A202602709.

Nguồn: `artifacts/ragas_50q.json`; run timestamp: {{created_at}}.
Generation mode/fallback và điều kiện chạy: {{Điều kiện thực tế}}.
Models generation/evaluator: {{metadata.models.generation và metadata.models.evaluator từ m4}}.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | {{factual_faithfulness}} | {{multi_faithfulness}} | {{adversarial_faithfulness}} |
| answer_relevancy | {{factual_relevancy}} | {{multi_relevancy}} | {{adversarial_relevancy}} |
| context_precision | {{factual_precision}} | {{multi_precision}} | {{adversarial_precision}} |
| context_recall | {{factual_recall}} | {{multi_recall}} | {{adversarial_recall}} |
| avg_score | {{factual_mean}} | {{multi_mean}} | {{adversarial_mean}} |

## Bottom 10 và nguyên nhân

{{Điền đúng 10 rows từ Task 3: rank, id, question, distribution, avg_score,
worst_metric, diagnosis và suggested_fix. Không thay diagnosis học viên bằng
diagnosis mặc định của exporter.}}

{{Đối chiếu answer/contexts/reference của ít nhất các câu đại diện cho nhóm lỗi;
giải thích lỗi retrieval, generation, phiên bản hoặc phủ định bằng bằng chứng.}}

## Matrix và nhóm yếu nhất

{{Điền matrix 4 metric × 3 distributions. Mỗi câu được đếm theo worst_metric,
không coi mọi câu là failure.}}

Nhóm yếu theo mean thấp nhất: {{distribution}}; mean: {{giá trị}}.
Worst metric xuất hiện nhiều nhất: {{metric}}; số câu: {{số lượng}}.

{{Giải thích vì sao nhóm đó yếu. Không dùng tổng 20/20/10 chọn dominant distribution.
Đề xuất sửa cụ thể và cách chạy lại để biết sửa có hiệu quả.}}

## Bẫy adversarial và giới hạn

{{So sánh với factual/multi_hop, nêu version conflict/negation trong bottom 10.
Điểm thấp hơn không tự chứng minh pipeline đã nhận ra bẫy. Ghi giới hạn số mẫu,
model và fallback nếu có.}}
