# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | PHẠM THANH HƯNG             |
| MSSV               | 2A202601468                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | AETAODONG     |
| Vai trò chính    | Phụ trách Ingestion (Ingestion owner)                 |
| Repository         | https://github.com/ThanhHungtaptanhhocpython/K4_Day10_AETAODONG/tree/main |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Crossref API Integration | `src/ingestion/crossref.py` | Query params (Settings) | List các record JSON thô | Hoàn thành |
| Lưu trữ Raw Data | `src/ingestion/crossref.py` | JSON Records | `data/raw/crossref_records.json` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Sửa cấu trúc Schema Data | Trương Công Cường (Cleaning) | Thống nhất được các trường (paper_id, summary) cần thiết |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Fetch dữ liệu từ API | `src/ingestion/crossref.py` | Dữ liệu thô tải thành công | Kiểm tra file json raw sinh ra |
| Đảm bảo Lineage cho Data Repair | `data/raw/crossref_records.json` | Snapshot raw đáng tin cậy | Phase 2 dùng file này để repair 100% |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Tạo ra file dữ liệu gốc `data/raw/crossref_records.json` chứa 24 bài báo khoa học chất lượng cao từ Crossref, đây là huyết mạch cho toàn bộ các công đoạn xử lý, làm sạch và vector hóa phía sau.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Làm thế nào để tải tự động dữ liệu các bài báo nghiên cứu khoa học một cách ổn định, xử lý các lỗi mạng hoặc giới hạn (rate limit) từ API của Crossref, đồng thời lưu trữ lại một bản "snapshot" nguyên thủy (raw data) để làm nguồn đối chiếu đáng tin cậy khi hệ thống gặp lỗi dữ liệu (data corruption).

### Cách triển khai

Sử dụng thư viện `requests` để gọi API của Crossref với từ khóa lấy từ cấu hình. Triển khai cơ chế Retry với Backoff (ví dụ dùng Tenacity) để thử gọi lại nếu server trả về lỗi 503 hoặc 429. Sau khi nhận được Response dạng JSON, bóc tách các trường cơ bản như DOI, title, abstract, date và map chúng vào Data Model (Pydantic). Cuối cùng, ghi ra file `crossref_records.json` trong thư mục `data/raw/`.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `settings.crossref_query`, `max_results` = 24 |
| Output                         | Danh sách các dict chứa dữ liệu bài báo |
| Module phụ thuộc             | `core.config.Settings` |
| Module sử dụng output        | `src.ingestion.cleaner.clean_records` |
| Điều kiện lỗi cần xử lý | Lỗi Timeout, Rate Limit, hoặc Data trả về rỗng |

### Cách xác minh

```bash
uv run python cli.py phase1
```

- **Kết quả mong đợi:** Terminal đếm quá trình tải API (1/24... 24/24) và báo thành công.
- **Kết quả thực tế:** 24 bài báo tải về đầy đủ.
- **Artifact/log:** `data/raw/crossref_records.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Crossref API có thể trả về một số field bị null (như abstract) hoặc DOI bị format lạ.
- **Các phương án đã cân nhắc:** 1. Filter bỏ ngay lúc Ingestion. 2. Lưu toàn bộ raw data như nguyên bản, đẩy trách nhiệm filter cho bước Cleaning.
- **Phương án đã chọn:** Lưu toàn bộ raw data nguyên bản.
- **Lý do:** Giữ được Single Source of Truth (Nguồn chân lý). Điều này cực kỳ quan trọng vì Data Observability cần một snapshot thô và chính xác tuyệt đối để thực hiện Repair (phục hồi) sau này nếu Clean Data bị hỏng.
- **Bằng chứng quyết định phù hợp:** Trong Phase 2, thuật toán Repair đã dùng chính file raw này để khôi phục lại 100% dữ liệu bị hỏng (corrupted summary).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Request tới Crossref API trả về Timeout hoặc 429 Too Many Requests do gọi nhiều lần liên tiếp khi test.
- **Lệnh hoặc bước tái hiện:** Chạy đi chạy lại script nhiều lần trong 1 phút.
- **Nguyên nhân gốc:** API của Crossref giới hạn tần suất truy cập đối với các request không khai báo thư mục mailto hoặc gọi quá gắt.
- **Cách xử lý:** Bổ sung cơ chế caching tại chỗ và hàm kiểm tra nếu file raw đã tồn tại thì đọc luôn từ đĩa (thay vì gọi lại API) để tăng tốc độ demo.
- **Cách xác minh sau khi sửa:** Chạy lại `uv run python cli.py phase1`, log báo "API requests completed rapidly (cached)".
- **Điều học được:** Việc caching raw data không chỉ giúp tránh Rate Limit mà còn tăng tốc độ Development cực kỳ hiệu quả.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
   Dữ liệu thô từ Crossref API (Ingestion) -> Lọc Null và Format Date (Cleaning) -> Nối Title + Abstract thành 1 cục Text -> Mã hóa thành Vector bằng MiniLM -> Lưu vào CSDL ChromaDB (Index).
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
   Tập câu hỏi được sinh ra có kèm theo ID của bài báo chứa câu trả lời. Hệ thống so sánh ID bài báo mà RAG tìm ra với cái ID gốc đó để tính Hit Rate. Tiếp đến so câu trả lời của AI với nội dung bài báo gốc để tính điểm F1.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
   Quality Check là rà soát tính đúng đắn (Không bị trùng lặp, Không rỗng). Freshness là đo độ tươi mới (Bài báo có bị quá cũ so với ngưỡng 180 ngày không).
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
   Để tạo ra một thước đo cố định và công bằng, giúp so sánh chính xác sự biến động điểm số RAG khi dữ liệu bị hỏng và khi được phục hồi.
5. Repair được xem là thành công dựa trên artifact và metric nào?
   Khi file `repaired_quality.json` trả về Passed cho các lỗi Great Expectations, và `repaired_metrics.json` có điểm số F1, Hit Rate hồi phục 100% bằng với Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0 |       0.6 |      1.0 | Khi data bị xóa Abstract, VectorDB không còn ngữ cảnh để tìm trúng bài báo. |
| `mean_token_f1`      |      0.432 |      0.250 |      0.432 | Mất hit rate kéo theo câu trả lời sai hoàn toàn. |
| `judge_accuracy`     |      0.333 |      0.200 |      0.333 | LLM Judge đánh giá tương tự F1. |
| `mean_judge_score`   |      2.333 |      1.800 |      2.333 | Điểm số trung bình sụt giảm rõ rệt. |
| Quality checks         |      Pass |      Fail |      Pass | Great Expectation check rất chính xác. |
| Freshness status       |      0 (stale) |       1 (stale) |      0 (stale) | Vẫn nhận diện đúng độ tuổi của báo. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Dữ liệu Abstract bị cắt ngắn → Cảnh báo Quality Fail (short_summaries) → Retrieval Hit Rate giảm từ 1.0 xuống 0.6.
2. Left Join với dữ liệu nguồn Raw → Quality Pass phục hồi → Retrieval Hit Rate và F1 hồi phục hoàn toàn về mức 1.0 và 0.432.

Corruption nào ảnh hưởng rõ nhất và vì sao?
Việc Truncate (Cắt ngắn) Abstract ảnh hưởng trực tiếp đến Retrieval. Vì Vector Embedding chủ yếu bám vào Abstract, khi bị cắt thì khoảng cách vector bị sai lệch, dẫn tới tìm không ra tài liệu.

Kết quả nào khác với kỳ vọng ban đầu?
LLM Judge chấm điểm khá ngặt nghèo (accuracy chỉ 0.333) cho dù RAG tìm trúng tài liệu (Hit rate 1.0). Có vẻ hệ thống Gemini trả lời ngắn gọn khác với đoạn trích Ground Truth gốc nên LLM Judge trừ điểm.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Tầm quan trọng của việc giữ lại Raw Data chưa qua chế biến (Source of truth).
2. Data Observability là cách duy nhất để biết khi nào RAG trả lời sai do dữ liệu xấu chứ không phải do Prompts.
3. Cách thiết lập một Pipeline End-to-End từ Ingestion, Vector hóa đến Evaluation tự động hóa hoàn toàn.

### Nếu có thêm thời gian

Mình sẽ bổ sung tính năng Ingestion chạy theo lịch trình (Cronjob) và cơ chế Caching Vectorize thông minh để chỉ thêm vào các bài báo mới (Incremental Update) thay vì phải nhồi lại cả database từ đầu.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** PHẠM THANH HƯNG
**Ngày xác nhận:** 2026-08-06
