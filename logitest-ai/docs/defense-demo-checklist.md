# Defense Demo Checklist

## Start

From the repository root:

```powershell
docker compose up --build
```

Optional Gemini explanation mode:

```powershell
$env:GEMINI_API_KEY="your-key"
$env:AI_PROVIDER="gemini"
$env:GEMINI_MODEL="gemini-1.5-flash"
$env:AI_FALLBACK_RULE_BASED="true"
docker compose up --build
```

Open:

- LogiTest dashboard: http://localhost:3000
- LogiTest API health: http://localhost:8000/health
- ShopLite UI: http://localhost:5173
- ShopLite API health: http://localhost:4000/health

## Click Path

1. In LogiTest, click `Import ES New`. If Elasticsearch has no logs, click `Import Mock`.
2. Click `Analyze`.
3. Open `Journeys`, select the checkout/order journey.
4. Show `Behavior explanation`: behavior name, type, user goal, steps, payload fields, response fields, and chaining.
5. Click `Generate Jest`.
6. Open `Test Cases`, select the generated checkout test.
7. Click `Run Test`; it should pass with the bug disabled.
8. Enable the demo regression:

```powershell
curl -X POST http://localhost:4000/api/demo/regression-toggle `
  -H "content-type: application/json" `
  -d "{\"bug\":\"missing_order_id\",\"enabled\":true}"
```

9. Click `Run Test` again.
10. Open `Report` and show status, diff path, expected value, actual value, severity, and ignored dynamic fields.
11. Disable the bug after the demo:

```powershell
curl -X POST http://localhost:4000/api/demo/regression-toggle `
  -H "content-type: application/json" `
  -d "{\"bug\":\"missing_order_id\",\"enabled\":false}"
```

## What To Say

- Gemini-style explanation is for human understanding only.
- Pass/fail is deterministic: status code, schema, business field, response time, chaining, and unexpected errors.
- Dynamic fields like `order_id`, `traceId`, `createdAt`, and tokens are ignored for value comparison but still visible in the report.
- The checkout chain proves `POST /api/orders` output becomes the `GET /api/orders/{order_id}` input.
- The demo bug removes `order_id`, so the same test fails with a schema/chaining diff.

## Fallbacks

- No Elasticsearch logs: use `Import Mock`, then `Analyze`.
- No Gemini API key: the app uses deterministic endpoint-pattern explanations, so the demo still works and Journey Detail shows `rule_based / fallback`.
