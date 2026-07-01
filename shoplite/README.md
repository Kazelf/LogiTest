# ShopLite

ShopLite is a mini e-commerce System Under Test for the LogiTest AI-Driven Behavioral Testing Platform. It creates production-like API traffic and JSONL request logs for normal, abnormal, business-error, edge-case, and regression journeys.

## Stack

- Frontend: React + Vite
- Backend: Node.js + Express.js
- Database: PostgreSQL + Prisma
- Logs: `server/logs/request-logs.jsonl`
- Tests: Jest + Supertest

## 1. Run With Docker

```bash
cd shoplite
docker compose up --build
```

URLs:

- Frontend: `http://localhost:5173`
- API: `http://localhost:4000`
- PostgreSQL: `localhost:5433`

The server container runs Prisma migrations and seeds demo data before starting.

### Enable Elasticsearch Logging With Docker

If LogiTest AI's Elasticsearch is running at `http://localhost:9200`, create or edit `shoplite/.env`:

```env
ENABLE_ELASTICSEARCH_LOGGING=true
ELASTICSEARCH_URL=http://host.docker.internal:9200
SHOPLITE_LOG_INDEX=logitest-demo-logs
```

Then restart ShopLite:

```bash
docker compose up --build
```

Use `http://host.docker.internal:9200` inside Docker because the ShopLite server container reaches Elasticsearch through the host-published port.

## 2. Install Dependencies Manually

```bash
cd shoplite/server
npm install

cd ../client
npm install
```

## 3. Run Database Only

```bash
cd shoplite
docker compose up -d
```

PostgreSQL runs on `localhost:5433`.

## 4. Configure Environment

```bash
cd shoplite/server
cp .env.example .env

cd ../client
cp .env.example .env
```

For manual non-Docker backend runs, enable Elasticsearch in `shoplite/server/.env`:

```env
ENABLE_ELASTICSEARCH_LOGGING=true
ELASTICSEARCH_URL=http://localhost:9200
SHOPLITE_LOG_INDEX=logitest-demo-logs
```

## 5. Run Migration

```bash
cd shoplite/server
npm run prisma:generate
npm run prisma:migrate
```

## 6. Seed Demo Data

```bash
cd shoplite/server
npm run seed
```

Demo users all use password `Password123`:

- `normal_buyer@example.com`
- `browser_user@example.com`
- `hesitant_buyer@example.com`
- `voucher_hunter@example.com`
- `error_case_user@example.com`
- `admin@example.com`

## 7. Run Backend

```bash
cd shoplite/server
npm run dev
```

API base URL: `http://localhost:4000`

## 8. Run Frontend

```bash
cd shoplite/client
npm run dev
```

Frontend URL: `http://localhost:5173`

## 9. Run Tests

Make sure the database is running and migrated first.

```bash
cd shoplite/server
npm test
```

To intentionally demonstrate the payment regression, run:

```bash
cd shoplite/server
npm run test:regression
```

With `ENABLE_PAYMENT_REGRESSION_BUG=true`, payment simulation returns `payment_status = SUCCESS`, but the order remains `PENDING_PAYMENT`. The regression test expects the correct behavior (`PAID`), so it fails by design and demonstrates the high-severity paid-but-not-confirmed bug.

## 10. Enable Regression Bug Manually

Set this in `shoplite/server/.env`:

```env
ENABLE_PAYMENT_REGRESSION_BUG=true
```

Then restart the backend.

## 11. View Logs

Every API request is appended as one JSON object per line:

```text
shoplite/server/logs/request-logs.jsonl
```

If `ENABLE_ELASTICSEARCH_LOGGING=true`, the same request log is also indexed into Elasticsearch.

Each log includes:

- `session_id`
- `trace_id`
- `user_id`
- `method`
- `endpoint`
- `request_body`
- `response_status`
- `response_body`
- `response_time_ms`
- `error_code`
- `action_name`
- `business_entity`
- `business_entity_id`
- `journey_hint`
- `previous_step`
- `next_expected_step`

Sensitive fields such as `password`, `accessToken`, `refreshToken`, `authorization`, and `token` are masked.

## Demo Journeys

### Journey 1: Normal Buyer

Login as `normal_buyer@example.com`, search `iPhone`, view detail, add to cart, update quantity, checkout, create order, simulate payment success, then view order detail. Expected final state: `order_status = PAID`, `payment_status = SUCCESS`.

### Journey 2: Product Browser

Use `browser_user@example.com`, open product list, search `laptop`, filter brand `Dell`, sort `price_asc`, view product detail, and stop before checkout.

### Journey 3: Returning Buyer

Use `normal_buyer@example.com`, open cart seeded with products, remove one item, apply `SALE50`, checkout, pay, then view order history.

### Journey 4: Hesitant Buyer

Use `hesitant_buyer@example.com`, search, add multiple products, update quantities repeatedly, remove items, clear the cart, then checkout. Expected error: `CART_EMPTY`.

### Journey 5: Voucher Hunter

Use `voucher_hunter@example.com`, add `Logitech Mouse`, apply `SALE50` and receive `VOUCHER_MIN_ORDER_NOT_MET`; add `Mechanical Keyboard`, apply `SALE50` again, and checkout successfully.

### Journey 6: Out of Stock Edge Case

Use `error_case_user@example.com`, add `Limited Sneaker` to cart, then call:

```http
POST /api/admin/products/:productId/decrease-stock
```

After stock reaches zero, checkout returns `OUT_OF_STOCK`.

### Journey 7: Payment Regression

Enable `ENABLE_PAYMENT_REGRESSION_BUG=true`, create an order, simulate payment success, then view order detail. Actual bug state: `payment_status = SUCCESS`, `order_status = PENDING_PAYMENT`.
