# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

## 1. Thông tin học viên

- **Họ và tên:** Bùi Quang Vinh (suy từ tên repository; xác nhận trước khi nộp).
- **MSSV:** 2A202603012 (suy từ tên repository; xác nhận trước khi nộp).
- **Lớp:** K4-L3B.
- **Repository URL:** https://github.com/vbwork2/K4-L3-DAY13-BuiQuangVinh-2A202603012-Monitoring-LLMOps
- **Commit SHA cuối:** Chưa có; điền SHA sau khi hoàn thành evidence và commit.
- **Challenge ID:** Chưa nhận `config/challenge.json` chính thức.
- **Tên project Langfuse cá nhân:** Chưa tạo/xác minh; tên cần dùng là `day13-k4-l3b-2A202603012`.

## 2. Evidence index

| Evidence | Đường dẫn hoặc trạng thái |
|---|---|
| Pytest cuối | [evidence/01-pytest.txt](evidence/01-pytest.txt) |
| Log validator | [evidence/02-log-validator.txt](evidence/02-log-validator.txt) |
| Dashboard validator | [evidence/03-dashboard-validator.txt](evidence/03-dashboard-validator.txt) |
| Structured log | [evidence/04-structured-log.txt](evidence/04-structured-log.txt) |
| PII redaction | [evidence/05-pii-redaction.txt](evidence/05-pii-redaction.txt) |
| Trace list, waterfall, metadata | Chờ project Langfuse cá nhân; lưu lần lượt `06`, `07`, `08` trong `evidence/`. |
| Prompt versions và rollback | Chờ thao tác trên Langfuse; lưu `09`, `10` trong `evidence/`. |
| Dashboard runtime | Chạy `/dashboard` rồi chụp `evidence/11-dashboard-overview.png`. |
| Practice incident metric | [evidence/12-incident-metric.txt](evidence/12-incident-metric.txt) |
| Practice incident log | [evidence/13-incident-log.txt](evidence/13-incident-log.txt) |
| Incident trace chính thức | Chờ challenge và Langfuse; lưu `evidence/14-incident-trace.png`. |

Các file text là output thật trong workspace. `12` và `13` chỉ chứng minh practice `rag_slow`, không thay thế evidence challenge chính thức.

## 3. Kết quả kỹ thuật

| Nội dung | Baseline trước sửa | Kết quả đã kiểm chứng | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Không có `data/logs.jsonl`; validator báo lỗi. | 100/100, 44 log records, 22 correlation IDs. | 0 thiếu schema, 0 thiếu enrichment. |
| `validate_dashboard.py` | 6/6 panel. | 6/6 panel. | Contract hợp lệ; runtime `/dashboard` trả HTTP 200 với đủ sáu panel. |
| `pytest` | 22 passed. | 23 passed. | Có thêm kiểm tra child observations, headers, PII lồng nhau. |
| Số traces hợp lệ | 0. | Chưa xác minh. | Không có `.env`/Langfuse key; `/health` báo `tracing_enabled=false`. |
| Số PII leak | Chưa có log để đo. | 0 theo validator. | Mẫu email, điện thoại và thẻ trong workload đều được redact. |
| Latency P95 / TTFT P95 | 152 / 50 ms sau 10 request baseline. | 2653 / 50 ms sau practice `rag_slow`. | Retrieval làm latency tăng, TTFT của fake LLM giữ nguyên. |
| Retrieval success rate | 100% baseline. | 100% sau practice `rag_slow`. | Chậm nhưng không lỗi; xem log `tool_success=true`. |

## 4. Logging và PII

- **Correlation ID:** middleware xóa context cũ, nhận `x-request-id` nếu gồm ký tự an toàn và dài tối đa 64 ký tự, nếu không tạo `req-<8 hex>`. ID được bind vào structlog, lưu ở `request.state`, trả qua response header và truyền vào trace metadata.
- **Metadata:** `user_id_hash`, `session_id` đã hash, `feature`, `model`, `env`, latency, TTFT, token, cost, quality, trạng thái retrieval. Không ghi user ID/session ID thô.
- **PII scrub:** processor `scrub_event` chạy trước JSON renderer và ghi file, đi đệ quy qua các giá trị string trong dictionary/list. Pattern bao gồm email, số điện thoại Việt Nam, CCCD, thẻ thanh toán và số hộ chiếu dạng cơ bản. Prompt/answer trong trace chỉ có preview đã scrub; không capture raw input/output.
- **Kiểm chứng:** [validator](evidence/02-log-validator.txt), [structured log](evidence/04-structured-log.txt), [mẫu redact](evidence/05-pii-redaction.txt).

## 5. Tracing và prompt versioning

- **Project và trace ID:** Chưa xác minh vì chưa có project/key cá nhân. Sau khi cấu hình, chạy ít nhất 10 request và chụp danh sách trace trong đúng project.
- **Cấu trúc code:** root `day13-agent-request`/`lab-agent-run`, child `retrieval` (span) và `generation` (generation). Child generation ghi model, prompt name/label/version, token input/output, cost input/output, TTFT và preview đã scrub.
- **Nối log với trace:** dùng `correlation_id` trong structured log và trace metadata để tìm cùng request.
- **Prompt name:** `day13-chat`; code đọc label `production`, dùng local fallback nếu Langfuse chưa khả dụng.
- **Baseline v1, candidate v2, trace ID từng version, promote/rollback:** Chờ tạo thật trên Langfuse và ghi bằng chứng. Không dùng `local-v1` để thay cho managed prompt version.

## 6. Dashboard, SLO và alerts

- **Dashboard:** `/dashboard` đọc `data/logs.jsonl` trong 60 phút gần nhất, tự refresh 30 giây. Sáu panel: latency P50/P95/P99 và TTFT P95; traffic; error rate và retrieval success; cost; tokens; quality proxy. `config/dashboard.yaml` là contract tương ứng. Ảnh runtime cần chụp sau khi chạy workload.
- **SLO:** 99,5% request trong 28 ngày phải có `response_sent` với latency tối đa 2000 ms. Baseline local P95 là 152 ms; ngưỡng 2000 ms vẫn có headroom và phát hiện scenario retrieval chậm khoảng 2500 ms.
- **Error budget:** 0,5% tổng request. Với 10.000 request trong 28 ngày, tối đa 50 request được phép lỗi hoặc vượt 2000 ms.
- **Alerts:** `HighLatencyP95` (2000 ms/5m), `HighErrorRate` (2%/5m), `LowRetrievalSuccess` (90%/10m), đều có severity, owner, Slack channel trong [config/alert_rules.yaml](../config/alert_rules.yaml) và cách xử lý trong [docs/alerts.md](../docs/alerts.md). Đây là định nghĩa alert; cần nối với hệ thống gửi Slack thực tế nếu muốn thông báo tự động.

## 7. Điều tra challenge

- **Challenge ID:** Chưa nhận file chính thức từ Lab Coach. Không tự tạo hoặc thay thế file.
- **Practice đã chạy:** `rag_slow`, khoảng 2026-09-30 04:00:49 UTC. `/metrics` cho thấy P95 tăng từ 152 lên 2653 ms, TTFT P95 giữ 50 ms. [Log mẫu](evidence/13-incident-log.txt) có `correlation_id=req-7c49dc3b`, `latency_ms=2653`, `ttft_ms=50`, `tool_success=true`.
- **Giả thuyết có cơ sở:** retrieval bị chậm nhưng vẫn thành công. Trong practice, scenario `rag_slow` chủ động thêm độ trễ tại retrieval. Chưa có trace Langfuse nên không dùng kết quả này làm kết luận challenge chính thức.
- **Fix practice:** tắt `rag_slow`, đã kiểm tra `/health` trả tất cả incident là `false`.
- **Preventive measure:** alert `HighLatencyP95`, lọc log bằng correlation ID rồi xác nhận span retrieval trên Langfuse trước khi kết luận sự cố thực.
- **Cần hoàn tất cho challenge thật:** ghi challenge ID, cửa sổ thời gian, metric, log/correlation ID, trace ID/span, root cause, fix và preventive measure từ cùng một lần chạy.

## 8. Giải thích và tự đánh giá

- **Quyết định kỹ thuật:** hash session ID trước khi ghi log/trace để tránh trường hợp client đưa PII vào session ID; vẫn giữ khả năng nhóm request theo session.
- **Blocker đã gặp:** cổng 8000 trên Windows báo WinError 10013. Chạy API trên cổng 8765 và thêm `--base-url` cho `load_test.py`/`inject_incident.py`. Chrome headless lỗi GPU nên chưa lưu được ảnh dashboard; trang dashboard chạy và trả HTTP 200.
- **Metrics → Logs → Traces:** metric chỉ ra loại bất thường và thời gian; log chọn một `correlation_id`; trace của cùng ID xác định span gây ảnh hưởng. Bước trace chưa kiểm chứng trên Langfuse vì thiếu project/key cá nhân.
- **Prompt/token/cost/SLO/rollback:** prompt version liên kết hành vi request với thay đổi prompt; token và cost giúp phát hiện tăng chi phí; SLO/alert báo mức ảnh hưởng; label `production` cho phép rollback mà không đổi code.
- **Điều học được và hạn chế:** phần code, validator, log, dashboard runtime và practice đã kiểm tra; phần Langfuse, ảnh dashboard và challenge chính thức chờ thao tác/evidence cá nhân. Học viên cần tự xác nhận nội dung tự đánh giá này trước khi nộp.

## 9. Checklist trước khi nộp

- [x] Tests và validators đã chạy; evidence text khớp lần chạy hiện tại.
- [x] Log và evidence text không chứa API key hoặc PII thô.
- [ ] Tạo project Langfuse cá nhân, ít nhất 10 trace, prompt v1/v2 và rollback; bổ sung evidence.
- [ ] Chụp dashboard runtime và bổ sung đường dẫn ảnh.
- [ ] Nhận challenge chính thức, điều tra metric → log → trace và bổ sung evidence.
- [ ] Xác nhận họ tên/MSSV, phần tự đánh giá, commit SHA cuối, rồi nộp repo URL/SHA trên LMS.
