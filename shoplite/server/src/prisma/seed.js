const bcrypt = require("bcryptjs");
const { prisma } = require("../config/prisma");

const demoPassword = "Password123";

const users = [
  ["normal_buyer@example.com", "Normal Buyer", "BUYER", "123 Demo Street"],
  ["browser_user@example.com", "Product Browser", "BUYER", "456 Browse Avenue"],
  ["hesitant_buyer@example.com", "Hesitant Buyer", "BUYER", "789 Maybe Road"],
  ["voucher_hunter@example.com", "Voucher Hunter", "BUYER", "10 Discount Lane"],
  ["error_case_user@example.com", "Error Case User", "BUYER", "404 Edge Street"],
  ["admin@example.com", "ShopLite Admin", "ADMIN", "1 Admin Plaza"]
];

const products = [
  ["iPhone 15", "Apple", "Phone", 25000000, 10, "Apple iPhone 15 demo product"],
  ["iPhone 15 Pro", "Apple", "Phone", 32000000, 5, "Apple iPhone 15 Pro demo product"],
  ["Dell XPS 13", "Dell", "Laptop", 28000000, 8, "Compact Dell premium laptop"],
  ["Dell Inspiron 15", "Dell", "Laptop", 15000000, 12, "Dell everyday work laptop"],
  ["Logitech Mouse", "Logitech", "Accessories", 200000, 20, "Wireless Logitech mouse"],
  ["Mechanical Keyboard", "Keychron", "Accessories", 1800000, 6, "Keychron mechanical keyboard"],
  ["Limited Sneaker", "Nike", "Fashion", 3000000, 1, "Limited stock Nike sneaker"]
];

async function seedDatabase() {
  const passwordHash = await bcrypt.hash(demoPassword, 10);

  for (const [, , category] of products) {
    await prisma.category.upsert({
      where: { name: category },
      update: {},
      create: { name: category }
    });
  }

  for (const [email, name, role, address] of users) {
    await prisma.user.upsert({
      where: { email },
      update: { name, role, address, passwordHash },
      create: { email, name, role, address, passwordHash }
    });
  }

  for (const [name, brand, category, price, stock, description] of products) {
    const categoryRecord = await prisma.category.findUnique({ where: { name: category } });
    await prisma.product.upsert({
      where: { name },
      update: {
        brand,
        price,
        stock,
        description,
        categoryId: categoryRecord.id,
        imageUrl: `/products/${name.toLowerCase().replaceAll(" ", "-")}.jpg`
      },
      create: {
        name,
        brand,
        price,
        stock,
        description,
        categoryId: categoryRecord.id,
        imageUrl: `/products/${name.toLowerCase().replaceAll(" ", "-")}.jpg`
      }
    });
  }

  await prisma.voucher.upsert({
    where: { code: "SALE50" },
    update: { discountAmount: 50000, minimumOrderAmount: 500000, isActive: true },
    create: {
      code: "SALE50",
      discountAmount: 50000,
      minimumOrderAmount: 500000,
      isActive: true
    }
  });

  const normalBuyer = await prisma.user.findUnique({ where: { email: "normal_buyer@example.com" } });
  const mouse = await prisma.product.findUnique({ where: { name: "Logitech Mouse" } });
  const keyboard = await prisma.product.findUnique({ where: { name: "Mechanical Keyboard" } });
  const cart = await prisma.cart.upsert({
    where: { id: "seed_normal_buyer_cart" },
    update: { userId: normalBuyer.id, status: "ACTIVE" },
    create: { id: "seed_normal_buyer_cart", userId: normalBuyer.id, status: "ACTIVE" }
  });
  await prisma.cartItem.upsert({
    where: { cartId_productId: { cartId: cart.id, productId: mouse.id } },
    update: { quantity: 1 },
    create: { cartId: cart.id, productId: mouse.id, quantity: 1 }
  });
  await prisma.cartItem.upsert({
    where: { cartId_productId: { cartId: cart.id, productId: keyboard.id } },
    update: { quantity: 1 },
    create: { cartId: cart.id, productId: keyboard.id, quantity: 1 }
  });

  console.log("ShopLite seed data created.");
}

if (require.main === module) {
  seedDatabase()
    .catch((error) => {
      console.error(error);
      process.exit(1);
    })
    .finally(async () => {
      await prisma.$disconnect();
    });
}

module.exports = { seedDatabase, demoPassword };
