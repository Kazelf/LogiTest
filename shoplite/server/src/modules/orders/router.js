const express = require("express");
const { prisma } = require("../../config/prisma");
const { authMiddleware } = require("../../middlewares/authMiddleware");
const { createHttpError } = require("../../middlewares/errorHandler");
const { calculateCart, getOrCreateActiveCart } = require("../cart/service");

const router = express.Router();
router.use(authMiddleware);

function serializeOrder(order) {
  return {
    order_id: order.id,
    order_status: order.status,
    payment_status: order.payment?.status || null,
    subtotal_amount: order.subtotalAmount,
    discount_amount: order.discountAmount,
    total_amount: order.totalAmount,
    voucher_code: order.voucher?.code || null,
    shipping_address: order.shippingAddress,
    items: order.items.map((item) => ({
      order_item_id: item.id,
      product_id: item.productId,
      name: item.product.name,
      quantity: item.quantity,
      unit_price: item.unitPrice,
      line_total: item.lineTotal
    })),
    created_at: order.createdAt
  };
}

const orderInclude = {
  voucher: true,
  payment: true,
  items: { include: { product: true } }
};

router.post("/", async (req, res, next) => {
  try {
    const cart = await getOrCreateActiveCart(req.user.id);
    if (cart.items.length === 0) throw createHttpError(400, "CART_EMPTY", "Cart is empty");

    const outOfStock = cart.items.find((item) => item.product.stock < item.quantity);
    if (outOfStock) {
      throw createHttpError(409, "OUT_OF_STOCK", "Product is out of stock", {
        product_id: outOfStock.productId
      });
    }

    const totals = calculateCart(cart);
    const order = await prisma.$transaction(async (tx) => {
      const createdOrder = await tx.order.create({
        data: {
          userId: req.user.id,
          voucherId: cart.voucherId,
          subtotalAmount: totals.subtotal_amount,
          discountAmount: totals.discount_amount,
          totalAmount: totals.total_amount,
          shippingAddress: req.body.shipping_address || req.user.address || "Demo Address",
          items: {
            create: cart.items.map((item) => ({
              productId: item.productId,
              quantity: item.quantity,
              unitPrice: item.product.price,
              lineTotal: item.product.price * item.quantity
            }))
          },
          payment: {
            create: {
              amount: totals.total_amount,
              status: "PENDING"
            }
          }
        }
      });

      for (const item of cart.items) {
        await tx.product.update({
          where: { id: item.productId },
          data: { stock: { decrement: item.quantity } }
        });
        await tx.inventoryTransaction.create({
          data: {
            productId: item.productId,
            type: "SALE",
            quantity: item.quantity,
            reason: `Order ${createdOrder.id}`
          }
        });
      }

      await tx.cartItem.deleteMany({ where: { cartId: cart.id } });
      await tx.cart.update({ where: { id: cart.id }, data: { voucherId: null } });
      return tx.order.findUnique({ where: { id: createdOrder.id }, include: orderInclude });
    });

    res.status(201).json(serializeOrder(order));
  } catch (error) {
    next(error);
  }
});

router.get("/", async (req, res, next) => {
  try {
    const orders = await prisma.order.findMany({
      where: { userId: req.user.id },
      include: orderInclude,
      orderBy: { createdAt: "desc" }
    });
    res.json({ orders: orders.map(serializeOrder) });
  } catch (error) {
    next(error);
  }
});

router.get("/:id", async (req, res, next) => {
  try {
    const order = await prisma.order.findFirst({
      where: { id: req.params.id, userId: req.user.id },
      include: orderInclude
    });
    if (!order) throw createHttpError(404, "ORDER_NOT_FOUND", "Order not found");
    res.json(serializeOrder(order));
  } catch (error) {
    next(error);
  }
});

router.post("/:id/cancel", async (req, res, next) => {
  try {
    const order = await prisma.order.findFirst({ where: { id: req.params.id, userId: req.user.id } });
    if (!order) throw createHttpError(404, "ORDER_NOT_FOUND", "Order not found");
    if (order.status === "PAID") throw createHttpError(409, "ORDER_ALREADY_PAID", "Paid order cannot be cancelled");

    const updated = await prisma.order.update({
      where: { id: order.id },
      data: { status: "CANCELLED" },
      include: orderInclude
    });
    res.json(serializeOrder(updated));
  } catch (error) {
    next(error);
  }
});

module.exports = router;
