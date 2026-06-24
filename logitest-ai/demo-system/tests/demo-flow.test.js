const assert = require("node:assert/strict");
const test = require("node:test");
const request = require("supertest");

const { createApp } = require("../src/app");

const headers = {
  "x-session-id": "session-demo-test",
  "x-trace-id": "trace-demo-test",
  "x-request-id": "req-demo-test",
  "x-user-id": "user-buyer-001",
};

test("health endpoint returns demo backend status", async () => {
  const app = createApp();

  const response = await request(app).get("/health").expect(200);

  assert.equal(response.body.success, true);
  assert.equal(response.body.data.service, "demo-ecommerce");
});

test("login, search, cart, order, and order detail flow is repeatable", async () => {
  const app = createApp();

  const login = await request(app)
    .post("/api/auth/login")
    .set(headers)
    .send({ username: "buyer_001", password: "password123" })
    .expect(200);
  assert.equal(login.body.data.userId, "user-buyer-001");
  assert.equal(login.body.data.token, "demo-token-user-buyer-001");

  const search = await request(app)
    .get("/api/products?keyword=headphones")
    .set(headers)
    .expect(200);
  assert.equal(search.body.data.total, 1);
  const productId = search.body.data.items[0].id;

  await request(app)
    .post("/api/cart/items")
    .set(headers)
    .send({ productId, quantity: 1 })
    .expect(201);

  const cart = await request(app).get("/api/cart").set(headers).expect(200);
  assert.equal(cart.body.data.total, 1290000);

  const order = await request(app).post("/api/orders").set(headers).send({}).expect(201);
  const orderId = order.body.data.orderId;
  assert.equal(orderId, "order-001");
  assert.equal(order.body.data.status, "created");

  const detail = await request(app).get(`/api/orders/${orderId}`).set(headers).expect(200);
  assert.equal(detail.body.data.orderId, orderId);
  assert.equal(detail.body.data.status, "created");
});

test("regression mode changes order detail business status", async () => {
  const app = createApp({ regressionMode: true });

  await request(app)
    .post("/api/cart/items")
    .set(headers)
    .send({ productId: "prod-headphone-001", quantity: 1 })
    .expect(201);

  const order = await request(app).post("/api/orders").set(headers).send({}).expect(201);
  assert.equal(order.body.data.status, "created");

  const detail = await request(app)
    .get(`/api/orders/${order.body.data.orderId}`)
    .set(headers)
    .expect(200);

  assert.equal(detail.body.data.status, "pending");
});
