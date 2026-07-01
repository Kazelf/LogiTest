const request = require("supertest");
const { app } = require("../src/app");
const { prisma } = require("../src/config/prisma");
const { seedDatabase, demoPassword } = require("../src/prisma/seed");

async function resetDatabase() {
  await prisma.requestLog.deleteMany();
  await prisma.inventoryTransaction.deleteMany();
  await prisma.payment.deleteMany();
  await prisma.orderItem.deleteMany();
  await prisma.order.deleteMany();
  await prisma.cartItem.deleteMany();
  await prisma.cart.deleteMany();
  await prisma.product.deleteMany();
  await prisma.category.deleteMany();
  await prisma.voucher.deleteMany();
  await prisma.user.deleteMany();
  await seedDatabase();
}

async function login(email = "normal_buyer@example.com") {
  const response = await request(app)
    .post("/api/auth/login")
    .set("x-session-id", `sess_test_${Date.now()}`)
    .send({ email, password: demoPassword });

  return {
    token: response.body.accessToken,
    user: response.body.user
  };
}

async function productByName(name) {
  return prisma.product.findUnique({ where: { name } });
}

function auth(token) {
  return { Authorization: `Bearer ${token}`, "x-session-id": "sess_test_suite" };
}

module.exports = { app, auth, login, productByName, resetDatabase, request, prisma };
