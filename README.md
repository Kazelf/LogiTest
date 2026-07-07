# LogiTest

LogiTest là nền tảng demo kiểm thử hồi quy dựa trên hành vi người dùng. Repo này chạy cùng lúc hai phần:

- **LogiTest AI**: dashboard Next.js + API FastAPI để nhập log, phát hiện journey, sinh test Jest/Supertest và xem báo cáo regression.
- **ShopLite**: ứng dụng ecommerce demo bằng React + Express, dùng làm hệ thống cần kiểm thử và nguồn sinh log hành vi.

## Kiến trúc nhanh

```text
Người dùng thao tác trên ShopLite
        |
        v
ShopLite API ghi structured logs
        |
        v
Elasticsearch / JSONL logs
        |
        v
LogiTest AI API phân tích journey
        |
        v
PostgreSQL + generated tests + test runs
        |
        v
Dashboard LogiTest AI
```

## Cấu trúc repo

```text
.
├── docker-compose.yml          # stack local đầy đủ
├── Dockerfile                  # image chạy cả LogiTest AI và ShopLite
├── docker/                     # entrypoint và init database
├── logitest-ai/                # dashboard, FastAPI API, schema DB, shared package
└── shoplite/                   # ecommerce demo: React client + Express server
```

## Chạy nhanh bằng Docker

Yêu cầu: Docker Desktop.

```powershell
# Chạy từ thư mục gốc repo
docker compose up --build
```

Sau khi các service khởi động:

| Service | URL |
| --- | --- |
| LogiTest dashboard | `http://localhost:3000` |
| LogiTest API health | `http://localhost:8000/health` |
| ShopLite frontend | `http://localhost:5173` |
| ShopLite API health | `http://localhost:4000/health` |
| Elasticsearch | `http://localhost:9200` |
| PostgreSQL LogiTest | `localhost:5432`, database `logitest_ai` |
| PostgreSQL ShopLite | `localhost:5433`, database `shoplite` |

Stack Docker sẽ tự:

- tạo database `logitest_ai` và `shoplite`;
- chạy migration LogiTest;
- chạy Prisma migration và seed dữ liệu ShopLite;
- bật Elasticsearch logging;
- chạy 4 app process trong một container app.

## Luồng demo

1. Mở ShopLite tại `http://localhost:5173`.
2. Đăng nhập bằng user demo, ví dụ `normal_buyer@example.com` / `Password123`.
3. Tạo traffic ecommerce: tìm sản phẩm, xem chi tiết, thêm giỏ hàng, checkout, thanh toán.
4. Mở LogiTest dashboard tại `http://localhost:3000`.
5. Bấm `Run Full Pipeline`.
6. Xem các tab `Logs`, `Sessions`, `Journeys`, `Test Cases`, `Runs`, `Report`.

Luồng thủ công trên dashboard:

```text
Import from ES -> Analyze -> Generate Jest -> Run Test -> Report
```

## Reset dữ liệu local

Xóa toàn bộ volume PostgreSQL và Elasticsearch:

```powershell
docker compose down -v
docker compose up --build
```

Chỉ xóa journey/test đã phân tích trong database LogiTest:

```powershell
docker compose exec postgres psql -U logitest -d logitest_ai -c "DELETE FROM test_case_artifacts; DELETE FROM test_cases; DELETE FROM journeys;"
```

## Phát triển thủ công

Chạy hạ tầng trước:

```powershell
docker compose up -d postgres elasticsearch
```

### LogiTest API

```powershell
cd .\logitest-ai\apps\api
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:DATABASE_URL="postgresql://logitest:logitest@localhost:5432/logitest_ai"
$env:ELASTICSEARCH_URL="http://localhost:9200"
$env:STAGING_API_BASE_URL="http://localhost:4000"
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

### LogiTest dashboard

```powershell
cd .\logitest-ai
npm install
npm run build --workspace @logitest/shared
npm run dev --workspace web
```

### ShopLite API

```powershell
cd .\shoplite\server
npm install
$env:DATABASE_URL="postgresql://shoplite:shoplite@localhost:5433/shoplite?schema=public"
$env:ENABLE_ELASTICSEARCH_LOGGING="true"
$env:ELASTICSEARCH_URL="http://localhost:9200"
npm run prisma:generate
npm run prisma:migrate
npm run seed
npm run dev
```

### ShopLite frontend

```powershell
cd .\shoplite\client
npm install
npm run dev
```

## Test

LogiTest API:

```powershell
cd .\logitest-ai\apps\api
$env:PYTHONPATH=(Get-Location).Path
.\.venv\Scripts\python -m pytest
```

ShopLite API:

```powershell
cd .\shoplite\server
npm test
```

Demo lỗi regression thanh toán:

```powershell
cd .\shoplite\server
npm run test:regression
```

## Biến môi trường chính

| Biến | Ý nghĩa |
| --- | --- |
| `DATABASE_URL` | PostgreSQL URL cho LogiTest API |
| `SHOPLITE_DATABASE_URL` | PostgreSQL URL cho ShopLite |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint |
| `DEMO_LOG_INDEX` | index log demo trong Elasticsearch |
| `NEXT_PUBLIC_API_BASE_URL` | URL FastAPI cho dashboard |
| `STAGING_API_BASE_URL` | target để chạy generated tests, thường là ShopLite API |
| `ENABLE_ELASTICSEARCH_LOGGING` | bật/tắt ghi log ShopLite vào Elasticsearch |
| `ENABLE_PAYMENT_REGRESSION_BUG` | bật bug thanh toán để demo regression |
| `GEMINI_API_KEY` | tùy chọn, dùng cho phân tích AI; thiếu key thì fallback rule-based |

## Tài liệu chi tiết

- `logitest-ai/README.md`: luồng MVP, API, dashboard và demo defense.
- `logitest-ai/apps/api/README.md`: các endpoint FastAPI và lệnh smoke test.
- `logitest-ai/database/README.md`: migration và kiểm tra bảng PostgreSQL.
- `shoplite/README.md`: user demo, journey demo và regression case.
