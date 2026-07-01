const express = require("express");
const { prisma } = require("../../config/prisma");
const { authMiddleware } = require("../../middlewares/authMiddleware");
const { createHttpError } = require("../../middlewares/errorHandler");
const { cartInclude, getOrCreateActiveCart, requireCartItem, serializeCart } = require("./service");

const router = express.Router();
router.use(authMiddleware);

router.get("/", async (req, res, next) => {
  try {
    const cart = await getOrCreateActiveCart(req.user.id);
    res.json(serializeCart(cart));
  } catch (error) {
    next(error);
  }
});

router.post("/items", async (req, res, next) => {
  try {
    const { product_id, quantity = 1 } = req.body;
    const product = await prisma.product.findUnique({ where: { id: product_id } });
    if (!product) throw createHttpError(404, "PRODUCT_NOT_FOUND", "Product not found");
    if (product.stock < Number(quantity)) {
      throw createHttpError(409, "OUT_OF_STOCK", "Product is out of stock");
    }

    const cart = await getOrCreateActiveCart(req.user.id);
    const item = await prisma.cartItem.upsert({
      where: { cartId_productId: { cartId: cart.id, productId: product.id } },
      create: { cartId: cart.id, productId: product.id, quantity: Number(quantity) },
      update: { quantity: { increment: Number(quantity) } }
    });

    const updatedCart = await prisma.cart.findUnique({ where: { id: cart.id }, include: cartInclude() });
    res.status(201).json({
      cart_item_id: item.id,
      product_id: product.id,
      cart: serializeCart(updatedCart)
    });
  } catch (error) {
    next(error);
  }
});

router.put("/items/:id", async (req, res, next) => {
  try {
    const quantity = Number(req.body.quantity);
    if (!Number.isInteger(quantity) || quantity < 1) {
      throw createHttpError(400, "INVALID_QUANTITY", "Quantity must be greater than zero");
    }
    const item = await requireCartItem(req.user.id, req.params.id);
    if (item.product.stock < quantity) {
      throw createHttpError(409, "OUT_OF_STOCK", "Product is out of stock");
    }

    await prisma.cartItem.update({ where: { id: item.id }, data: { quantity } });
    const cart = await prisma.cart.findUnique({ where: { id: item.cartId }, include: cartInclude() });
    res.json({
      cart_item_id: item.id,
      cart: serializeCart(cart)
    });
  } catch (error) {
    next(error);
  }
});

router.delete("/items/:id", async (req, res, next) => {
  try {
    const item = await requireCartItem(req.user.id, req.params.id);
    await prisma.cartItem.delete({ where: { id: item.id } });
    const cart = await prisma.cart.findUnique({ where: { id: item.cartId }, include: cartInclude() });
    res.json({
      removed_cart_item_id: item.id,
      cart: serializeCart(cart)
    });
  } catch (error) {
    next(error);
  }
});

router.delete("/", async (req, res, next) => {
  try {
    const cart = await getOrCreateActiveCart(req.user.id);
    await prisma.cartItem.deleteMany({ where: { cartId: cart.id } });
    await prisma.cart.update({ where: { id: cart.id }, data: { voucherId: null } });
    res.json({ cart_id: cart.id, items: [] });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
