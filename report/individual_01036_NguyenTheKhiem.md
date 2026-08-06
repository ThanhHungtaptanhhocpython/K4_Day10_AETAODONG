# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Thế Khiêm             |
| MSSV               | 01036                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | AETAODONG     |
| Vai trò chính    | Điều phối pipeline (Orchestrator)                 |
| Repository         | https://github.com/ThanhHungtaptanhhocpython/K4_Day10_AETAODONG/tree/main |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Backend & API | `app.py`, `script.js` | Tín hiệu chạy từ UI | Gọi đúng pipeline phase 1, 2 | Hoàn thành |
| Cấu hình dự án | `src/core/config.py` | Biến môi trường .env | Cấu hình xuyên suốt toàn cục | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Sửa lỗi UI trả về [object Object] | Võ Quốc Huy | Fix lỗi LangChain Agent trả list block thay vì string |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Nối toàn bộ pipeline | `app.py` / `cli.py` | Chạy 1 click end-to-end | Bấm chạy Phase 1 và Phase 2 trên Web |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Tạo ra Web UI Dashboard hoàn chỉnh, giúp toàn bộ các thành viên khác có thể theo dõi tiến trình chạy của hệ thống và trực quan hóa các chỉ số Quality, Metrics.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Làm thế nào để kết nối các đoạn code rời rạc (Ingestion, Cleaning, VectorDB, RAG, Eval) thành một khối thống nhất (Pipeline) có thể chạy tuần tự, đảm bảo đầu ra của bước này là đầu vào của bước kia mà không bị ngắt quãng.

### Cách triển khai
Viết các API (FastAPI) nhận tín hiệu từ Frontend. Khi gọi Phase 1, hệ thống sẽ dùng module `crossref.py` lấy data -> truyền qua `cleaner.py` -> đẩy vào `index.py` -> chạy `metrics.py` và `quality.py`. Dữ liệu cấu hình như đường dẫn file (paths) được khai báo động trong `Settings` để đảm bảo Phase 1 và Phase 2 không ghi đè lên nhau.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Yêu cầu từ người dùng (Chạy Phase 1/2) |
| Output                         | Pipeline chạy hoàn tất, lưu metrics |
| Module phụ thuộc             | Tất cả các module khác |
| Module sử dụng output        | Giao diện Frontend |
| Điều kiện lỗi cần xử lý | Xử lý lỗi đứt gãy giữa các hàm, try-catch exception |

### Cách xác minh

```bash
uv run uvicorn app:app --port 8000
```
- **Kết quả mong đợi:** Khởi động Web server.
- **Kết quả thực tế:** Web chạy, các nút bấm gọi đúng luồng.
- **Artifact/log:** Terminal log của uvicorn.

## 5. Một quyết định kỹ thuật quan trọng
- **Bối cảnh:** Cần truyền đường dẫn file xuyên suốt hệ thống.
- **Các phương án đã cân nhắc:** Dùng đường dẫn tĩnh (Hardcode) vs dùng class Settings quản lý.
- **Phương án đã chọn:** Dùng class Settings quản lý.
- **Lý do:** Giúp Phase 1 (Baseline) và Phase 2 (Corrupted) hoàn toàn tách biệt, không bao giờ ghi đè nhầm file của nhau, đảm bảo Reproducibility.
- **Bằng chứng quyết định phù hợp:** Chạy Phase 2 không làm mất file `baseline_metrics.json`.

## 6. Một lỗi hoặc blocker đã xử lý
- **Triệu chứng/lỗi nguyên văn:** UI chat hiện `[object Object]`.
- **Lệnh hoặc bước tái hiện:** Hỏi Agent câu cần gọi Tool.
- **Nguyên nhân gốc:** Agent trả về List các Dict thay vì một chuỗi văn bản thuần.
- **Cách xử lý:** Cập nhật hàm `run_agent_question` để tự động parse List thành String.
- **Cách xác minh sau khi sửa:** Chat lại trên UI hiển thị bình thường.
- **Điều học được:** Serialization giữa Python (FastAPI) và JS có nhiều khác biệt khi làm việc với LLM outputs.

## 7. Hiểu biết về luồng end-to-end
1. Dữ liệu đi từ Crossref đến vector index như thế nào? Cào dữ liệu -> Xóa rỗng -> Nhúng vector -> Lưu ChromaDB.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao? Đối chiếu ID do RAG truy xuất với ID gốc để tính Hit rate. Đưa đáp án của RAG và đáp án gốc vào LLM Judge để tính F1.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab? Quality đo độ đúng đắn, Freshness đo độ mới.
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired? Để so sánh công bằng.
5. Repair được xem là thành công dựa trên artifact và metric nào? Quality pass, Metric F1 và Hit rate hồi 100%.

## 8. Phân tích kết quả
(Đã trình bày chi tiết trong Group Report)

## 9. Điều học được và hướng cải thiện
1. Biết cách điều phối một quy trình data pipeline phức tạp.
2. Hiểu rõ giá trị của Data Contract.
3. Cách Fast API tương tác với Langchain.
Nếu có thời gian, mình sẽ viết Dockerfile để container hóa hệ thống.

## 10. Cam kết của thành viên
- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.

**Họ và tên:** Nguyễn Thế Khiêm
**Ngày xác nhận:** 2026-08-06
