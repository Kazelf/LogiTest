const { app, auth, login, productByName, resetDatabase, request } = require("./helpers");

beforeAll(resetDatabase);

test("TC_05 Checkout success", async () => {
  const { token } = await login("voucher_hunter@example.com");
  const product = await productByName("Mechanical Keyboard");
  await request(app).post("/api/cart/items").set(auth(token)).send({ product_id: product.id, quantity: 1 });

  const response = await request(app).post("/api/checkout").set(auth(token)).send({});

  expect(response.status).toBe(200);
  expect(response.body.checkout_ready).toBe(true);
  expect(response.body.total_amount).toBe(1800000);
});

test("TC_08 Apply voucher fails when minimum order not met", async () => {
  const { token } = await login("voucher_hunter@example.com");
  const mouse = await productByName("Logitech Mouse");
  await request(app).delete("/api/cart").set(auth(token));
  await request(app).post("/api/cart/items").set(auth(token)).send({ product_id: mouse.id, quantity: 1 });

  const response = await request(app).post("/api/vouchers/apply").set(auth(token)).send({ code: "SALE50" });

  expect(response.status).toBe(400);
  expect(response.body.error_code).toBe("VOUCHER_MIN_ORDER_NOT_MET");
});

test("TC_09 Apply voucher success when order amount is enough", async () => {
  const { token } = await login("voucher_hunter@example.com");
  const keyboard = await productByName("Mechanical Keyboard");
  await request(app).post("/api/cart/items").set(auth(token)).send({ product_id: keyboard.id, quantity: 1 });

  const response = await request(app).post("/api/vouchers/apply").set(auth(token)).send({ code: "SALE50" });

  expect(response.status).toBe(200);
  expect(response.body.discount_amount).toBe(50000);
});

test("TC_11 Checkout out-of-stock product returns OUT_OF_STOCK", async () => {
  const { token } = await login("error_case_user@example.com");
  const admin = await login("admin@example.com");
  const sneaker = await productByName("Limited Sneaker");
  await request(app).post("/api/cart/items").set(auth(token)).send({ product_id: sneaker.id, quantity: 1 });
  await request(app).post(`/api/admin/products/${sneaker.id}/decrease-stock`).set(auth(admin.token)).send({ quantity: 1 });

  const response = await request(app).post("/api/checkout").set(auth(token)).send({});

  expect(response.status).toBe(409);
  expect(response.body.error_code).toBe("OUT_OF_STOCK");
});
