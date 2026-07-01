const { prisma } = require("../../config/prisma");
const { createHttpError } = require("../../middlewares/errorHandler");

async function getOrCreateActiveCart(userId) {
  const existing = await prisma.cart.findFirst({
    where: { userId, status: "ACTIVE" },
    include: cartInclude()
  });
  if (existing) return existing;

  return prisma.cart.create({
    data: { userId },
    include: cartInclude()
  });
}

function cartInclude() {
  return {
    voucher: true,
    items: {
      include: {
        product: {
          include: { category: true }
        }
      },
      orderBy: { createdAt: "asc" }
    }
  };
}

function calculateCart(cart) {
  const subtotal_amount = cart.items.reduce((total, item) => total + item.product.price * item.quantity, 0);
  const discount_amount = cart.voucher ? cart.voucher.discountAmount : 0;
  return {
    subtotal_amount,
    discount_amount,
    total_amount: Math.max(subtotal_amount - discount_amount, 0)
  };
}

function serializeCart(cart) {
  const totals = calculateCart(cart);
  return {
    cart_id: cart.id,
    user_id: cart.userId,
    voucher_code: cart.voucher?.code || null,
    items: cart.items.map((item) => ({
      cart_item_id: item.id,
      product_id: item.productId,
      name: item.product.name,
      brand: item.product.brand,
      price: item.product.price,
      stock: item.product.stock,
      quantity: item.quantity,
      line_total: item.product.price * item.quantity
    })),
    ...totals
  };
}

async function requireCartItem(userId, itemId) {
  const item = await prisma.cartItem.findFirst({
    where: {
      id: itemId,
      cart: { userId, status: "ACTIVE" }
    },
    include: { cart: true, product: true }
  });
  if (!item) throw createHttpError(404, "CART_ITEM_NOT_FOUND", "Cart item not found");
  return item;
}

module.exports = { calculateCart, cartInclude, getOrCreateActiveCart, requireCartItem, serializeCart };
