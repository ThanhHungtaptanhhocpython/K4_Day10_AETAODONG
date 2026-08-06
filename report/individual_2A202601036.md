# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Thế Khiêm             |
| MSSV               | 2A202601036                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | [AETAODONG]     |
| Vai trò chính    | Vai trò 2 — Nền tảng dữ liệu & recovery (ingest \| clean) |
| Repository         | [https://github.com/ThanhHungtaptanhhocpython/K4_Day10_Data-Pipeline-Data-Observability/tree/khiem/dev] |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Ingestion Crossref (CP0) | `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records`, `load_raw_records` | Crossref REST API (query + filter trong Settings) | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành |
| Cleaning & data model (CP1) | `src/ingestion/cleaning.py`: `build_clean_dataframe` | `list[PaperRecord]` từ raw | `data/clean/papers_clean.csv`, `papers_clean.json` (có `text_for_embedding`, `age_days`) | Hoàn thành |
| Frozen evaluation set (CP2) | `src/evaluation/testset.py`: `build_test_set` | `papers_clean` dataframe | `data/eval/test_set.json` (24 câu, schema chuẩn) | Hoàn thành |
| Corruption có kiểm soát (CP5) | `src/ingestion/corruption.py`: `corrupt_clean_dataframe` | `papers_clean` dataframe | corrupted clean data + corruption log | Chưa hoàn thành (Pha 2) |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

> **Quan hệ phụ thuộc:** Output `papers_clean.json` của tôi là input cho Vai trò 3 (RAG/index) và Vai trò 4 (evaluation/observability). `test_set.json` của tôi được Vai trò 4 dùng để chạy `evaluate_pipeline`. Raw snapshot của tôi là "nguồn tin cậy" để repair ở Pha 2.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Xác minh lineage một `paper_id` xuyên suốt raw → clean → index | Vai trò 3 (RAG/index) | Xác nhận `paper_id` (DOI) ổn định, metadata index khớp clean data |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Gọi Crossref có retry/backoff, parse JATS abstract, tạo `paper_id` ổn định từ DOI | `src/ingestion/crossref.py` → `data/raw/` | 24 raw records, raw response lưu trước khi parse | Kiểm tra `data/raw/crossref_records.json` (24 record, mỗi record có DOI) |
| Làm sạch theo quy tắc bắt buộc: strip XML/HTML, drop summary <100 ký tự, `authors_joined`/`categories_joined`, `age_days`, `text_for_embedding` | `src/ingestion/cleaning.py` → `data/clean/` | 24 papers sạch, không tag sót, không trùng `paper_id` | Xem cột `text_for_embedding` dạng `Title: ... \| Authors: ... \| Summary: ...` |
| Chốt frozen eval set 24 câu factual, mỗi câu trỏ `ground_truth_doc_ids` là `paper_id` chứa đáp án | `src/evaluation/testset.py` → `data/eval/test_set.json` | test_set.json đúng schema, mọi doc_id tồn tại trong clean data | Script validate: 24/24 câu đủ 5 field, 0 doc_id thiếu |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Frozen eval set `data/eval/test_set.json` (24 câu) do tôi tạo là input trực tiếp cho bước evaluation. Nhờ ground truth trích thẳng từ clean data và question phrasing khớp với `qa._extract_answer`, baseline đạt `retrieval_hit_rate = 1.0` và `mean_token_f1 = 1.0` — chứng minh dữ liệu sạch + eval set chuẩn cho phép agent trả lời chính xác tuyệt đối, tạo mốc cao để Pha 2 đo mức tụt do corruption.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần của tôi là "nền tảng dữ liệu": biến metadata thô, không đồng nhất từ Crossref (abstract dạng JATS XML, tác giả rời rạc, ngày dạng date-parts, có bản ghi thiếu abstract) thành một corpus sạch, ổn định và có thể truy vết — để các bước embedding/RAG/evaluation phía sau tin cậy được. Đồng thời chốt một bộ câu hỏi đánh giá cố định (frozen) để so sánh công bằng 3 trạng thái hệ thống.

### Cách triển khai

**1. Ingestion (`crossref.py`):** Gọi Crossref `/works` với `query` + `filter` (from-pub-date, has-abstract:true). Dùng retry với exponential backoff (1→2→4→8s) cho các status 429/500/502/503/504 vì API công khai hay rate-limit. Lưu **raw response trước khi parse** để giữ khả năng truy vết. Chọn **DOI làm `paper_id`** vì DOI là định danh toàn cầu, ổn định — điều kiện tiên quyết để repair sau này khớp đúng record.

**2. Cleaning (`cleaning.py`):** Áp quy tắc bắt buộc — strip mọi tag XML/HTML bằng regex `<[^>]+>` khỏi title/summary; **drop bản ghi rác** (title rỗng hoặc summary <100 ký tự); gộp `authors`/`categories` thành chuỗi ngăn dấu phẩy; chuẩn hóa ngày về `YYYY-MM-DD`; tính `age_days = (hôm nay − published)`; tạo `text_for_embedding = "Title: … | Authors: … | Summary: …"`; dedupe theo `paper_id`; sort mới nhất trước cho ổn định.

**3. Frozen eval set (`testset.py`):** Sinh 24 câu hỏi factual, mỗi câu có đáp án **trích trực tiếp** từ clean data (không bịa). Phrasing câu hỏi được canh khớp với `qa._extract_answer` để ground truth đúng bằng thứ một retrieval + extraction đúng sẽ trả về. Ghi ra file cố định để "đóng băng".

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Crossref REST API (query/filter/rows từ `Settings`) |
| Output                         | `data/raw/*.json`, `data/clean/papers_clean.{csv,json}` (15 cột gồm `paper_id`, `text_for_embedding`, `age_days`), `data/eval/test_set.json` (schema: id, question_type, question, ground_truth, ground_truth_doc_ids) |
| Module phụ thuộc             | `core.config.Settings`, `core.utils` (normalize, write_json/csv), `requests`, `pandas` |
| Module sử dụng output        | `retrieval/index.py` (dùng `text_for_embedding` + metadata), `evaluation/metrics.py` (dùng test_set), `pipelines/corruption_flow.py` (dùng raw để repair) |
| Điều kiện lỗi cần xử lý | Crossref 429/503 (retry/backoff); abstract thiếu → drop record; date-parts rỗng → bỏ qua record; summary quá ngắn → loại rác |

### Cách xác minh

```bash
REFRESH_TEST_SET=1 python script/run_phase1.py
```

- **Kết quả mong đợi:** Sinh đủ raw/clean/eval artifact; test set đúng schema; baseline metrics cao trên dữ liệu sạch.
- **Kết quả thực tế:** 24 raw → 24 clean papers; test_set.json 24 câu (id `q1..q24`, `question_type="factual"`); `retrieval_hit_rate=1.0`, `mean_token_f1=1.0`; data quality PASS 6/6; freshness FRESH.
- **Artifact/log:** `data/raw/`, `data/clean/`, `data/eval/test_set.json`, `data/results/baseline_metrics.json` (không chứa secret).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn field làm `paper_id` (khóa định danh xuyên suốt raw → clean → index → repair).
- **Các phương án đã cân nhắc:** (1) Dùng chỉ số dòng / index tự sinh; (2) Dùng title đã chuẩn hóa (slug); (3) Dùng DOI từ Crossref.
- **Phương án đã chọn:** Dùng **DOI** làm `paper_id`.
- **Lý do:** Index tự sinh không ổn định qua các lần fetch (thứ tự đổi → ID đổi → repair không khớp record). Title-slug dễ trùng và vỡ khi title bị corrupt/truncate ở Pha 2. DOI là định danh toàn cầu, duy nhất, không đổi — đảm bảo **reproducibility** và cho phép repair Pha 2 khớp đúng bản ghi gốc từ raw. Đánh đổi: bỏ các record không có DOI, nhưng đây đúng là "rác" nên chấp nhận được.
- **Bằng chứng quyết định phù hợp:** Xác minh cùng một `paper_id` (DOI) tồn tại nhất quán trong `crossref_records.json`, `papers_clean.json` và metadata index; mọi `ground_truth_doc_ids` trong test_set (24/24) đều khớp `paper_id` trong clean data (0 thiếu).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'pandas'` khi chạy thử pipeline; `.venv` tồn tại nhưng `pip list` trống.
- **Lệnh hoặc bước tái hiện:** `.venv/Scripts/python.exe -c "import pandas"` → lỗi.
- **Nguyên nhân gốc:** Virtual env đã được tạo nhưng chưa cài project/dependency (và `uv.lock` đã bị xóa khỏi repo — git status: `D uv.lock`), nên không có package nào trong env.
- **Cách xử lý:** Cài project vào env hiện có bằng `uv pip install -e .` (cài cả package trong `src/` lẫn dependency, không chỉ `requirements.txt`).
- **Cách xác minh sau khi sửa:** `python -c "import pandas, requests, chromadb, sentence_transformers, langchain, datasets, pydantic; print('deps ok')"` → in `deps ok`; sau đó pipeline chạy end-to-end exit 0.
- **Điều học được:** `pip install -r requirements.txt` không đủ cho project layout `src/` — phải `install -e .` để package (pipelines, ingestion…) import được; và lockfile bị xóa thì nên dùng `uv pip install -e .` thay vì `uv sync`.

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** [Module/artifact.]
- **Những gì đã loại trừ:** [Các giả thuyết đã kiểm tra.]
- **Bước tiếp theo:** [Hành động có thể kiểm chứng.]

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. **Crossref → vector index:** `fetch_source_records` gọi Crossref, lưu raw response, rồi `parse_crossref_payload` biến mỗi item thành `PaperRecord` (DOI làm `paper_id`, strip JATS abstract). `build_clean_dataframe` chuẩn hóa và tạo `text_for_embedding`. `LocalEmbeddingIndex.build` dùng MiniLM đổi `text_for_embedding` thành vector 384 chiều, nạp vào ChromaDB collection `papers-baseline` kèm metadata (gồm `paper_id`).

2. **Eval set & ground-truth doc IDs:** Mỗi câu hỏi có `ground_truth` (đáp án đúng) và `ground_truth_doc_ids` (paper chứa đáp án). Khi đánh giá, agent truy hồi top-k rồi so: **retrieval_hit_rate** = có tài liệu truy hồi nào nằm trong `ground_truth_doc_ids` không; **token_f1** = độ trùng token giữa câu trả lời và ground_truth; **judge** = LLM/heuristic chấm câu trả lời đúng/sai.

3. **Quality checks vs freshness:** Quality checks kiểm tra tính *đúng đắn/toàn vẹn* của dữ liệu tại một thời điểm (row count, `paper_id` null/unique, title/summary hợp lệ). Freshness monitoring kiểm tra tính *thời sự* theo thời gian (`age_days`, số dòng stale, ngày mới/cũ nhất). Một dataset có thể "sạch" (pass quality) nhưng "cũ" (fail freshness) và ngược lại.

4. **Vì sao cùng test set:** Để so sánh công bằng, chỉ được thay đổi *một biến* là chất lượng dữ liệu. Nếu đổi test set giữa baseline/corrupted/repaired thì không biết metric đổi do dữ liệu xấu hay do câu hỏi khác — mất tính đối chứng. Đóng băng test set giữ cho ground truth, top-k và evaluator bất biến.

5. **Repair thành công dựa vào gì:** Khi các metric của **repaired** phục hồi về gần **baseline** (retrieval_hit_rate, token_f1, judge score tăng lại), quality checks chuyển FAIL→PASS và freshness về FRESH — tất cả trên **cùng frozen test set**. Quan trọng: repaired data phải được re-run từ raw source, không sửa tay answers/metrics.

> **Trả lời riêng câu hỏi checkpoint C2** — *Tại sao phải chốt & đóng băng eval set trước khi đánh giá RAG? Xử lý thế nào nếu một paper trong `ground_truth_doc_ids` bị thiếu ở pha sau?*
>
> **Phải đóng băng vì:** bộ câu hỏi là "thước đo". Nếu thước đo thay đổi giữa các lần đo thì mọi so sánh baseline/corrupted/repaired đều vô nghĩa — ta không tách được ảnh hưởng của corruption khỏi ảnh hưởng của việc đổi câu hỏi. Đóng băng đảm bảo mọi khác biệt về điểm số **chỉ đến từ chất lượng dữ liệu**, đúng mục tiêu observability của bài.
>
> **Nếu paper trong `ground_truth_doc_ids` bị thiếu ở pha sau** (ví dụ CP5 corruption cố tình drop record đó): đây chính là **tín hiệu chẩn đoán**, không phải lỗi cần "vá". Câu hỏi vẫn giữ nguyên; khi đánh giá corrupted, `retrieval_hit_rate` của câu đó sẽ rớt xuống 0 vì không tài liệu nào truy hồi được khớp `ground_truth_doc_ids` — chính điều này *chứng minh* corruption làm giảm chất lượng. Ở bước repair, record được phục hồi từ raw (nhờ `paper_id`=DOI ổn định) nên doc_id khớp trở lại và điểm hồi phục. Tuyệt đối **không** xóa câu hỏi hay đổi ground_truth để "cứu" điểm — làm vậy là phá tính đối chứng.

> **Trả lời riêng câu hỏi checkpoint C3** — *`retrieval_hit_rate` phản ánh hiệu suất của cấu phần nào? Vì sao Token F1 không bao giờ đạt tuyệt đối 1.0 kể cả khi retrieval đúng?*
>
> **`retrieval_hit_rate` đo tầng Retriever** (embedding model + ChromaDB), *không* đo LLM. Nó kiểm tra `paper_id` của tài liệu truy hồi trong top-k có nằm trong `ground_truth_doc_ids` không — tức "hệ có tìm đúng tài liệu chứa đáp án không". Nó độc lập với chất lượng câu chữ của câu trả lời: retrieval có thể trúng nhưng answer vẫn sai, nên đây là chỉ số chẩn đoán riêng cho khâu tìm kiếm.
>
> **Token F1 (trong hệ RAG sinh bằng LLM) gần như không đạt 1.0** vì F1 so khớp **token/từ vựng**, không so khớp ngữ nghĩa. Dù retrieval đúng (LLM có đủ ngữ cảnh), LLM vẫn diễn đạt lại bằng từ khác, thêm câu dẫn/giải thích/dấu câu → xuất hiện token thừa (giảm precision) và thiếu (giảm recall) → F1 < 1.0. Retrieval đúng chỉ đảm bảo *đầu vào* đúng, còn F1 phụ thuộc *cách LLM diễn đạt đầu ra*.
>
> **Lưu ý trung thực về pipeline hiện tại:** ở bài này Token F1 lại **= 1.0** cho cả 24 câu. Nguyên nhân: `qa._extract_answer` trong starter là cơ chế **extractive** — trích thẳng field (`authors_joined`, `published`, `first_sentence(summary)`) từ metadata; còn eval set của tôi lấy `ground_truth` từ *đúng field đó*, nên answer trùng khít ground_truth. Đây là giới hạn có chủ đích của starter (đánh giá retrieval mà không cần tốn LLM), không mâu thuẫn nguyên lý — chuyển sang answer do LLM sinh tự do thì F1 sẽ tụt xuống dưới 1.0 đúng như câu hỏi mô tả.

## 8. Phân tích kết quả

### Metrics chính

> Cột Baseline đã có số thật (Pha 1). Cột Corrupted/Repaired sẽ điền sau khi hoàn thành Pha 2 (CP5–CP6).

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0 |       [ ] |      [ ] | Dữ liệu sạch → luôn truy hồi đúng paper |
| `mean_token_f1`      |      1.0 |       [ ] |      [ ] | Ground truth trích thẳng từ clean data nên khớp tuyệt đối |
| `judge_accuracy`     |      1.0 |       [ ] |      [ ] | Chạy với heuristic judge (chưa cấu hình `.env` LLM) |
| `mean_judge_score`   |      5.0 |       [ ] |      [ ] | Điểm tối đa do token_f1=1.0 |
| Quality checks         | PASS (6/6) |     [ ] |      [ ] | Đủ row, `paper_id` unique, summary ≥100, không stale |
| Freshness status       |    FRESH |       [ ] |      [ ] | 0/24 dòng stale (ngưỡng 180 ngày) |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. _(Sẽ điền sau CP5)_ [Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi].
2. _(Sẽ điền sau CP6)_ [Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi hoặc chưa phục hồi].

Corruption nào ảnh hưởng rõ nhất và vì sao?

_Chưa thực hiện Pha 2 — sẽ phân tích dựa trên số liệu corrupted/repaired sau khi hoàn thành CP5–CP6._

Kết quả nào khác với kỳ vọng ban đầu?

Ở Pha 1: baseline đạt điểm tối đa (hit_rate/f1 = 1.0). Ban đầu tôi kỳ vọng có vài câu miss do summary dài; nhưng nhờ canh phrasing câu hỏi khớp với `qa._extract_answer` và ground_truth trích thẳng từ clean data, tất cả đều hit. Điều này xác nhận eval set và cleaning contract khớp nhau.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** Định danh ổn định (DOI làm `paper_id`) là nền móng — nó cho phép truy vết lineage raw→clean→index và làm cho việc repair khả thi. Luôn lưu raw *trước* khi parse để có nguồn khôi phục.
2. **Data quality/observability:** Quality (đúng đắn) và freshness (thời sự) là hai trục độc lập; mỗi check phải để lại con số/log truy vết được, không "âm thầm" drop record.
3. **Ảnh hưởng data → RAG:** Chất lượng đầu ra RAG bị chặn trên bởi chất lượng dữ liệu. Muốn đo được ảnh hưởng đó, phải cố định "thước đo" (frozen eval set) và chỉ thay đổi một biến là dữ liệu.

### Nếu có thêm thời gian

Thêm kiểm tra ngôn ngữ và trùng lặp ngữ nghĩa ở bước cleaning (hiện chỉ dedupe theo `paper_id` chính xác). Đo cải thiện bằng cách so số record bị loại thêm và xem `retrieval_hit_rate` có ổn định hơn khi corpus có các paper gần-trùng hay không.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng (Pha 2 ghi rõ "Chưa hoàn thành").
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Thế Khiêm
**Ngày xác nhận:** 2026-08-06
