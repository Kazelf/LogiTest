const { app, auth, login, productByName, resetDatabase, request } = require("./helpers");

beforeEach(resetDatabase);

async function createOrder(email = "normal_buyer@example.com") {
  const { token } = await login(email);
  const product = await productByName("iPhone 15");
  await request(app).delete("/api/cart").set(auth(token));
  await request(app).post("/api/cart/items").set(auth(token)).send({ product_id: product.id, quantity: 1 });
  await request(app).post("/api/checkout").set(auth(token)).send({});
  const order = await request(app).post("/api/orders").set(auth(token)).send({ shipping_address: "Demo Address" });
  return { token, orderId: order.body.order_id, order };
}

test("TC_06 Create order success", async () => {
  const { order } = await createOrder();

  expect(order.status).toBe(201);
  expect(order.body.order_status).toBe("PENDING_PAYMENT");
  expect(order.body.order_id).toBeDefined();
});

test("TC_07 Payment success updates order to PAID", async () => {
  const { token, orderId } = await createOrder();

  const payment = await request(app)
    .post("/api/payments/simulate-success")
    .set(auth(token))
    .send({ order_id: orderId });

  const detail = await request(app).get(`/api/orders/${orderId}`).set(auth(token));

  expect(payment.status).toBe(200);
  expect(payment.body.payment_status).toBe("SUCCESS");
  expect(detail.body.order_status).toBe("PAID");
  expect(detail.body.payment_status).toBe("SUCCESS");
});

const regressionTest = process.env.ENABLE_PAYMENT_REGRESSION_BUG === "true" ? test : test.skip;

regressionTest("TC_12 Regression: payment success but order remains PENDING_PAYMENT should fail", async () => {
  const { token, orderId } = await createOrder();

  await request(app)
    .post("/api/payments/simulate-success")
    .set(auth(token))
    .send({ order_id: orderId });

  const detail = await request(app).get(`/api/orders/${orderId}`).set(auth(token));

  expect(detail.body.payment_status).toBe("SUCCESS");
  expect(detail.body.order_status).toBe("PAID");
});
