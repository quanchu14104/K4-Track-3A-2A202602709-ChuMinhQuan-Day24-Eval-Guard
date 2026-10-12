# Phân tích lỗi Phase A

Nhóm: K4-L3-DAY24-ChuMinhQuan-Eval-Guard

Người phụ trách: Chu Minh Quân — 2A202602709.

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T09:57:09.500924+00:00.
Generation mode/fallback và điều kiện chạy: Thực nghiệm live bằng mô hình generation LLM kr/deepseek-3.2, M5 enrichment chạy chế độ local deterministic trên 107 chunks tài liệu nội bộ; kết hợp Qdrant vector database localhost:6333, BM25 hybrid retrieval và CrossEncoder reranker.
Models generation/evaluator: Generation: kr/deepseek-3.2; Evaluator: BAAI/bge-m3 (embedding) và kr/deepseek-3.2 (LLM evaluator).

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.9008 | 0.6902 | 0.8958 |
| answer_relevancy | 0.8343 | 0.7727 | 0.7014 |
| context_precision | 0.8500 | 0.7083 | 0.9000 |
| context_recall | 0.8083 | 0.6500 | 0.6583 |
| avg_score | 0.8484 | 0.7053 | 0.7889 |

## Bottom 10 và nguyên nhân

| Rank | ID | Câu hỏi | Phân phối | Điểm TB | Metric yếu nhất | Chẩn đoán | Đề xuất khắc phục |
|---|---|---|---|---|---|---|---|
| 1 | 5 | Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt? | factual | 0.2500 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 2 | 27 | Nhân viên có thâm niên 7 năm theo v2024 được nghỉ bao nhiêu ngày phép? Nếu bị trừ thêm 4 ngày ốm không có giấy y tế thì còn lại bao nhiêu? | multi_hop | 0.4034 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |
| 3 | 4 | Mentor và buddy của nhân viên mới có thể là cùng một người không? Quản lý trực tiếp có thể làm mentor không? | factual | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 4 | 49 | Theo chính sách nghỉ phép cũ (v2023), nhân viên được nghỉ bao nhiêu ngày? Còn chính sách nào đang có hiệu lực hiện tại? | adversarial | 0.4583 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 5 | 39 | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | multi_hop | 0.4695 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |
| 6 | 33 | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | multi_hop | 0.5208 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 7 | 21 | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | multi_hop | 0.5322 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |
| 8 | 22 | Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT? | multi_hop | 0.5521 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 9 | 46 | Nhân viên thử việc có được nghỉ phép năm không? | adversarial | 0.5625 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 10 | 35 | Nhân viên Junior P1 có lương cơ bản 12 triệu vừa vào thử việc: nhận lương bao nhiêu và phụ cấp gì tháng đầu tiên? | multi_hop | 0.6782 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |

### Đối chiếu các câu đại diện cho từng nhóm lỗi:
- **Lỗi Answer Relevancy (Câu ID 5 - Rank 1, Avg 0.2500):** Câu hỏi *"Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?"*. Ground truth yêu cầu Tổng Giám đốc (CEO) phê duyệt vì mức tiền vượt 50 triệu. Tuy nhiên, answer sinh ra bị dài dòng và tập trung vào các quy trình mua sắm chung thay vì trực tiếp chỉ rõ người có thẩm quyền cao nhất, khiến điểm answer_relevancy bị đánh giá thấp.
- **Lỗi Context Precision (Câu ID 27 - Rank 2, Avg 0.4034):** Câu hỏi multi-hop phức tạp về thâm niên 7 năm theo chính sách v2024 kết hợp tính trừ ngày nghỉ ốm không giấy xác nhận. Quá trình hybrid search đã kéo về nhiều đoạn văn bản liên quan đến các chính sách nghỉ phép đặc biệt khác (thai sản, kết hôn) làm loãng context, dẫn đến context_precision giảm sâu.
- **Lỗi Faithfulness (Câu ID 4 - Rank 3, Avg 0.4167):** Câu hỏi về việc mentor và buddy có thể là cùng một người không. Mô hình sinh câu trả lời đưa ra nhận định suy diễn cá nhân chưa được bảo chứng hoàn toàn trong văn bản context trích xuất từ quy chế onboarding, dẫn đến hallucination.
- **Lỗi Bẫy Adversarial (Câu ID 49 - Rank 4, Avg 0.4583):** Câu hỏi hỏi về chính sách nghỉ phép cũ v2023 song song với chính sách hiện hành. Context truy xuất lẫn lộn giữa hai phiên bản dẫn đến câu trả lời thiếu tính cô đọng theo trọng tâm.

## Matrix và nhóm yếu nhất

| Worst Metric | factual (20) | multi_hop (20) | adversarial (10) | Tổng |
|---|---|---|---|---|
| faithfulness | 2 | 8 | 0 | 10 |
| context_recall | 5 | 2 | 5 | 12 |
| context_precision | 6 | 6 | 2 | 14 |
| answer_relevancy | 7 | 4 | 3 | 14 |

Nhóm yếu theo mean thấp nhất: multi_hop; mean: 0.7053.
Worst metric xuất hiện nhiều nhất: context_precision và answer_relevancy; số câu: 14 mỗi metric.

### Giải thích nguyên nhân nhóm multi_hop yếu nhất:
Nhóm câu hỏi multi_hop đòi hỏi phải tổng hợp thông tin từ nhiều điều khoản nằm rải rác ở các tài liệu khác nhau (chính sách thâm niên, bảng ngạch lương, quy chế nghỉ phép và mua sắm tài sản). Khi kích thước chunk con là 256 tokens, việc liên kết 2 chunk từ 2 văn bản khác nhau đòi hỏi bộ tìm kiếm phải đạt recall rất cao. Tuy nhiên, Cross-Encoder chỉ nhận top 20 từ HybridSearch rồi lọc top 3, khiến thông tin cần thiết của chặng 2 dễ bị rơi ra ngoài top contexts.
Đề xuất khắc phục cụ thể:
1. Nâng `RERANK_TOP_K` từ 3 lên 5 để bao quát đủ ngữ cảnh liên văn bản cho các câu hỏi tổng hợp.
2. Tích hợp metadata filter theo tags hoặc phân loại loại tài liệu trước khi rerank.
3. Chạy lại benchmark bằng lệnh: `python scripts/run_experiments.py --phase a --live` và so sánh avg_score của tập multi_hop để kiểm chứng mức tăng trưởng.

## Bẫy adversarial và giới hạn

So với nhóm factual đạt avg_score 0.8484, nhóm adversarial đạt 0.7889 với điểm answer_relevancy thấp nhất (0.7014). Điều này phản ánh rõ bẫy xung đột phiên bản (version conflict v2023 vs v2024 trong câu 41, 49) và bẫy phủ định (câu 46, 50). Reranker đôi khi vẫn xếp các chunk có chứa từ khóa nhưng thuộc phiên bản đã hết hiệu lực lên vị trí cao vì độ tương đồng từ vựng lớn.
Giới hạn thực nghiệm: Kích thước mẫu 50 câu (20/20/10) là bộ mẫu tiêu chuẩn của lab, chưa bao quát toàn bộ các tình huống edge-case trong thực tế doanh nghiệp; M5 chạy chế độ local fallback thay vì trích xuất tóm tắt bằng LLM trực tiếp trên toàn bộ kho tài liệu.
