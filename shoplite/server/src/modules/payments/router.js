const express = require("express");
const { prisma } = require("../../config/prisma");
const { env } = require("../../config/env");
const { authMiddleware } = require("../../middlewares/authMiddleware");
const { createHttpError } = require("../../middlewares/errorHandler");

const router = express.Router();
router.use(authMiddleware);

async function requireOwnedOrder(userId, orderId) {
  const order = await prisma.order.findFirst({
    where: { id: orderId, userId },
    include: { payment: true }
  });
  if (!order) throw createHttpError(404, "ORDER_NOT_FOUND", "Order not found");
  return order;
}

router.post("/simulate-success", async (req, res, next) => {
  try {
    const orderId = req.body.order_id;
    const order = await requireOwnedOrder(req.user.id, orderId);
    const payment = await prisma.payment.update({
      where: { orderId: order.id },
      data: { status: "SUCCESS" }
    });

    if (!env.paymentRegressionBug) {
      await prisma.order.update({
        where: { id: order.id },
        data: { status: "PAID" }
      });
    }

    const updatedOrder = await prisma.order.findUnique({
      where: { id: order.id },
      include: { payment: true }
    });

    res.json({
      payment_id: payment.id,
      order_id: order.id,
      payment_status: payment.status,
      order_status: updatedOrder.status
    });
  } catch (error) {
    next(error);
  }
});

router.post("/simulate-failed", async (req, res, next) => {
  try {
    const order = await requireOwnedOrder(req.user.id, req.body.order_id);
    const payment = await prisma.payment.update({
      where: { orderId: order.id },
      data: { status: "FAILED" }
    });
    await prisma.order.update({ where: { id: order.id }, data: { status: "FAILED" } });
    res.json({
      payment_id: payment.id,
      order_id: order.id,
      payment_status: "FAILED",
      order_status: "FAILED"
    });
  } catch (error) {
    next(error);
  }
});

router.post("/webhook", async (req, res, next) => {
  try {
    const { order_id, payment_status } = req.body;
    const order = await requireOwnedOrder(req.user.id, order_id);
    if (payment_status === "SUCCESS") {
      const payment = await prisma.payment.update({
        where: { orderId: order.id },
        data: { status: "SUCCESS" }
      });
      if (!env.paymentRegressionBug) {
        await prisma.order.update({ where: { id: order.id }, data: { status: "PAID" } });
      }
      const updatedOrder = await prisma.order.findUnique({ where: { id: order.id }, include: { payment: true } });
      res.json({
        payment_id: payment.id,
        order_id,
        payment_status: "SUCCESS",
        order_status: updatedOrder.status
      });
      return;
    }
    await prisma.payment.update({ where: { orderId: order.id }, data: { status: "FAILED" } });
    await prisma.order.update({ where: { id: order.id }, data: { status: "FAILED" } });
    res.json({ order_id, payment_status: "FAILED", order_status: "FAILED" });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
