const express = require("express");
const { prisma } = require("../../config/prisma");
const { authMiddleware } = require("../../middlewares/authMiddleware");
const { createHttpError } = require("../../middlewares/errorHandler");
const { calculateCart, cartInclude, getOrCreateActiveCart, serializeCart } = require("../cart/service");

const router = express.Router();
router.use(authMiddleware);

router.post("/apply", async (req, res, next) => {
  try {
    const code = String(req.body.code || req.body.voucher_code || "").toUpperCase();
    const voucher = await prisma.voucher.findUnique({ where: { code } });
    if (!voucher || !voucher.isActive) {
      throw createHttpError(404, "VOUCHER_NOT_FOUND", "Voucher not found");
    }

    const cart = await getOrCreateActiveCart(req.user.id);
    const totals = calculateCart({ ...cart, voucher: null });
    if (totals.subtotal_amount < voucher.minimumOrderAmount) {
      throw createHttpError(400, "VOUCHER_MIN_ORDER_NOT_MET", "Minimum order amount is not met");
    }

    const updatedCart = await prisma.cart.update({
      where: { id: cart.id },
      data: { voucherId: voucher.id },
      include: cartInclude()
    });

    res.json({
      voucher_code: voucher.code,
      discount_amount: voucher.discountAmount,
      cart: serializeCart(updatedCart)
    });
  } catch (error) {
    next(error);
  }
});

router.delete("/remove", async (req, res, next) => {
  try {
    const cart = await getOrCreateActiveCart(req.user.id);
    const updatedCart = await prisma.cart.update({
      where: { id: cart.id },
      data: { voucherId: null },
      include: cartInclude()
    });
    res.json(serializeCart(updatedCart));
  } catch (error) {
    next(error);
  }
});

module.exports = router;
