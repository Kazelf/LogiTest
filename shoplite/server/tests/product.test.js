const fs = require("fs");
const path = require("path");
const { app, productByName, resetDatabase, request } = require("./helpers");
const { demoPassword } = require("../src/prisma/seed");

const logPath = path.join(__dirname, "..", "logs", "request-logs.jsonl");

beforeAll(resetDatabase);

beforeEach(() => {
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
  fs.writeFileSync(logPath, "");
});

test("TC_02 Search product by keyword", async () => {
  const response = await request(app).get("/api/products?keyword=iPhone");

  expect(response.status).toBe(200);
  expect(response.body.products.length).toBeGreaterThan(0);
  expect(response.body.products[0]).toHaveProperty("product_id");
});

test("Product browser can filter by brand and sort ascending", async () => {
  const response = await request(app).get("/api/products?keyword=laptop&brand=Dell&sort=price_asc");

  expect(response.status).toBe(200);
  expect(response.body.products.map((product) => product.brand)).toEqual(["Dell", "Dell"]);
  expect(response.body.products[0].price).toBeLessThanOrEqual(response.body.products[1].price);
});

describe("product discovery request logs", () => {
  test("GET /api/products?keyword=iPhone creates a SEARCH_PRODUCTS log", async () => {
    const response = await request(app)
      .get("/api/products?keyword=iPhone")
      .set("x-session-id", "sess_search_test")
      .set("x-trace-id", "trace_search_test");

    expect(response.status).toBe(200);
    expect(response.headers["x-session-id"]).toBe("sess_search_test");
    expect(response.headers["x-trace-id"]).toBe("trace_search_test");

    const log = await waitForLog((record) => record.action_name === "SEARCH_PRODUCTS");
    expect(log).toEqual(
      expect.objectContaining({
        session_id: "sess_search_test",
        trace_id: "trace_search_test",
        method: "GET",
        endpoint: "/api/products",
        query: { keyword: "iPhone" },
        business_entity: "PRODUCT",
        journey_hint: "PRODUCT_DISCOVERY",
        response_status: 200
      })
    );
    expect(log.response_body_summary).toEqual(
      expect.objectContaining({
        result_count: 2,
        first_result_id: expect.any(String),
        first_result_name: expect.stringContaining("iPhone")
      })
    );
    expect(log.response_body_summary.products).toBeUndefined();
    expect(log.response_body.products).toBeUndefined();
  });

  test("GET /api/products?keyword=laptop&brand=Dell creates a FILTER_PRODUCTS log", async () => {
    const response = await request(app).get("/api/products?keyword=laptop&brand=Dell");

    expect(response.status).toBe(200);

    const log = await waitForLog((record) => record.action_name === "FILTER_PRODUCTS");
    expect(log.endpoint).toBe("/api/products");
    expect(log.query).toEqual({ keyword: "laptop", brand: "Dell" });
    expect(log.business_entity).toBe("PRODUCT");
    expect(log.journey_hint).toBe("PRODUCT_DISCOVERY");
    expect(log.response_body_summary.result_count).toBe(2);
  });

  test("GET /api/products?keyword=laptop&brand=Dell&sort=price_asc creates a SORT_PRODUCTS log", async () => {
    const response = await request(app).get("/api/products?keyword=laptop&brand=Dell&sort=price_asc");

    expect(response.status).toBe(200);

    const log = await waitForLog((record) => record.action_name === "SORT_PRODUCTS");
    expect(log.endpoint).toBe("/api/products");
    expect(log.query).toEqual({ keyword: "laptop", brand: "Dell", sort: "price_asc" });
    expect(log.response_body_summary.result_count).toBe(2);
  });

  test("GET /api/products/:id creates a VIEW_PRODUCT_DETAIL log", async () => {
    const product = await productByName("Dell XPS 13");
    const response = await request(app).get(`/api/products/${product.id}`);

    expect(response.status).toBe(200);

    const log = await waitForLog((record) => record.action_name === "VIEW_PRODUCT_DETAIL");
    expect(log.endpoint).toBe("/api/products/:id");
    expect(log.path_params).toEqual({ id: product.id });
    expect(log.business_entity).toBe("PRODUCT");
    expect(log.business_entity_id).toBe(product.id);
    expect(log.journey_hint).toBe("PRODUCT_DISCOVERY");
    expect(log.response_body_summary).toEqual({
      product_id: product.id,
      product_name: "Dell XPS 13",
      brand: "Dell",
      category: "Laptop",
      price: 28000000,
      stock: 8
    });
  });

  test("generated session and trace ids are returned and logged when headers are absent", async () => {
    const response = await request(app).get("/api/products");

    expect(response.status).toBe(200);
    expect(response.headers["x-session-id"]).toMatch(/^sess_/);
    expect(response.headers["x-trace-id"]).toMatch(/^trace_/);

    const log = await waitForLog((record) => record.action_name === "VIEW_PRODUCTS");
    expect(log.session_id).toBe(response.headers["x-session-id"]);
    expect(log.trace_id).toBe(response.headers["x-trace-id"]);
  });

  test("sensitive request and response fields are masked in logs", async () => {
    const response = await request(app)
      .post("/api/auth/login")
      .send({
        email: "normal_buyer@example.com",
        password: demoPassword,
        token: "raw-token",
        secret: "raw-secret"
      });

    expect(response.status).toBe(200);

    const log = await waitForLog((record) => record.action_name === "LOGIN");
    expect(log.request_body).toEqual(
      expect.objectContaining({
        email: "normal_buyer@example.com",
        password: "***MASKED***",
        token: "***MASKED***",
        secret: "***MASKED***"
      })
    );
    expect(log.response_body_summary.accessToken).toBe("***MASKED***");
  });
});

async function waitForLog(predicate) {
  const deadline = Date.now() + 1000;
  while (Date.now() < deadline) {
    const records = readLogs();
    const match = records.find(predicate);
    if (match) return match;
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  throw new Error(`Timed out waiting for matching log in ${logPath}`);
}

function readLogs() {
  if (!fs.existsSync(logPath)) return [];
  return fs
    .readFileSync(logPath, "utf8")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}
