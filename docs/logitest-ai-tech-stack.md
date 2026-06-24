# Tech Stack MVP cho LogiTest AI

## 1. Bối cảnh

Đề tài: **AI-Driven Behavioral Testing Platform**  
Tên hệ thống: **LogiTest AI**

Sau góp ý của mentor, demo không cần dựng microservices thật. Trọng tâm là chứng minh pipeline backend/API testing dựa trên log hành vi người dùng:

```text
Express e-commerce demo backend
        -> Elasticsearch local
        -> FastAPI LogiTest AI
        -> Journey + chaining detection
        -> Jest + Supertest generation
        -> Test execution + Golden Response comparator
        -> Next.js dashboard
```

Mock JSON logs vẫn là fallback để demo không phụ thuộc hoàn toàn vào Elasticsearch.

---

## 2. Kiến trúc được chọn

### 2.1. Demo system: Express Modular Monolith

Demo system là hệ thống cần test, dùng để tạo log thật.

Chọn **Node.js + Express.js** theo Modular Monolith vì:

- Dễ tạo API backend nhanh.
- Dễ gắn middleware sinh `session_id`, `trace_id`, `request_id`.
- Dễ ghi structured JSON log vào Elasticsearch.
- Đủ để demo login, search, cart/order và chaining.
- Không tốn thời gian vào hạ tầng microservices thật.

Modular Monolith vẫn có module rõ ràng:

```text
demo-system/
  src/
    modules/
      auth/
      products/
      cart/
      orders/
      payments/
    middlewares/
      request-context.middleware.js
      logging.middleware.js
    shared/
      logger.js
      response.js
```

Sau này có thể tách module thành service riêng nếu cần mở rộng.

### 2.2. LogiTest AI Platform: FastAPI Modular Monolith

LogiTest AI giữ **Python + FastAPI** vì project hiện tại đã có nền này và phù hợp với xử lý log/data/AI.

Module chính:

```text
apps/api/app/modules/
  ingestion/
  session_reconstruction/
  behavior_mining/
  test_generation/
  execution/
  reports/
```

Không nên rewrite platform sang Node.js trong MVP. Việc đó tốn thời gian và không tạo thêm giá trị demo trực tiếp.

---

## 3. Tech stack tổng thể

| Thành phần | Tech stack MVP | Lý do |
|---|---|---|
| Demo backend | Node.js + Express.js | Dễ dựng e-commerce API và logging middleware |
| LogiTest AI backend | Python + FastAPI | Hợp với ingestion, analysis, generation, reporting |
| Dashboard | Next.js + Tailwind CSS | Có sẵn trong repo, phù hợp dashboard demo |
| Database | PostgreSQL | Lưu sessions, logs, journeys, test cases, test runs |
| Log storage | Elasticsearch local | Primary source theo mentor |
| Fallback logs | JSON sample dataset | Dự phòng khi Elasticsearch/Docker lỗi |
| Test generation | Jest + Supertest | Primary API regression output |
| Test execution | FastAPI executor hoặc Jest runner | MVP ưu tiên reliable path |
| Deployment | Docker Compose | Đủ cho local demo |
| Optional visibility | Kibana | Chỉ thêm nếu máy chạy ổn |

---

## 4. Những công nghệ không ưu tiên trong MVP

| Công nghệ / hướng | Trạng thái | Lý do |
|---|---|---|
| Kubernetes | Future work | Quá nặng cho demo local |
| Real microservices | Future work | Mentor đã xác nhận không bắt buộc |
| RabbitMQ/Kafka | Optional | Chỉ cần nếu làm async callback mức 4 |
| Playwright UI/E2E | Future work | Đề tài ưu tiên backend/API testing |
| Local LLM nặng | Future work | MVP nên rule-based + template |
| Persona clustering nâng cao | Future work | Không phải điểm chứng minh chính |
| Grafana | Không cần | Dashboard Next.js đã đủ |

---

## 5. API demo system

E-commerce mini là lựa chọn chính.

| Flow | API | Mục đích |
|---|---|---|
| Login | `POST /api/auth/login` | Mức 1, session/user context |
| Search | `GET /api/products?keyword=...` | Mức 2, query behavior |
| Product detail | `GET /api/products/:id` | Chuẩn bị dữ liệu order |
| Cart | `GET /api/cart`, `POST /api/cart/items` | Multi-step behavior |
| Order | `POST /api/orders`, `GET /api/orders/:id` | Mức 3, chaining với `orderId` |
| Payment | `POST /api/payments`, `POST /api/payment-callback` | Optional mức 4 |

Regression toggle nên có trong demo backend, ví dụ:

```text
REGRESSION_MODE=true
```

Khi bật, demo backend có thể trả sai `order.status`, thiếu field business, hoặc đổi schema để LogiTest AI phát hiện regression.

---

## 6. Structured log schema

Log tối thiểu cần có:

```json
{
  "timestamp": "2026-06-24T10:00:00.000Z",
  "session_id": "sess_001",
  "trace_id": "trace_001",
  "request_id": "req_001",
  "user_id": "user_001",
  "method": "POST",
  "endpoint": "/api/orders",
  "request_headers": {},
  "request_payload": {},
  "response_status": 201,
  "response_body": {},
  "response_time_ms": 120,
  "service_name": "demo-ecommerce",
  "environment": "demo"
}
```

Các field nhạy cảm như `password`, `token`, `authorization`, `email`, `phone` phải được mask trước khi index vào Elasticsearch hoặc lưu vào PostgreSQL.

---

## 7. Docker Compose mục tiêu

MVP stack:

```text
services:
  database        PostgreSQL
  elasticsearch   Elasticsearch local
  demo-backend    Express e-commerce backend
  api             FastAPI LogiTest AI backend
  web             Next.js dashboard
```

Optional:

```text
  kibana          Chỉ dùng nếu cần xem log trực tiếp
```

Không thêm Kubernetes, service mesh, broker hoặc CI/CD trước khi pipeline demo chính chạy ổn.

---

## 8. Luồng dữ liệu

```text
Demo script / Postman
  -> demo-backend
  -> Elasticsearch
  -> /api/logs/import-elasticsearch
  -> PostgreSQL logs/sessions
  -> /api/behavior/analyze
  -> journeys with chaining metadata
  -> /api/test-generation/generate
  -> Jest + Supertest artifact
  -> /api/execution/test-cases/{id}/run
  -> test_runs + diff_result
  -> dashboard report
```

---

## 9. Vì sao không dùng microservices thật trong MVP?

Mentor đã xác nhận modular monolith là đủ cho demo. Microservices thật sẽ làm tăng rủi ro ở các phần không phải trọng tâm:

- Service discovery.
- Nhiều database.
- Cross-service networking.
- Docker Compose nặng.
- Debug log phân tán khó hơn.

Cách trả lời khi bảo vệ:

> Trong MVP, hệ thống cần test được triển khai dạng Modular Monolith để giảm độ phức tạp vận hành. Các module auth, products, cart, orders, payments vẫn được tách rõ và ghi structured log đầy đủ. Kiến trúc này đủ chứng minh pipeline học hành vi từ log để sinh API regression test, đồng thời có thể tách thành microservices trong tương lai.

---

## 10. Vì sao giữ FastAPI cho LogiTest AI?

FastAPI phù hợp với LogiTest AI vì:

- Project hiện tại đã có module ingestion, behavior mining, test generation bằng FastAPI.
- Python thuận tiện cho xử lý log, phân tích dữ liệu và so sánh JSON.
- Pydantic giúp định nghĩa API contract rõ.
- Không cần rewrite platform sang Node.js để đáp ứng yêu cầu mentor.

Cách trả lời khi bảo vệ:

> Demo backend dùng Node.js/Express để sinh log nghiệp vụ. LogiTest AI dùng FastAPI vì phần lõi là xử lý dữ liệu, phân tích journey, sinh test và báo cáo. Hai phần tách vai trò rõ ràng nên vừa đơn giản để demo, vừa hợp lý về kỹ thuật.

---

## 11. Vai trò của AI

Không để LLM quyết định toàn bộ pipeline. MVP chia rõ:

### Deterministic

- Parse log.
- Group session.
- Sort timestamp.
- Classify endpoint/action.
- Detect chaining cơ bản.
- Render test từ template.
- Compare status/schema/business fields/response time.

### AI / Future work

- Gợi ý tên test case.
- Giải thích regression.
- Persona clustering nâng cao.
- Edge case discovery nâng cao.
- LLM-assisted assertion proposal.

Điều này giúp demo đáng tin hơn và tránh hallucination.

---

## 12. Kết luận tech stack

```text
Demo System:
  Node.js + Express.js Modular Monolith
  Structured logging
  Elasticsearch local

LogiTest AI:
  FastAPI Modular Monolith
  PostgreSQL
  Elasticsearch import
  Rule-based journey + chaining analysis
  Jest + Supertest generation
  Execution + Golden Response comparison
  Next.js dashboard

Deployment:
  Docker Compose
```

Đây là hướng gọn hơn, dễ hoàn thành hơn và bám sát góp ý mentor hơn so với bản microservices/Kubernetes/Playwright-first ban đầu.
