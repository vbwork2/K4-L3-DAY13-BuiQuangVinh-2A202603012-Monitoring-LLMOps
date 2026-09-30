# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

## 1. Thông tin học viên

- **Họ và tên:** Bùi Quang Vinh .
- **MSSV:** 2A202603012 .
- **Lớp:** K4-L3B.
- **Repository URL:** https://github.com/vbwork2/K4-L3-DAY13-BuiQuangVinh-2A202603012-Monitoring-LLMOps
- **Commit SHA cuối:** Chưa có; điền SHA sau khi hoàn thành evidence và commit.
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1.
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202603012`, đã xác nhận qua API và ảnh `06-trace-list.png`/`07-trace-waterfall.png`; project ID `cmunmfk6o00hxad0c1opri6cg`, vùng Nhật `https://jp.cloud.langfuse.com`.

## 2. Evidence index

| Evidence | Đường dẫn hoặc trạng thái |
|---|---|
| Pytest cuối | [evidence/01-pytest.txt](evidence/01-pytest.txt) |
| Log validator | [evidence/02-log-validator.txt](evidence/02-log-validator.txt) |
| Dashboard validator | [evidence/03-dashboard-validator.txt](evidence/03-dashboard-validator.txt) |
| Structured log | [evidence/04-structured-log.png](evidence/04-structured-log.png), [output text](evidence/04-structured-log.txt). Có timestamp, event, correlation ID, model, env, feature và latency. |
| PII redaction | [evidence/05-pii-redaction.png](evidence/05-pii-redaction.png), [output text trước đây](evidence/05-pii-redaction.txt). Ảnh mới có input giả và runtime che đủ email, điện thoại, CCCD, thẻ. |
| Trace list, waterfall, metadata | [Danh sách trace](evidence/06-trace-list.png), [cây trace](evidence/07-trace-waterfall.png), [metadata an toàn](evidence/08-trace-metadata.png), [14 trace IDs đã kiểm chứng](evidence/trace-list-verification.json). Ảnh danh sách có tên project, bộ lọc root, ít nhất 10 dòng và tổng khoảng 163 root observations. |
| Prompt versions và rollback | [Trước rollback: production/v2](evidence/09-prompt-versions.png), [sau rollback: production/v1](evidence/10-prompt-rollback.png). |
| Dashboard runtime | [evidence/11-dashboard-overview.png](evidence/11-dashboard-overview.png), [snapshot panel thật](evidence/12-challenge-dashboard.json). Ảnh mới lúc 09:39:11 UTC có đủ sáu panel, time range, đơn vị và threshold, gồm Cost 2,5 USD. |
| Incident metric | [evidence/12-incident-metric.png](evidence/12-incident-metric.png), [metrics trước/sau challenge](evidence/12-challenge-metric.json), [snapshot dashboard](evidence/12-challenge-dashboard.json). Ảnh mới lúc 09:39:41 UTC, cửa sổ 60 phút chứa request 09:01:35 UTC; P95/P99 2653 ms > 2000 ms, TTFT 50 ms, error 0%, retrieval 100%. |
| Incident log | [Ảnh log đúng request](evidence/13-incident-log.png), [log cùng request](evidence/13-challenge-log.json). Đã xác nhận correlation ID, timestamp, latency 2653 ms, TTFT 50 ms và retrieval thành công. |
| Incident trace chính thức | [Ảnh trace cùng correlation ID](evidence/14-incident-trace.png), [observations qua API](evidence/14-challenge-trace.json). Đúng trace ID, retrieval 2,50 giây, generation 0,15 giây; metadata nối được với ảnh log. |

Các file text/JSON là output thật; JSON trace chỉ lưu các trường an toàn, không lưu public/secret key. Hai file cũ `12-incident-metric.txt` và `13-incident-log.txt` là practice, không thay thế challenge. Các ảnh mới đã được đặt tên theo checklist đề bài. `08-trace-metadata.png` là bản sao nguyên vẹn của screenshot `14-incident-trace.png`, dùng cùng trace để chứng minh metadata; ảnh 08 cũ chứa public key đã được giữ riêng trong `.venv` được Git ignore và không thuộc bài nộp. Snapshot dashboard, ảnh dashboard và ảnh danh sách có thời điểm chụp khác nhau nên số đếm có thể khác.

## 3. Kết quả kỹ thuật

| Nội dung | Baseline trước sửa | Kết quả đã kiểm chứng | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Không có `data/logs.jsonl`; validator báo lỗi. | 100/100, 382 log records, 188 correlation IDs. | 0 thiếu schema, 0 thiếu enrichment, 0 PII leak. |
| `validate_dashboard.py` | 6/6 panel. | 6/6 panel. | Contract hợp lệ; runtime `/dashboard` trả HTTP 200 với đủ sáu panel. |
| `pytest` | 22 passed. | 23 passed. | Có thêm kiểm tra child observations, headers, PII lồng nhau. |
| Số traces hợp lệ | 0. | API query có 162 root observations, không có trang tiếp theo; đã lưu 14 trace IDs, tất cả có retrieval và generation đúng parent. Ảnh danh sách mới hiển thị khoảng 163 root observations. | API query và ảnh chụp có thời điểm khác nhau; ảnh có ít nhất 10 dòng trong project cá nhân. Trace incident dùng `production/v1`. |
| Số PII leak | Chưa có log để đo. | 0 theo validator. | Request `req-7f4d4067` trong ảnh 05/log runtime đã che đủ email, điện thoại, CCCD và thẻ. |
| Latency P95 / TTFT P95 | Lần baseline mới ngày 30/09: 783 / 50 ms, 10 request. | 2653 / 50 ms sau challenge; P99 2653 ms. Riêng 10 request sau fix: P95/P99 152 ms. | Trace cùng request xác nhận retrieval 2503 ms, generation 152 ms; TTFT là chỉ số của fake LLM, không bao gồm thời gian retrieval. |
| Retrieval success rate | 100% baseline. | 100%: 5/5 request challenge và 10/10 request hồi phục. | Error rate challenge 0%; request chậm vẫn có `tool_success=true`. |

## 4. Logging và PII

- **Correlation ID:** middleware xóa context cũ, nhận `x-request-id` nếu gồm ký tự an toàn và dài tối đa 64 ký tự, nếu không tạo `req-<8 hex>`. ID được bind vào structlog, lưu ở `request.state`, trả qua response header và truyền vào trace metadata.
- **Metadata:** `user_id_hash`, `session_id` đã hash, `feature`, `model`, `env`, latency, TTFT, token, cost, quality, trạng thái retrieval. Không ghi user ID/session ID thô.
- **PII scrub:** processor `scrub_event` chạy trước JSON renderer và ghi file, đi đệ quy qua các giá trị string trong dictionary/list. Pattern bao gồm email, số điện thoại Việt Nam, CCCD, thẻ thanh toán và số hộ chiếu dạng cơ bản. Prompt/answer trong trace chỉ có preview đã scrub; không capture raw input/output.
- **Kiểm chứng:** [validator](evidence/02-log-validator.txt), [structured log](evidence/04-structured-log.png), [PII redaction đủ bốn loại](evidence/05-pii-redaction.png). Request `req-7f4d4067` lúc `2026-09-30T09:41:46.574539Z` có message preview gồm đủ bốn placeholder, được xác nhận lại trực tiếp từ `data/logs.jsonl`.

## 5. Tracing và prompt versioning

- **Project và trace ID:** Project cá nhân đã xác nhận ở mục 1. Trace v1 trước đây: `b1478afb72b494af6e7c3d6b7509eca2`, `correlation_id=req-ea64816c`. Ảnh `07-trace-waterfall.png` có trace `105e2d01336e33122b6190bd03ec8e59`, `correlation_id=req-513a2ae8`. Hai ảnh `08-trace-metadata.png` và `14-incident-trace.png` cùng chụp trace incident `6ee5e0d0fe5d4bfe8090c5a9b689ddce`, `correlation_id=req-45d62217`; không nhầm hai request. `06-trace-list.png` đã có danh sách ít nhất 10 dòng root trong đúng project.
- **Cấu trúc code:** root `day13-agent-request`/`lab-agent-run`, child `retrieval` (span) và `generation` (generation). Child generation ghi model, prompt name/label/version, token input/output, cost input/output, TTFT và preview đã scrub.
- **Nối log với trace:** dùng `correlation_id` trong structured log và trace metadata để tìm cùng request.
- **Prompt name:** `day13-chat`; code đọc label `production`, dùng local fallback nếu Langfuse chưa khả dụng.
- **Baseline v1, candidate v2:** API xác nhận `baseline → v1`, `candidate → v2`. Trace candidate v2: `11608016e97d92ac325cebb89924d3ae`, `correlation_id=req-15bde94f`.
- **Promote/rollback:** Đã chuyển `production → v2`, tạo trace `8820506915b52793b1b2dca2efa4cc32` (`correlation_id=req-f2846e1e`, metadata `production/v2`), rồi chuyển `production → v1`. Ảnh `09-prompt-versions.png` xác nhận production/v2; `10-prompt-rollback.png` xác nhận baseline/production trên v1 và candidate trên v2. Trace incident lần này xác nhận `day13-chat`, `production`, version 1, source `langfuse`.

## 6. Dashboard, SLO và alerts

- **Dashboard:** `/dashboard` đọc `data/logs.jsonl` trong 60 phút gần nhất, tự refresh 30 giây. Ảnh `11-dashboard-overview.png` lúc 09:39:11 UTC có đủ sáu panel và threshold: 30 request, P50/P95/P99 152/2653/2653 ms, TTFT P95 50 ms, error 0%, retrieval 100%, cost 0,0597 USD, token input/output 1030/3772 và quality 0,87. Snapshot JSON lúc 09:03:37 UTC có 110 request và P99 7016 ms vì cửa sổ khi đó còn chứa log cũ; không quy P99 đó cho request incident đã chọn. `/metrics` tính từ khi tiến trình API khởi động, phạm vi khác dashboard. Cổng 8000 và 8765 đã được xác nhận cùng đọc nguồn log; ưu tiên 8765 cho demo.
- **SLO:** 99,5% request trong 28 ngày phải có `response_sent` với latency tối đa 2000 ms. Baseline local P95 là 152 ms; ngưỡng 2000 ms vẫn có headroom và phát hiện scenario retrieval chậm khoảng 2500 ms.
- **Error budget:** 0,5% tổng request. Với 10.000 request trong 28 ngày, tối đa 50 request được phép lỗi hoặc vượt 2000 ms.
- **Alerts:** `HighLatencyP95` (2000 ms/5m), `HighErrorRate` (2%/5m), `LowRetrievalSuccess` (90%/10m), đều có severity, owner, Slack channel trong [config/alert_rules.yaml](../config/alert_rules.yaml) và cách xử lý trong [docs/alerts.md](../docs/alerts.md). Đây là định nghĩa alert; cần nối với hệ thống gửi Slack thực tế nếu muốn thông báo tự động.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`, cohort K4. `config/challenge.json` tồn tại local, schema hợp lệ, được Git ignore; chạy nguyên workflow `inject_incident.py` rồi `load_test.py --challenge --concurrency 5 --base-url http://127.0.0.1:8765`. Không sửa hoặc đưa nội dung file vào evidence; hash kiểm tra sau chạy không đổi.
- **Practice đã chạy:** Các file practice cũ vẫn được giữ riêng. Lần challenge mới chạy từ 2026-09-30 09:01:24.3724102 đến 09:01:38.2154097 UTC (16:01:24–16:01:38 UTC+7). [Metrics](evidence/12-challenge-metric.json): traffic 10 → 15; P50 151 → 152 ms; P95/P99 783 → 2653 ms; TTFT P95 50 ms; error breakdown `{}`. 5/5 request challenge thành công, error rate 0%, retrieval success 100%. Cost tổng 0,0182 → 0,0287 USD, trung bình 0,0018 → 0,0019 USD; token input/output 338/1148 → 513/1810; quality trung bình 0,88 → 0,8667. Đây là tail latency degradation / slow request, vượt SLO 2000 ms; không có bằng chứng error incident hoặc cost incident.
- **Giả thuyết có cơ sở:** [Log](evidence/13-challenge-log.json) chọn `response_sent` lúc `2026-09-30T09:01:35.529686Z`, `correlation_id=req-45d62217`, latency 2653 ms, TTFT 50 ms, retrieval thành công. [Trace cùng ID](evidence/14-challenge-trace.json) là `6ee5e0d0fe5d4bfe8090c5a9b689ddce`: root `lab-agent-run` 2655 ms, retrieval 2503 ms, generation 152 ms. Hai child có cùng parent `cd38489d6e4784da`; retrieval chiếm khoảng 94,3% tổng duration. Root cause đã kiểm chứng: incident injection gây chậm retrieval; `app/mock_rag.py` thêm sleep 2,5 giây khi injection bật, phù hợp duration runtime. Generation dùng production/v1 và nhỏ hơn rõ rệt. Sai khác 2 ms giữa latency log và root span do phạm vi đo/độ phân giải timestamp; không thay số cho khớp. Client load test đo 5,3–13,3 giây, bao gồm cả chờ xử lý khi concurrency 5; latency log là thời gian chạy agent.
- **Fix practice:** Với challenge mới, chạy `inject_incident.py --disable --base-url http://127.0.0.1:8765`, rồi chạy workload hồi phục. [Kết quả thật](evidence/challenge-recovery.json) lúc 09:07:17–09:07:20 UTC: 10/10 response thành công, P50/P95/P99 152 ms, TTFT 50 ms; health `ok=true`, `tracing_enabled=true`, mọi incident `false`. Chỉ xác nhận latency của workload hồi phục; percentile tích lũy/dashboard chưa nhất thiết giảm ngay vì còn dữ liệu incident.
- **Preventive measure:** Dùng `HighLatencyP95` (>2000 ms liên tục 5 phút), điều tra bằng correlation ID và theo dõi duration retrieval riêng. Workload ngắn này chứng minh vượt threshold, chưa chứng minh alert đã firing đủ duration hoặc đã gửi Slack. Với hệ thống thực, cân nhắc timeout/cache cho retrieval sau khi đo span; chưa triển khai hoặc đo hiệu quả các biện pháp này trong lab.
- **Cần hoàn tất cho challenge thật:** Chuỗi metric → log → trace → offending span → root cause → fix đã xác minh bằng runtime và screenshot. Ảnh `12-incident-metric.png` lúc 09:39:41 UTC có cửa sổ 08:39:41–09:39:41 UTC chứa request `req-45d62217` lúc 09:01:35 UTC; ảnh `13-incident-log.png` và `14-incident-trace.png` khớp request đó. Evidence incident đã đầy đủ. Đã thay commit `cc286c2` và commit xóa challenge theo sau bằng commit sạch `e04f63d72b7961d2e75c0819546980b22d13ef1b`, giữ nguyên cây source và các thay đổi đang stage; cập nhật `origin/main` bằng force-with-lease. Lịch sử nhánh main mới không chứa file challenge riêng; còn cần hoàn thiện commit evidence/report cuối và nộp LMS.

## 8. Giải thích và tự đánh giá

- **Quyết định kỹ thuật:** hash session ID trước khi ghi log/trace để tránh trường hợp client đưa PII vào session ID; vẫn giữ khả năng nhóm request theo session.
- **Blocker đã gặp:** Shell hiện tại không nhận `python` và không có `.venv`; tạo venv từ Python runtime sẵn có rồi cài đúng `requirements.txt`, chạy bằng `.venv\Scripts\python.exe`. API khởi động cổng 8765 và tracing được xác nhận qua health lẫn Langfuse API. PowerShell tự chuyển timestamp JSON thành datetime; khi truy vấn observations cần format UTC ISO rõ ràng, không truyền chuỗi ngày theo locale. Screenshot do học viên tự chụp, không dùng ảnh sinh bằng code.
- **Metrics → Logs → Traces:** Lúc 16:01 UTC+7, `/metrics` có P95/P99 2653 ms > SLO 2000 ms, error 0%. Từ log chọn `req-45d62217` (2653 ms), rồi observations API tìm đúng trace `6ee5e0d0fe5d4bfe8090c5a9b689ddce`. Retrieval 2503 ms so với generation 152 ms xác định retrieval là span gây chậm. Sau tắt injection, workload riêng có P95 152 ms. TTFT 50 ms của fake LLM không đại diện thời gian từ khi nhận HTTP request tới token đầu tiên, nên không suy ra người dùng chỉ chờ 50 ms.
- **Prompt/token/cost/SLO/rollback:** prompt version liên kết hành vi request với thay đổi prompt; token và cost giúp phát hiện tăng chi phí; SLO/alert báo mức ảnh hưởng; label `production` cho phép rollback mà không đổi code.
- **Điều học được và hạn chế:** Request thành công vẫn có thể vi phạm latency SLO; phải so cùng phạm vi metric và cùng correlation ID trước khi kết luận span. Evidence 01–14 đã có file hợp lệ: tests/validators dạng text, các mục còn lại dạng screenshot. Incident metric, log và trace đã khớp; PII runtime đủ bốn loại, danh sách trace và dashboard đã bổ sung. Lịch sử main chứa challenge artifact đã được thay bằng lịch sử sạch; còn cần hoàn thiện commit evidence/report cuối và nộp LMS. Học viên cần tự xác nhận phần tự đánh giá trước khi nộp.

## 9. Checklist trước khi nộp

- [x] Tests và validators đã chạy; evidence text khớp lần chạy hiện tại.
- [x] Log và evidence text không chứa API key hoặc PII thô.
- [x] Project, danh sách 10 traces, cây trace, metadata an toàn, prompt rollback và structured log/PII đủ bốn loại đã có ảnh.
- [x] Dashboard runtime đủ sáu panel, time range, đơn vị, threshold và đường dẫn ảnh.
- [x] Challenge local đã điều tra metric → log → trace; ảnh 12/13/14 cùng request/khoảng sự cố, root cause và fix đã xác minh.
- [ ] Lịch sử main chứa challenge artifact đã xử lý; xác nhận họ tên/MSSV, tự đánh giá, commit evidence/report cuối và SHA, rồi nộp repo URL/SHA trên LMS.
