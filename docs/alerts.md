# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`; duration: `5m`; kênh: Slack `#k4-l3b-alerts`; owner: `student-on-call`.
- SLI/SLO: latency của request thành công, ngưỡng 2000 ms.
- Điều kiện: P95 `response_sent.latency_ms > 2000` liên tục 5 phút. Người dùng chờ câu trả lời quá lâu.
- Kiểm tra: (1) xem P50/P95/P99, TTFT và khoảng thời gian trên dashboard; (2) lọc `response_sent` có latency cao, ghi `correlation_id`; (3) mở trace cùng ID và so thời gian retrieval với generation.
- Mitigation: nếu retrieval chậm, kiểm tra nguồn tài liệu hoặc tắt practice incident; nếu generation chậm sau đổi prompt, rollback label `production` về version trước.

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`; duration: `5m`; kênh: Slack `#k4-l3b-alerts`; owner: `student-on-call`.
- SLI/SLO: tỷ lệ request không có `response_sent`, guardrail error rate 2%.
- Điều kiện: `request_failed / request_received * 100 > 2` liên tục 5 phút. Người dùng nhận lỗi thay vì câu trả lời.
- Kiểm tra: (1) xác nhận error rate và số request trên dashboard; (2) lọc `request_failed`, đọc `error_type` và `correlation_id`; (3) mở trace cùng ID để tìm span lỗi.
- Mitigation: khôi phục dependency đang lỗi, tắt practice incident nếu có, rồi chạy lại workload để xác nhận error rate hồi phục.

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`; duration: `10m`; kênh: Slack `#k4-l3b-alerts`; owner: `student-on-call`.
- SLI/SLO: retrieval success rate, guardrail tối thiểu 90%.
- Điều kiện: `tool_success == true / tool_success != null * 100 < 90` liên tục 10 phút. Request có thể lỗi hoặc thiếu ngữ cảnh để trả lời.
- Kiểm tra: (1) xem retrieval success và error rate cùng khoảng thời gian; (2) lọc log có `tool_name=retrieval`, `tool_success=false` và lấy `correlation_id`; (3) mở trace cùng ID để xem span retrieval và lỗi.
- Mitigation: khôi phục nguồn retrieval, tắt practice incident nếu có, xác nhận tỷ lệ hồi phục trước khi đóng cảnh báo.
