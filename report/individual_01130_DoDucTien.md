# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân
| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đỗ Đức Tiến             |
| MSSV               | 2A202601130                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | AETAODONG     |
| Vai trò chính    | Evaluation & Observability |
| Repository         | https://github.com/ThanhHungtaptanhhocpython/K4_Day10_AETAODONG/tree/main |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc
### Phần việc sở hữu
| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | --- |
| Quality Checks (Great Expectations) | `src/observability/quality.py` | `papers_clean.csv` | `baseline_quality.json` | Hoàn thành |
| Metrics Evaluation | `src/evaluation/metrics.py` | RAG outputs | `baseline_metrics.json` | Hoàn thành |

## 3. Kết quả theo vai trò
Chạy báo cáo chất lượng để phát hiện dữ liệu hỏng. Đo đạc các chỉ số Hit Rate và Token F1 cho RAG Agent, cho thấy rõ tương quan giữa Data Xấu và RAG Tệ.

## 4. Giải thích phần kỹ thuật đã thực hiện
Dùng Great Expectations tạo bộ Rules (Expectations): Không được rỗng ID, Không được lặp ID, Độ dài Summary phải > 50 ký tự.
Dùng thuật toán Token F1 để chấm điểm tương đồng giữa Ground Truth (Đáp án chuẩn) và Agent Answer. Tích hợp Ragas (tùy chọn) để chấm sâu hơn về Context.

## 5. Một quyết định kỹ thuật quan trọng
- **Quyết định:** Mặc định tắt Ragas và dùng Token F1.
- **Lý do:** Chạy Ragas tốn hàng phút đồng hồ và tốn hàng ngàn tokens LLM cho mỗi lần test. F1 chạy cực nhanh và vẫn đủ nhạy bén để phát hiện câu trả lời sai do data hỏng.

## 6. Một lỗi hoặc blocker đã xử lý
LLM Judge chấm điểm quá khắt khe dù tìm trúng tài liệu. Rút ra bài học Prompt Engineering cho Evaluator Agent cần được tuning chặt chẽ hơn.

## 7. Hiểu biết về luồng end-to-end
Data Observability chính là "Chốt chặn" kiểm định chất lượng dữ liệu. Khi chốt chặn này cảnh báo lỗi, metrics F1 của RAG chắc chắn giảm.

## 10. Cam kết của thành viên
- [x] Nội dung báo cáo phản ánh đúng phần việc.
**Họ và tên:** Đỗ Đức Tiến
**Ngày xác nhận:** 2026-08-06
