const { prisma } = require("../src/config/prisma");

afterAll(async () => {
  await prisma.$disconnect();
});
