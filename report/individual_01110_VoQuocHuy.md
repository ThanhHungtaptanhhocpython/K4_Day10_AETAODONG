# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân
| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Võ Quốc Huy             |
| MSSV               | 2A202601110                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | AETAODONG     |
| Vai trò chính    | Phụ trách RAG & Agent |
| Repository         | https://github.com/ThanhHungtaptanhhocpython/K4_Day10_AETAODONG/tree/main |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc
### Phần việc sở hữu
| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | --- |
| VectorDB Indexing | `src/retrieval/index.py` | `papers_clean.csv` | ChromaDB Collection | Hoàn thành |
| LangChain Agent | `src/retrieval/agent.py` | Query từ User | Câu trả lời AI (String) | Hoàn thành |

## 3. Kết quả theo vai trò
Tạo ra hệ thống RAG thông minh bằng Langchain Agent, có khả năng tự động dùng Tool (semantic_search, lookup) để trả về thông tin dựa trên cơ sở dữ liệu học thuật.

## 4. Giải thích phần kỹ thuật đã thực hiện
Sử dụng mô hình nhúng `sentence-transformers/all-MiniLM-L6-v2` để vector hóa chuỗi `text_for_embedding` (Title + Summary) của từng bài báo. Khởi tạo Agent Executor bằng Langgraph/Langchain với LLM là Gemini-2.5-Flash, cấp cho nó các công cụ tìm kiếm và truy xuất thông tin cụ thể.

## 5. Một quyết định kỹ thuật quan trọng
- **Bối cảnh:** Lựa chọn mô hình Embedding.
- **Phương án đã chọn:** Dùng MiniLM cục bộ thay vì OpenAI/Google Embeddings.
- **Lý do:** Miễn phí, chạy nhanh trên máy tính cá nhân, tiết kiệm chi phí API, đủ mạnh cho bài toán search văn bản tiếng Anh.

## 6. Một lỗi hoặc blocker đã xử lý
Lỗi WebUI không render được response dạng List. Xử lý bằng cách ép parsing các TextBlock của LLM trả về dạng string thuần túy trong `agent.py`.

## 7. Hiểu biết về luồng end-to-end
Hiểu rõ việc Agent cần Context (Ngữ cảnh) chất lượng từ VectorDB. Nếu Ingestion đưa vào data rỗng, Vector search sẽ trả về rác, làm Agent trả lời sai (Ảo giác).

## 10. Cam kết của thành viên
- [x] Nội dung báo cáo phản ánh đúng phần việc.
**Họ và tên:** Võ Quốc Huy
**Ngày xác nhận:** 2026-08-06
