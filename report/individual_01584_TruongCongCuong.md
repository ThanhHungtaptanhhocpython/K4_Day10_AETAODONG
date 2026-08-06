# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân
| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | TRƯƠNG CÔNG CƯỜNG             |
| MSSV               | 2A202601584                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | AETAODONG     |
| Vai trò chính    | Phụ trách Cleaning & Corruption |
| Repository         | https://github.com/ThanhHungtaptanhhocpython/K4_Day10_AETAODONG/tree/main |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc
### Phần việc sở hữu
| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | --- |
| Làm sạch dữ liệu | `src/ingestion/cleaner.py` | JSON Records | `papers_clean.csv` | Hoàn thành |
| Tiêm lỗi và Sửa lỗi | `src/pipelines/corruption_flow.py` | Clean Data | `papers_corrupt/repair` | Hoàn thành |

## 3. Kết quả theo vai trò
Tạo ra cơ chế tiêm lỗi (nhân bản dữ liệu, cắt cụt abstract) và thuật toán Left Join để khôi phục dữ liệu từ Raw Data.

## 4. Giải thích phần kỹ thuật đã thực hiện
### Vấn đề cần giải quyết
Chuyển đổi dữ liệu thô sang định dạng chuẩn (CSV) để VectorDB dễ dàng xử lý. Đồng thời, giả lập các sự cố dữ liệu thực tế (Data Corruption) và lên phương án cứu hộ (Repair).

### Cách triển khai
Cleaning: Xóa các bài báo không có summary, chuẩn hóa định dạng Date yyyy-mm-dd.
Corruption: Chọn random 1 dòng cắt abstract, 1 dòng duplicate.
Repair: Lấy các ID bị đánh cờ lỗi, Drop chúng ra khỏi dataset hiện tại, và Join lại với Raw Dataset bằng `paper_id`.

## 5. Một quyết định kỹ thuật quan trọng
- **Bối cảnh:** Sửa dữ liệu lỗi.
- **Phương án đã chọn:** Dùng thuật toán Left Join thay vì chỉnh sửa thủ công.
- **Lý do:** Tự động hóa và đảm bảo tính nhất quán (Single Source of Truth) từ nguồn ingestion.

## 6. Một lỗi hoặc blocker đã xử lý
- **Triệu chứng:** Join data bị sai lệch cột.
- **Nguyên nhân gốc:** Không đồng nhất kiểu dữ liệu (String vs Object).
- **Cách xử lý:** Ép kiểu `astype(str)` cho `paper_id` trước khi Merge.

## 7. Hiểu biết về luồng end-to-end
Đã nắm rõ cơ chế làm hỏng Abstract sẽ ảnh hưởng trực tiếp đến khoảng cách Vector lúc tìm kiếm, gây rớt Hit Rate.

## 10. Cam kết của thành viên
- [x] Nội dung báo cáo phản ánh đúng phần việc.
**Họ và tên:** TRƯƠNG CÔNG CƯỜNG
**Ngày xác nhận:** 2026-08-06
