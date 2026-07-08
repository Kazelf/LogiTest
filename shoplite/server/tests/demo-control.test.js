const request = require("supertest");

describe("demo control token", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = {
      ...originalEnv,
      DEMO_CONTROL_TOKEN: "demo-secret"
    };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  test("rejects reset-state without token", async () => {
    const { app } = require("../src/app");

    const response = await request(app).post("/api/demo/reset-state").send({});

    expect(response.status).toBe(401);
  });

  test("rejects regression-toggle with wrong token", async () => {
    const { app } = require("../src/app");

    const response = await request(app)
      .post("/api/demo/regression-toggle")
      .set("x-demo-control-token", "wrong")
      .send({ bug: "missing_order_id", enabled: true });

    expect(response.status).toBe(401);
  });

  test("reset-state clears demo data before reseeding", async () => {
    const resetDemoData = jest.fn().mockResolvedValue();
    jest.doMock("../src/prisma/seed", () => ({ resetDemoData }));
    const { app } = require("../src/app");

    const response = await request(app)
      .post("/api/demo/reset-state")
      .set("x-demo-control-token", "demo-secret")
      .send({});

    expect(response.status).toBe(200);
    expect(resetDemoData).toHaveBeenCalledTimes(1);
  });
});
