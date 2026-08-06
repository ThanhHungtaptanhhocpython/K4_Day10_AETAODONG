# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4              |
| Tên nhóm         | AETAODONG     |
| Repository         | https://github.com/ThanhHungtaptanhhocpython/K4_Day10_AETAODONG |
| Ngày hoàn thành | 2026-08-06               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Thế Khiêm | 01036 | Điều phối pipeline | src/core/, src/pipelines/ |
| 2 | PHẠM THANH HƯNG | 01468 | Phụ trách ingestion | src/ingestion/crossref.py, data/raw/ |
| 3 | TRƯƠNG CÔNG CƯỜNG | 01584 | Phụ trách cleaning & corruption | src/ingestion/cleaning.py, corruption flow |
| 4 | Võ Quốc Huy | 2A202601110 | Phụ trách RAG & agent | src/retrieval/, data/embeddings/ |
| 5 | Đỗ Đức Tiến | 2A202601130 | Evaluation & observability | src/evaluation/, src/observability/ |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

**Tóm tắt của nhóm:**
Nhóm đã hoàn thành toàn bộ End-to-End Pipeline từ bước cào dữ liệu qua Crossref API, làm sạch, lưu vào CSDL Vector (ChromaDB), xây dựng hệ thống LangChain RAG sử dụng mô hình Gemini, và triển khai luồng Data Observability. 
Baseline pipeline đã tạo ra các file dữ liệu sạch (`papers_clean.csv`), vector database (`papers-baseline`), tập đánh giá (`test_set.json`), và báo cáo chất lượng ban đầu cho thấy dữ liệu đạt chuẩn (Passed Great Expectations check). 
Trong Phase 2, các lỗi dữ liệu (corruption) như xóa tóm tắt (short summary), lặp dữ liệu (duplicate) và lỗi định dạng thời gian (stale_rows) được tiêm vào khiến chất lượng RAG giảm rõ rệt (Retrieval Hit Rate rớt từ 1.0 xuống 0.6, Token F1 giảm từ 0.43 xuống 0.25). 
Quá trình Repair đã phục hồi hoàn hảo 100% các dòng bị lỗi dựa trên dữ liệu thô (raw_records), đưa điểm số RAG trở lại mức chuẩn. 
Hạn chế còn lại hiện tại là tốc độ và chi phí của bước Ragas đánh giá tự động (hiện đang tắt) và việc UI gặp một số lỗi hiển thị nhỏ.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records (papers_raw.json)
    -> cleaning và data modeling (papers_clean.csv)
    -> embedding + ChromaDB index (papers-baseline)
    -> evaluation baseline
    -> quality/freshness reports (Great Expectations)
    -> corruption (papers_clean_corrupted.csv)
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn (papers_clean_repaired.csv)
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API | Fetch REST API, parse json | `data/raw/` | PHẠM THANH HƯNG |
| Cleaning          | `raw_records.json` | Lọc None, sửa date | `data/clean/` | TRƯƠNG CÔNG CƯỜNG |
| Embedding/index   | `papers_clean.csv` | Embed với sentence-transformer | ChromaDB dir | Võ Quốc Huy |
| Evaluation        | ChromaDB, `test_set` | Agent trả lời + tính F1/Ragas | `baseline_metrics.json` | Đỗ Đức Tiến |
| Observability     | `papers_clean.csv` | Great Expectations validate | `baseline_quality.json` | Đỗ Đức Tiến |
| Corruption/repair | Clean records | Xóa data, sau đó map lại từ raw | `papers_corrupt/repair` | TRƯƠNG CÔNG CƯỜNG |
| Orchestration     | Toàn bộ code | Gọi theo thứ tự (Phase 1, 2) | Web UI Dashboard | Nguyễn Thế Khiêm |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | gemini         |
| `LLM_MODEL`                | gemini-2.5-flash         |
| Embedding model              | sentence-transformers/all-MiniLM-L6-v2         |
| Số lượng Crossref records | 24         |
| Retrieval `top_k`           | 4         |
| Freshness threshold          | 180 days         |
| Random seed, nếu có        | N/A         |

### Lệnh cài đặt

```bash
uv sync
```

### Lệnh chạy

Web UI Demo Dashboard (Khuyên dùng):
```bash
uv run uvicorn app:app --port 8000 --reload
```

Hoặc chạy Terminal CLI:
```bash
uv run python cli.py phase1
uv run python cli.py phase2
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 | `data/results/baseline_metrics.json` |
| Corruption flow   | Thành công | 2026-08-06 | `data/results/corrupted_metrics.json` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | api.crossref.org/works |
| Query/filter                | query=rag agent language models |
| Thời điểm lấy dữ liệu | 2026-08-06                           |
| Số record nhận được    | 24                         |
| Cơ chế retry/backoff      | Timeout 30s, retry 3 lần, backoff x2                       |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| paper_id | str | Có | DOI định danh | Loại bỏ (Drop) |
| summary | str | Có | Nội dung bài báo | Đánh cờ lỗi Great Expectation |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại record không có paper_id | Completeness | 0 | File json |
| Format lại Date yyyy-mm-dd | Validity | 24 | File json |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:
- `text_for_embedding`: Nối Title và Summary thành 1 chuỗi để tăng ngữ cảnh khi Retrieval.
- `age_days`: Lấy datetime hiện tại trừ đi `published` date. Dùng để check tính Fresness (stale_rows).

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 15                 |
| Các`question_type`                    | summary, author, date                  |
| Ground-truth document ID                 | Truy xuất từ dữ liệu chuẩn của Crossref     |
| Embedding model                          | sentence-transformers/all-MiniLM-L6-v2                  |
| Vector store/collection                  | ChromaDB (`papers-baseline`)                 |
| Retrieval `top_k`                       | 4                   |
| LLM provider/model                       | gemini / gemini-2.5-flash                   |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:
Giữ nguyên test set giúp kiểm chứng một cách công bằng (cùng một tập câu hỏi), đánh giá xem việc làm hỏng data và sau đó fix lại data tác động trực tiếp như thế nào tới điểm số.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có |  |
| Cleaned dataset          | `data/clean/`                        | Có |  |
| Embedding manifest/index | `data/embeddings/`                   | Có |  |
| Evaluation set           | `data/eval/`                         | Có |  |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có |  |
| Quality/freshness        | `data/quality/`                      | Có |  |
| Baseline report          | `data/reports/phase1_report.md`      | Có |  |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0 | RAG tìm trúng được 100% văn bản Ground Truth  |
| `mean_token_f1`      |     0.432 | Mức độ trùng khớp giữa câu trả lời AI và Ground Truth |
| `judge_accuracy`     |     0.333 | LLM Judge đánh giá độ chính xác (1-5) |
| `mean_judge_score`   |     2.333 | LLM Judge đánh giá trung bình |
| Ragas, nếu có        | N/A | Tắt vì quá lâu |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| check_duplicate | Uniqueness | = 0 | Pass (0) | `baseline_quality.json` |
| check_summary_length | Completeness | = 0 | Pass (0) | `baseline_quality.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Dataset `papers_clean.csv`            |
| Timestamp mới nhất       | Ngày tạo DB (2026-08)                         |
| Ngưỡng freshness         | 180 days                         |
| Trạng thái baseline      | Fresh               |
| Lý do                     | Dữ liệu lấy trực tiếp từ Crossref nên luôn up-to-date |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Truncate Summary | Cắt cụt Abstract  | 1 | Fails `short_summaries` GE check | Bị phát hiện | Khôi phục bằng Left Join raw records |
| Duplicate ID | Nhân bản row  | 1 | Fails `duplicate_paper_ids` GE check | Bị phát hiện | Khôi phục bằng Left Join raw records |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi nhận đầy đủ việc corrupt 1 trường summary và 1 trường ID.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:
Thuật toán Repair lấy tập hợp dữ liệu hỏng (`corrupted_df`), xóa bỏ (Drop) toàn bộ những ID đã bị cảnh báo lỗi từ Great Expectations, sau đó tiến hành Left Join ghép chúng lại bằng dữ liệu nguyên bản lấy từ hệ thống Ingestion ban đầu (`raw_records.json`). Đảm bảo dữ liệu nguyên vẹn nhất được trả về.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.0 |       0.6 |      1.0 |                     -0.4 |           +0.4 | Mất dữ liệu làm vector DB vô dụng |
| `mean_token_f1`        |      0.432 |      0.250 |      0.432 |                    -0.182 |           +0.182 | Trả lời sai trầm trọng |
| `judge_accuracy`       |      0.333 |      0.200 |      0.333 |                    -0.133 |           +0.133 |  |
| `mean_judge_score`     |      2.333 |      1.800 |      2.333 |                    -0.533 |           +0.533 |  |
| Quality checks pass/fail |      Pass |      Fail |      Pass |      - |             - | GE hoạt động tốt |
| Freshness status         |      0 (stale) |       1 (stale) |      0 (stale) |                      1 |            -1 | |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. Dữ liệu Abstract bị cắt ngắn → Vector mất ngữ cảnh (Fail Context) → Retrieval Hit Rate giảm từ 1.0 xuống 0.6.
2. Dùng code Repair Join Raw Data → Khôi phục đầy đủ chữ → Token F1 và Agent Answer quay về mức gốc 0.432.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Frontend nhận lỗi `[object Object]` khi chat với LangChain.
- **Nguyên nhân:** LangGraph (React Agent) thỉnh thoảng trả về kết quả `content` là một list các text blocks thay vì string.
- **Cách xử lý:** Sửa file `agent.py` trong hàm `run_agent_question`, gộp nối các text blocks về dạng `str`.
- **Cách xác minh:** Mở giao diện và chat bình thường.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Dataset quá nhỏ (24 row) | Model chưa có nhiều thách thức lớn | Tăng cấu hình `max_results = 200` |
| Ragas chạy quá lâu | Không dùng được realtime | Chạy ngầm hoặc giới hạn 3 câu |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
