const { app, resetDatabase, request } = require("./helpers");

beforeAll(resetDatabase);

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
