# AI-Driven Behavioral Testing Platform

## 1. Tên đề tài

**Hệ thống tự động hóa kiểm thử Backend dựa trên phân tích hành vi người dùng**  
**AI-Driven Behavioral Testing Platform**

---

## 2. Mô tả đề tài

LogiTest AI là nền tảng demo tự động phân tích log API từ hành vi người dùng, tái dựng user journey, sinh API regression test, chạy lại test trên môi trường local/staging, rồi so sánh kết quả với Golden Response để phát hiện lỗi hồi quy.

Sau góp ý của mentor, MVP không cần chứng minh bằng microservices thật. Bản demo ưu tiên một hệ thống nghiệp vụ **E-commerce Modular Monolith** dễ chạy, dễ bảo vệ, nhưng vẫn đủ hành vi backend quan trọng: login, search, cart/order, API chaining và optional payment callback.

---

## 3. Định hướng MVP mới

MVP tập trung vào pipeline có thể demo end-to-end:

```text
Postman / demo script
        |
        v
Express E-commerce Demo Backend
        |
        | structured API logs
        v
Elasticsearch local
        |
        v
FastAPI LogiTest AI Platform
        |
        v
Journey detection + chaining detection
        |
        v
Jest + Supertest API test generation
        |
        v
Test execution + Golden Response comparison
        |
        v
Next.js dashboard + regression report
```

Mock JSON logs vẫn được giữ làm fallback để tránh hỏng demo nếu Elasticsearch hoặc Docker gặp lỗi.

---

## 4. Mục tiêu chính

- Thu thập hoặc import structured API logs từ Elasticsearch local.
- Chuẩn hóa log và lưu vào PostgreSQL.
- Gom log theo `session_id`, `trace_id`, `request_id`.
- Nhận diện user journey như `LOGIN_FLOW`, `SEARCH_FLOW`, `ORDER_CREATION_FLOW`.
- Phát hiện API chaining, ví dụ `POST /api/orders` trả `orderId`, sau đó `GET /api/orders/:id` dùng lại `orderId`.
- Sinh API regression test bằng **Jest + Supertest**.
- Chạy test trên demo backend local/staging.
- So sánh status code, response schema, business fields và response time với Golden Response.
- Hiển thị raw logs, detected journeys, generated tests, execution result và regression report trên dashboard.

---

## 5. Phạm vi MVP

### 5.1. Must-have

- Demo e-commerce backend bằng Node.js + Express.js theo Modular Monolith.
- API: login, search product, product detail, cart, create order, get order detail.
- Structured logging middleware có `session_id`, `trace_id`, `request_id`.
- Elasticsearch local làm nguồn log chính.
- Mock JSON import làm fallback.
- FastAPI platform xử lý ingestion, normalize, journey analysis, test generation, execution/report.
- PostgreSQL lưu logs, journeys, generated tests và test runs.
- Jest + Supertest là output test chính.
- Next.js dashboard trình bày pipeline demo.

### 5.2. Future work

- Playwright UI/E2E test generation.
- Persona detection nâng cao.
- LLM-based explanation hoặc LLM-based generation tự do.
- Async callback/payment notification mức 4 nếu còn thời gian.
- CI/CD auto-run test.
- Kubernetes.
- Tách hệ thống demo thành microservices thật.

---

## 6. Demo system cần test

Demo system nên là e-commerce mini vì hội đồng dễ hiểu và đủ hành vi backend:

| Mức | Hành vi | API minh họa | Mục đích |
|---|---|---|---|
| 1 | Login | `POST /api/auth/login` | Chứng minh request/response/status/session |
| 2 | Search | `GET /api/products?keyword=...` | Chứng minh truy vấn và biến thể input |
| 3 | Create order | `GET /api/cart` -> `POST /api/orders` -> `GET /api/orders/:id` | Chứng minh API chaining |
| 4 | Payment callback | `POST /api/payments` -> `POST /api/payment-callback` | Optional, chứng minh async/callback |

Trong MVP, mức 1-3 là bắt buộc. Mức 4 là bonus.

---

## 7. Module chính của LogiTest AI

### 7.1. Data Ingestion

- Query log từ Elasticsearch theo index/time range.
- Import fallback từ `mock-data/logs.json`.
- Normalize log về schema chung.
- Mask dữ liệu nhạy cảm như password, token, email, phone.
- Lưu log vào PostgreSQL.

### 7.2. Journey Analyzer

- Group logs theo `session_id` hoặc `trace_id`.
- Sort theo timestamp.
- Classify journey type bằng rule-based detection.
- Detect output-input chaining.
- Lưu journey JSON để sinh test.

### 7.3. Test Generator

- Nhận journey JSON.
- Sinh test case và artifact Jest + Supertest.
- Giữ đúng thứ tự request.
- Extract biến từ response trước và inject vào request sau.
- Assert status code, schema, business fields và response time threshold.

### 7.4. Execution & Reporting

- Chạy generated test hoặc persisted JSON steps against demo backend.
- Lưu actual response và diff result.
- So sánh với Golden Response.
- Không so sánh full response body mặc định vì các field động như `id`, `createdAt`, `token`, `orderCode` dễ làm test fail giả.

### 7.5. Dashboard

Dashboard cần hiển thị:

- Raw Logs
- Sessions
- Detected Journeys
- Journey Detail
- Generated Test Cases
- Test Script Viewer
- Execution Results
- Regression Report

---

## 8. Kiến trúc triển khai demo

```text
logitest-ai/
  demo-system/        Express e-commerce modular monolith
  apps/api/           FastAPI LogiTest AI modular monolith
  apps/web/           Next.js dashboard
  packages/shared/    Shared TypeScript schemas
  mock-data/          JSON fallback logs
  database/           PostgreSQL migrations
  generated-tests/    Generated Jest/Supertest artifacts
  docker-compose.yml  Local demo stack
```

Docker Compose mục tiêu:

```text
services:
  database
  elasticsearch
  demo-backend
  api
  web
```

Kibana có thể thêm nếu máy chạy ổn, nhưng không bắt buộc cho MVP.

---

## 9. Golden Response

Golden Response là response chuẩn lấy từ log đã học được. Khi chạy lại test trên local/staging, LogiTest AI so sánh actual response với Golden Response theo thứ tự ưu tiên:

1. Status code.
2. Response schema.
3. Business fields ổn định.
4. Response time threshold.
5. Full body chỉ dùng cho response thật sự ổn định.

Ví dụ regression:

```text
Golden: POST /api/orders -> status = "created"
Actual: POST /api/orders -> status = "pending"
Result: Regression detected
```

---

## 10. Kịch bản demo bảo vệ

1. Chạy Docker Compose.
2. Chạy Postman collection hoặc demo script để tạo log.
3. Mở dashboard Raw Logs để chứng minh log đã vào Elasticsearch/platform.
4. Bấm Analyze Journey.
5. Hiển thị `LOGIN_FLOW`, `SEARCH_FLOW`, `ORDER_CREATION_FLOW`.
6. Mở Journey Detail và chỉ ra `orderId` chaining.
7. Bấm Generate Test.
8. Hiển thị Jest + Supertest code.
9. Bấm Run Test.
10. Hiển thị pass.
11. Bật regression mode ở demo backend.
12. Run lại test.
13. Hiển thị fail và regression report.

---

## 11. Công nghệ đề xuất

| Thành phần | Công nghệ MVP | Ghi chú |
|---|---|---|
| Demo Business System | Node.js + Express.js | Modular Monolith, dễ sinh log |
| LogiTest AI Backend | Python + FastAPI | Modular Monolith cho ingestion/analyzer/generator/report |
| Dashboard | Next.js + Tailwind CSS | Operational dashboard |
| Log Storage | Elasticsearch local | Primary source |
| Fallback Source | JSON sample logs | Dự phòng khi demo |
| Database | PostgreSQL | Lưu logs, journeys, generated tests, reports |
| Test Generation | Jest + Supertest | Primary output |
| Optional E2E | Playwright | Future work |
| Deployment | Docker Compose | Đủ cho demo local |

---

## 12. Ghi chú bảo mật dữ liệu

Log cần được mask trước khi lưu hoặc sinh test. Các field phải xử lý cẩn thận:

- `password`
- `token`
- `authorization`
- `email`
- `phone`
- thông tin thanh toán
- thông tin định danh cá nhân

MVP chỉ dùng dữ liệu demo/seed, nhưng vẫn phải thể hiện rõ tư duy masking để bảo vệ đề tài.
