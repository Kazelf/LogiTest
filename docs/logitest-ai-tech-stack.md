# Đề xuất Tech Stack cho hệ thống demo LogiTest AI

## 1. Bối cảnh hệ thống

Đề tài: **AI-Driven Behavioral Testing Platform**  
Tên gợi ý hệ thống: **LogiTest AI**

Mục tiêu của hệ thống là xây dựng một nền tảng tự động hóa kiểm thử backend dựa trên phân tích hành vi người dùng từ log thực tế.

Luồng tổng quát:

```text
Production / Demo Microservice System
        ↓
ELK Stack / Elasticsearch
        ↓
LogiTest AI
        ↓
AI phân tích hành vi người dùng
        ↓
Sinh test case tự động
        ↓
Chạy test trên Staging / UAT
        ↓
So sánh với Golden Response
        ↓
Sinh báo cáo regression
```

Định hướng kiến trúc được chọn:

- **Hệ thống cần test:** Microservice
- **Hệ thống LogiTest AI:** Modular Monolith
- **AI Engine:** Python-based AI module / background worker trong LogiTest AI
- **Triển khai demo:** Docker Compose

---

## 2. Vì sao chia như vậy?

### 2.1. Hệ thống cần test nên là Microservice

Hệ thống cần test nên được xây dựng theo kiến trúc microservice vì đề tài tập trung vào bài toán kiểm thử hồi quy trong môi trường có nhiều service, nhiều API và nhiều luồng nghiệp vụ.

Microservice giúp demo rõ các yếu tố sau:

- Có nhiều service phát sinh log khác nhau.
- Có nhiều API endpoint để AI phân tích.
- Có thể sinh `trace_id`, `session_id` để xâu chuỗi hành vi người dùng.
- Có thể mô phỏng lỗi hồi quy ở một service cụ thể.
- Thể hiện rõ giá trị của LogiTest AI trong môi trường phức tạp.

Ví dụ:

```text
User login
→ search product
→ view detail
→ add to cart
→ checkout
→ payment
→ view order
```

Hoặc nếu demo theo hệ thống quiz:

```text
Student login
→ join class
→ start exam
→ answer questions
→ submit exam
→ view result
```

---

### 2.2. LogiTest AI nên là Modular Monolith

LogiTest AI không nên làm microservice ngay trong bản demo vì hệ thống đã có nhiều thành phần phức tạp như:

- Kết nối Elasticsearch
- Phân tích log
- Tái dựng session
- Sequence mining
- Clustering persona
- Sinh test case
- Chạy test
- So sánh kết quả
- Sinh báo cáo

Nếu tiếp tục chia LogiTest AI thành nhiều microservice, độ phức tạp triển khai sẽ tăng mạnh, dễ mất thời gian vào hạ tầng thay vì tập trung vào giá trị AI.

Vì vậy, lựa chọn hợp lý là:

```text
LogiTest AI = Modular Monolith
```

Tức là hệ thống vẫn là một backend chính, nhưng code được chia module rõ ràng. Sau này có thể tách từng module thành microservice riêng.

Cách trình bày khi bảo vệ:

> Trong bản demo, LogiTest AI được triển khai theo kiến trúc Modular Monolith để giảm độ phức tạp vận hành. Tuy nhiên, các module như ingestion, AI engine, test generation và execution được thiết kế tách biệt để có thể tách thành microservice riêng trong tương lai.

---

## 3. Tech stack tổng thể

| Thành phần | Tech stack đề xuất | Lý do |
|---|---|---|
| Demo system cần test | Node.js + NestJS Microservices | Dễ chia service, có cấu trúc rõ ràng, phù hợp demo |
| API Gateway | NestJS Gateway / Nginx | Gom request, gắn `trace_id`, `session_id` |
| Database cho demo system | PostgreSQL | Phù hợp nghiệp vụ thật, dễ seed data |
| Message broker | RabbitMQ | Dùng nếu muốn demo giao tiếp async |
| Logging | Pino / Winston + JSON structured log | Dễ đẩy vào Elasticsearch |
| Log storage | Elasticsearch + Kibana | Đúng với hướng ELK của đề tài |
| LogiTest AI frontend | Next.js + Tailwind CSS + shadcn/ui | Làm dashboard nhanh, đẹp, dễ trình bày |
| LogiTest AI backend | Python FastAPI | Phù hợp xử lý AI, log, data processing |
| LogiTest AI database | PostgreSQL | Lưu project, journey, test case, report |
| AI / ML | pandas, scikit-learn, LangChain / LangGraph, OpenAI API / Gemini API | Phù hợp phân tích hành vi và sinh test |
| Test generation | Jinja2 template + LLM | Sinh file test có cấu trúc |
| API testing | pytest + requests / httpx | Chạy test backend FastAPI |
| E2E testing | Playwright | Mô phỏng hành vi người dùng |
| JSON comparison | deepdiff, jsonschema | So sánh Golden Response |
| Deployment | Docker Compose | Phù hợp demo, dễ chạy local |

---

## 4. Kiến trúc hệ thống cần test

Nên xây dựng một hệ thống nhỏ nhưng có đủ luồng nghiệp vụ, ví dụ e-commerce mini hoặc quiz mini.

### 4.1. Phương án khuyên dùng: E-commerce mini

```text
Demo Microservice System
│
├── API Gateway
│
├── Auth Service
│   └── PostgreSQL
│
├── Product Service
│   └── PostgreSQL
│
├── Cart / Order Service
│   └── PostgreSQL
│
├── Payment Mock Service
│   └── PostgreSQL
│
└── Logging Middleware
    └── gửi log sang Elasticsearch
```

Luồng demo:

```text
Login
→ Search product
→ View product detail
→ Add to cart
→ Checkout
→ Payment
→ View order history
```

Lý do nên chọn e-commerce:

- Hội đồng dễ hiểu.
- Có hành vi người dùng rõ ràng.
- Có nhiều API để sinh log.
- Có thể tạo lỗi hồi quy dễ dàng, ví dụ:
  - Payment trả sai status.
  - Order tạo thiếu item.
  - Product detail đổi schema.
  - Checkout trả sai total price.

---

### 4.2. Phương án thay thế: Quiz mini

```text
Demo Microservice System
│
├── API Gateway
│
├── Auth Service
│
├── Class Service
│
├── Exam Service
│
├── Submission Service
│
└── Result Service
```

Luồng demo:

```text
Student login
→ Join class
→ Start exam
→ Submit answer
→ Finish exam
→ View result
```

Phương án này gần với các project học tập của bạn hơn, nhưng có thể khó giải thích hơn e-commerce nếu hội đồng muốn nhìn luồng nghiệp vụ phổ thông.

---

## 5. Kiến trúc LogiTest AI

```text
LogiTest AI
│
├── Frontend: Next.js Dashboard
│
└── Backend: FastAPI Modular Monolith
    │
    ├── Project Module
    ├── Elasticsearch Connector Module
    ├── Log Ingestion Module
    ├── Masking / Anonymization Module
    ├── Session Reconstruction Module
    ├── Behavior Mining Module
    ├── Persona Detection Module
    ├── Test Case Generator Module
    ├── Test Execution Module
    └── Report Module
```

---

## 6. Module chi tiết của LogiTest AI

### 6.1. Project Module

Quản lý các project cần phân tích.

Chức năng:

- Tạo project
- Cấu hình Elasticsearch URL
- Cấu hình index log
- Cấu hình môi trường Staging / UAT
- Cấu hình loại test cần sinh: API test hoặc E2E test

---

### 6.2. Elasticsearch Connector Module

Kết nối và truy vấn log từ Elasticsearch.

Dữ liệu cần lấy:

- `timestamp`
- `trace_id`
- `session_id`
- `user_id`
- `service_name`
- `method`
- `endpoint`
- `request_payload`
- `response_status`
- `response_body`
- `response_time`

---

### 6.3. Log Ingestion Module

Chuẩn hóa log sau khi lấy từ Elasticsearch.

Nhiệm vụ:

- Parse log
- Chuẩn hóa format
- Loại bỏ log lỗi không cần thiết
- Lưu log đã xử lý vào PostgreSQL
- Chuẩn bị dữ liệu cho AI Engine

---

### 6.4. Masking / Anonymization Module

Ẩn dữ liệu nhạy cảm trước khi đưa vào AI hoặc sinh test.

Các dữ liệu cần mask:

- Token
- Password
- Email
- Số điện thoại
- Địa chỉ
- Thông tin thanh toán
- Dữ liệu định danh cá nhân

Ví dụ:

```json
{
  "email": "user_001@example.com",
  "password": "***MASKED***",
  "token": "***MASKED***"
}
```

---

### 6.5. Session Reconstruction Module

Tái dựng hành trình người dùng từ log.

Cách làm:

```text
Group log theo session_id
→ Sort theo timestamp
→ Gom các request liên tiếp thành journey
→ Gắn trace_id nếu có request liên quan giữa nhiều service
```

Output:

```text
Session A:
1. POST /auth/login
2. GET /products
3. GET /products/123
4. POST /cart/items
5. POST /orders
6. POST /payments
```

---

### 6.6. Behavior Mining Module

Phân tích hành vi người dùng.

Có thể dùng kết hợp:

- Rule-based processing
- Sequence mining
- Frequency analysis
- Clustering
- LLM summarization

Nhiệm vụ:

- Tìm luồng phổ biến
- Tìm luồng hiếm nhưng quan trọng
- Tìm edge cases
- Xác định điểm dễ phát sinh regression

---

### 6.7. Persona Detection Module

Gom nhóm người dùng theo hành vi.

Ví dụ persona:

| Persona | Mô tả |
|---|---|
| Buyer | Người dùng tìm kiếm, thêm giỏ hàng, thanh toán |
| Browser | Người dùng chỉ xem sản phẩm, ít mua |
| Failed Payment User | Người dùng có nhiều giao dịch lỗi |
| Admin | Người dùng thao tác quản trị dữ liệu |

---

### 6.8. Test Case Generator Module

Sinh test case từ journey đã phát hiện.

Output có thể gồm:

- Tên test case
- Mô tả test case
- Danh sách API step
- Request payload
- Expected status
- Expected response schema
- Golden response
- File test tự động

Ví dụ test case:

```text
Test case: Buyer checkout successfully

Steps:
1. Login
2. Search product
3. View product detail
4. Add product to cart
5. Create order
6. Make payment
7. Verify order status
```

---

### 6.9. Test Execution Module

Chạy test đã sinh trên môi trường Staging hoặc UAT.

Có thể chạy:

- API test bằng `pytest + requests`
- E2E test bằng `Playwright`
- Test runner trong Docker container

---

### 6.10. Report Module

Sinh báo cáo kết quả test.

Thông tin cần hiển thị:

- Tổng số test case
- Số test pass
- Số test fail
- Tỉ lệ pass/fail
- Lỗi regression
- Endpoint bị lỗi
- Expected response
- Actual response
- Response time
- Trace/session liên quan

---

## 7. Vì sao dùng Python FastAPI cho LogiTest AI?

Với nghiệp vụ AI nặng, Python phù hợp hơn Node.js vì hệ sinh thái xử lý dữ liệu và AI tốt hơn.

Các phần phù hợp với Python:

| Nhu cầu | Thư viện Python phù hợp |
|---|---|
| Xử lý log | pandas, polars |
| Sequence mining | prefixspan, mlxtend |
| Clustering persona | scikit-learn |
| LLM orchestration | LangChain, LangGraph |
| Sinh template test | Jinja2 |
| So sánh JSON | deepdiff |
| Validate schema | jsonschema |
| API test | pytest, requests |

FastAPI phù hợp vì:

- Dễ viết REST API.
- Tốc độ tốt.
- Tích hợp tốt với Pydantic.
- Dễ chia module.
- Phù hợp với AI backend.
- Dễ chạy bằng Docker.

---

## 8. Có nên dùng Node.js cho LogiTest AI không?

Có thể dùng Node.js/NestJS, nhưng không phải lựa chọn tốt nhất cho phần AI.

Node.js phù hợp với:

- API CRUD
- Gateway
- Realtime
- WebSocket
- Business backend

Nhưng LogiTest AI cần nhiều xử lý:

```text
log parsing
→ session reconstruction
→ sequence mining
→ clustering
→ prompt LLM
→ test generation
→ golden response comparison
```

Các phần này Python làm nhanh và tự nhiên hơn.

Vì vậy, lựa chọn khuyên dùng:

```text
Demo System: NestJS Microservices
LogiTest AI: FastAPI Modular Monolith
```

---

## 9. Vai trò của AI trong hệ thống

Không nên để LLM làm toàn bộ pipeline. Nên chia rõ phần deterministic và phần AI.

### 9.1. Phần deterministic

Các phần nên xử lý bằng code thông thường:

- Parse log
- Group theo `session_id`
- Sort theo `timestamp`
- Extract endpoint sequence
- Mask dữ liệu nhạy cảm
- Build golden response
- Compare response code
- Compare response schema
- Compare response body
- Generate report

### 9.2. Phần AI / ML

Các phần nên dùng AI:

- Nhận diện journey phổ biến
- Gom nhóm persona
- Phát hiện edge case
- Đặt tên test case
- Sinh mô tả test case
- Đề xuất assertion
- Sinh code test từ template
- Giải thích nguyên nhân test fail

Cách làm này giúp hệ thống đáng tin cậy hơn, tránh phụ thuộc hoàn toàn vào LLM.

---

## 10. Docker Compose đề xuất

### 10.1. Bản đầy đủ

```text
docker-compose.yml

1. logitest-frontend
2. logitest-backend
3. logitest-postgres
4. elasticsearch
5. kibana
6. demo-api-gateway
7. demo-auth-service
8. demo-product-service
9. demo-order-service
10. demo-payment-mock-service
11. playwright-runner
12. rabbitmq
```

### 10.2. Bản gọn để demo

```text
docker-compose.yml

1. logitest-frontend
2. logitest-backend
3. postgres
4. elasticsearch
5. kibana
6. demo-api-gateway
7. demo-auth-service
8. demo-product-service
9. demo-order-service
```

Khuyến nghị dùng bản gọn nếu thời gian ít.

---

## 11. Luồng demo đề xuất

```text
Bước 1: User thao tác trên Demo Microservice System
        ↓
Bước 2: Các service sinh JSON structured logs
        ↓
Bước 3: Logs được đẩy vào Elasticsearch
        ↓
Bước 4: LogiTest AI đọc logs từ Elasticsearch
        ↓
Bước 5: LogiTest AI reconstruct session theo session_id / trace_id
        ↓
Bước 6: AI phát hiện user journeys phổ biến
        ↓
Bước 7: AI phân loại persona / edge cases
        ↓
Bước 8: AI sinh test case API hoặc Playwright
        ↓
Bước 9: Test runner chạy test trên Staging / UAT
        ↓
Bước 10: So sánh actual response với Golden Response
        ↓
Bước 11: Dashboard hiển thị pass/fail/regression report
```

---

## 12. Luồng dữ liệu chi tiết

```text
[Demo Frontend]
      |
      v
[API Gateway]
      |
      v
[Microservices]
      |
      v
[Structured Logs]
      |
      v
[Elasticsearch]
      |
      v
[LogiTest AI - Ingestion Module]
      |
      v
[Session Reconstruction]
      |
      v
[Behavior Mining / Persona Detection]
      |
      v
[Test Case Generator]
      |
      v
[Test Runner]
      |
      v
[Regression Report]
```

---

## 13. Cấu trúc repo đề xuất

Có thể dùng monorepo để dễ quản lý demo.

```text
logitest-ai-platform/
│
├── demo-system/
│   ├── api-gateway/
│   ├── auth-service/
│   ├── product-service/
│   ├── order-service/
│   └── payment-mock-service/
│
├── logitest-ai-frontend/
│   └── Next.js dashboard
│
├── logitest-ai-backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── modules/
│   │   │   ├── projects/
│   │   │   ├── elasticsearch_connector/
│   │   │   ├── ingestion/
│   │   │   ├── masking/
│   │   │   ├── session_reconstruction/
│   │   │   ├── behavior_mining/
│   │   │   ├── persona/
│   │   │   ├── test_generation/
│   │   │   ├── execution/
│   │   │   └── reports/
│   │   └── workers/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── generated-tests/
│   ├── api-tests/
│   └── e2e-tests/
│
├── docker-compose.yml
└── README.md
```

---

## 14. Structured log format đề xuất

Mỗi service trong demo system nên ghi log dạng JSON.

Ví dụ:

```json
{
  "timestamp": "2026-06-23T10:00:00Z",
  "level": "info",
  "service_name": "order-service",
  "trace_id": "trace-abc-123",
  "session_id": "session-user-001",
  "user_id": "user-001",
  "method": "POST",
  "endpoint": "/orders",
  "request_payload": {
    "cart_id": "cart-001",
    "payment_method": "mock_card"
  },
  "response_status": 201,
  "response_body": {
    "order_id": "order-001",
    "status": "created",
    "total": 250000
  },
  "response_time_ms": 120
}
```

Các field quan trọng:

| Field | Ý nghĩa |
|---|---|
| `timestamp` | Thời điểm request xảy ra |
| `service_name` | Service phát sinh log |
| `trace_id` | Theo dõi một request qua nhiều service |
| `session_id` | Theo dõi hành trình của một user |
| `user_id` | Người dùng thực hiện hành động |
| `endpoint` | API được gọi |
| `request_payload` | Dữ liệu gửi lên |
| `response_status` | HTTP status |
| `response_body` | Response thực tế |
| `response_time_ms` | Thời gian phản hồi |

---

## 15. Golden Response là gì?

Golden Response là dữ liệu phản hồi chuẩn được lấy từ log thực tế.

Ví dụ, trong production log:

```json
{
  "endpoint": "/orders",
  "response_status": 201,
  "response_body": {
    "order_id": "order-001",
    "status": "created",
    "total": 250000
  }
}
```

Khi test chạy trên Staging/UAT, hệ thống gọi lại API tương ứng.

Nếu actual response là:

```json
{
  "endpoint": "/orders",
  "response_status": 201,
  "response_body": {
    "order_id": "order-001",
    "status": "pending",
    "total": 250000
  }
}
```

LogiTest AI phát hiện sai khác:

```text
Expected status: created
Actual status: pending
Result: Regression detected
```

---

## 16. Những điểm nên show khi demo

Khi demo trước hội đồng, nên tập trung vào các điểm sau:

### 16.1. Show hệ thống microservice sinh log

Chứng minh hệ thống cần test có nhiều service và log được ghi lại đầy đủ.

Nên show:

- API Gateway
- Một vài service backend
- Log JSON có `trace_id`, `session_id`
- Elasticsearch/Kibana có dữ liệu log

---

### 16.2. Show LogiTest AI đọc log

Nên show:

- Chọn project
- Kết nối Elasticsearch
- Chọn index log
- Import logs
- Danh sách session được tái dựng

---

### 16.3. Show AI phân tích hành vi

Nên show:

- Top user journeys
- Endpoint sequence
- Persona detection
- Edge case detection

Ví dụ:

```text
Journey 1: Login → Search → View Product → Add to Cart → Checkout
Frequency: 56 sessions
Persona: Buyer
```

---

### 16.4. Show sinh test case

Nên show:

- Test case name
- Steps
- Request payload
- Expected response
- Generated test code

---

### 16.5. Show chạy test và phát hiện regression

Đây là phần quan trọng nhất.

Kịch bản demo nên có lỗi cố tình tạo ra:

- Production log ghi order status là `created`
- Staging service trả về order status là `pending`
- LogiTest AI phát hiện regression

---

### 16.6. Show dashboard report

Nên hiển thị:

- Total test cases
- Passed
- Failed
- Regression detected
- Failed endpoint
- Expected vs actual
- Severity

---

## 17. Các công nghệ không nên dùng trong bản demo

### 17.1. Không nên dùng Kubernetes cho demo chính

Kubernetes phù hợp production, nhưng bản demo sẽ phức tạp và khó kiểm soát.

Nên nói:

> Trong bản demo, hệ thống sử dụng Docker Compose để đơn giản hóa triển khai. Kubernetes được xem là hướng mở rộng trong tương lai khi hệ thống cần scale độc lập từng service.

---

### 17.2. Không nên dùng quá nhiều message broker

Nếu chưa cần async thật sự, không nên ép RabbitMQ/Kafka vào.

Có thể dùng RabbitMQ cho một luồng nhỏ như:

```text
Order Service → publish event → Payment Mock Service
```

Nhưng nếu thời gian ít, có thể bỏ RabbitMQ và dùng REST.

---

### 17.3. Không nên để LLM sinh test tự do hoàn toàn

Nên dùng template để kiểm soát output.

Cách tốt hơn:

```text
AI phân tích journey
→ hệ thống tạo test spec dạng JSON
→ Jinja2 render thành code test
```

---

## 18. Câu trả lời ngắn gọn khi mentor hỏi

### Câu hỏi: Vì sao hệ thống cần test là microservice?

Trả lời:

> Vì mục tiêu của đề tài là phát hiện lỗi hồi quy trong môi trường nhiều service, nhiều API và log phân tán. Microservice giúp mô phỏng hệ thống thực tế tốt hơn, tạo ra log có `trace_id`, `session_id`, từ đó LogiTest AI có thể tái dựng hành vi người dùng và sinh test case có giá trị hơn.

---

### Câu hỏi: Vì sao LogiTest AI không làm microservice?

Trả lời:

> Vì trong bản demo, trọng tâm là chứng minh pipeline AI-driven testing, không phải độ phức tạp hạ tầng. Do đó, LogiTest AI được xây dựng theo Modular Monolith để dễ triển khai, dễ debug và giảm rủi ro. Các module vẫn được tách rõ để sau này có thể tách thành microservice riêng.

---

### Câu hỏi: Vì sao chọn Python FastAPI?

Trả lời:

> Vì LogiTest AI xử lý nhiều tác vụ AI và data processing như phân tích log, sequence mining, clustering, LLM và sinh test case. Python có hệ sinh thái thư viện mạnh hơn cho các tác vụ này, còn FastAPI giúp xây dựng REST API nhanh, rõ ràng và dễ tích hợp với frontend.

---

### Câu hỏi: Vì sao không dùng Node.js cho LogiTest AI?

Trả lời:

> Node.js phù hợp với API business và realtime, nhưng phần lõi của LogiTest AI là xử lý dữ liệu và AI. Các thư viện như pandas, scikit-learn, LangChain, DeepDiff, jsonschema và pytest trong Python phù hợp hơn cho pipeline này.

---

### Câu hỏi: AI có sinh test chính xác không?

Trả lời:

> Hệ thống không để LLM quyết định toàn bộ. Các bước parse log, group session, sort timeline, compare response và validate schema được xử lý deterministic bằng code. AI chỉ hỗ trợ nhận diện pattern, đặt tên test case, phát hiện edge case và đề xuất assertion. Vì vậy hệ thống giảm rủi ro hallucination.

---

### Câu hỏi: Golden Response là gì?

Trả lời:

> Golden Response là response chuẩn được lấy từ log thực tế. Khi test chạy lại trên Staging hoặc UAT, hệ thống so sánh actual response với Golden Response để phát hiện sai khác như status code, schema, business data hoặc response time.

---

## 19. Kết luận lựa chọn cuối cùng

Tech stack nên chọn:

```text
Demo System cần test:
NestJS Microservices
+ PostgreSQL
+ JSON structured logging
+ Elasticsearch / Kibana
+ Docker Compose

LogiTest AI:
Next.js Dashboard
+ FastAPI Modular Monolith
+ PostgreSQL
+ Elasticsearch Python Client
+ pandas / scikit-learn
+ LangChain hoặc LangGraph
+ OpenAI API hoặc Gemini API
+ Playwright / pytest runner
+ Docker Compose
```

Câu chốt khi trình bày:

> Hệ thống được chia thành hai phần. Phần hệ thống cần kiểm thử được xây dựng theo kiến trúc microservices để mô phỏng môi trường thực tế có nhiều API, nhiều service và log phân tán. Phần LogiTest AI được xây dựng theo kiến trúc modular monolith bằng FastAPI để tập trung xử lý AI, phân tích log, sinh test case và báo cáo. Cách thiết kế này giúp bản demo đơn giản hơn nhưng vẫn đảm bảo khả năng mở rộng trong tương lai.
