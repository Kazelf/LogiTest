const { app, login, resetDatabase, request } = require("./helpers");

beforeAll(resetDatabase);

test("TC_01 Login success", async () => {
  const response = await request(app)
    .post("/api/auth/login")
    .send({ email: "normal_buyer@example.com", password: "Password123" });

  expect(response.status).toBe(200);
  expect(response.body.user.email).toBe("normal_buyer@example.com");
  expect(response.body.accessToken).toBeDefined();
});

test("GET /api/users/me returns the current user", async () => {
  const { token } = await login();
  const response = await request(app).get("/api/users/me").set("Authorization", `Bearer ${token}`);

  expect(response.status).toBe(200);
  expect(response.body.email).toBe("normal_buyer@example.com");
});
