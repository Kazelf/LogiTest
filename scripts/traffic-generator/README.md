# ShopLite synthetic traffic generator

Generates ecommerce traffic by calling the real ShopLite HTTP API. It does not insert logs, write Elasticsearch records, or touch the database directly. ShopLite's existing request logger creates JSONL, PostgreSQL, and optional Elasticsearch logs from these API calls.

## Configure

Set values in the environment or pass CLI flags:

```powershell
$env:BASE_URL="http://localhost:4000"
$env:MODE="demo"
$env:TARGET_LOGS="360"
# Optional override when you want fixed sessions instead of target logs:
# $env:TOTAL_SESSIONS="120"
$env:CONCURRENCY="3"
$env:MIN_DELAY_MS="50"
$env:MAX_DELAY_MS="250"
$env:SEED="demo-traffic"
$env:USER_POOL_SIZE="5"
$env:OUTPUT_SUMMARY_PATH="reports/synthetic-traffic/traffic-summary-demo.json"
```

You can also copy `scripts/traffic-generator/.env.example` to `.env` in the repo root or in `scripts/traffic-generator/`.

Supported keys: `BASE_URL`, `MODE`, `TARGET_LOGS`, `TOTAL_SESSIONS`, `CONCURRENCY`, `MIN_DELAY_MS`, `MAX_DELAY_MS`, `SEED`, `USER_POOL_SIZE`, `OUTPUT_SUMMARY_PATH`.

When `TARGET_LOGS` is set, the generator estimates how many real API requests are needed and runs enough sessions to get close to that number. `TOTAL_SESSIONS` is used only when `TARGET_LOGS` is not set.

## Run

From `shoplite/server`:

```powershell
npm run traffic:smoke
npm run traffic:demo
npm run traffic:load
```

Or from the repo root:

```powershell
node scripts/traffic-generator/index.js --mode demo --base-url http://localhost:4000
```

Modes:

- `smoke`: about 30-50 API requests/logs to check that the API is alive.
- `demo`: about 250-500 API requests/logs across login success, login failed, browse products, search product, view product detail, add to cart, checkout success, checkout failed, and view order status.
- `load`: about 1,000-5,000 API requests/logs for larger reports, with concurrency and delay controls.

## Output

The script prints each API call and writes a JSON summary, by default:

```text
reports/synthetic-traffic/traffic-summary-{timestamp}.json
```

Summary fields include total sessions, total requests, success request counts, expected failed request counts, unexpected failed request counts, journey distribution, average latency, p95 latency, generated session ids, and unexpected API errors.

Intentional failures, such as invalid login and empty-cart checkout, are counted as expected failed requests when the API returns the expected 4xx response.

Current ShopLite checkout falls back to the user's address or `Demo Address`, so the "missing required checkout info" journey is represented by an empty-cart checkout failure (`CART_EMPTY`) unless backend validation changes later.
