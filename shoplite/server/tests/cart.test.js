const { app, auth, login, productByName, resetDatabase, request } = require("./helpers");

beforeAll(resetDatabase);

test("TC_03 Add product to cart", async () => {
  const { token } = await login("hesitant_buyer@example.com");
  const product = await productByName("iPhone 15");
  const response = await request(app)
    .post("/api/cart/items")
    .set(auth(token))
    .send({ product_id: product.id, quantity: 1 });

  expect(response.status).toBe(201);
  expect(response.body.cart_item_id).toBeDefined();
  expect(response.body.cart.items[0].product_id).toBe(product.id);
});

test("TC_04 Update cart item quantity", async () => {
  const { token } = await login("hesitant_buyer@example.com");
  const product = await productByName("iPhone 15 Pro");
  const added = await request(app).post("/api/cart/items").set(auth(token)).send({ product_id: product.id, quantity: 1 });

  const response = await request(app)
    .put(`/api/cart/items/${added.body.cart_item_id}`)
    .set(auth(token))
    .send({ quantity: 2 });

  expect(response.status).toBe(200);
  expect(response.body.cart.items.find((item) => item.cart_item_id === added.body.cart_item_id).quantity).toBe(2);
});

test("TC_10 Checkout empty cart returns CART_EMPTY", async () => {
  const { token } = await login("browser_user@example.com");
  await request(app).delete("/api/cart").set(auth(token));
  const response = await request(app).post("/api/checkout").set(auth(token)).send({});

  expect(response.status).toBe(400);
  expect(response.body.error_code).toBe("CART_EMPTY");
});
