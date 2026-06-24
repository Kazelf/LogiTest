const express = require("express");

const { fail, ok } = require("../../shared/response");

const DEFAULT_USER_ID = "user-buyer-001";

function createCartRouter(store) {
  const router = express.Router();

  router.get("/", (req, res) => {
    const userId = req.header("x-user-id") || DEFAULT_USER_ID;
    const cart = getOrCreateCart(store, userId);
    res.json(ok(toCartResponse(store, cart)));
  });

  router.post("/items", (req, res) => {
    const userId = req.header("x-user-id") || DEFAULT_USER_ID;
    const { productId, product_id: productIdSnake, quantity = 1 } = req.body || {};
    const selectedProductId = productId || productIdSnake;
    const product = store.products.find((candidate) => candidate.id === selectedProductId);

    if (!product) {
      res.status(404).json(fail("PRODUCT_NOT_FOUND", "Product was not found."));
      return;
    }

    const cart = getOrCreateCart(store, userId);
    const existing = cart.items.find((item) => item.productId === product.id);
    if (existing) {
      existing.quantity += Number(quantity);
    } else {
      cart.items.push({ productId: product.id, quantity: Number(quantity) });
    }

    res.status(201).json(ok(toCartResponse(store, cart)));
  });

  return router;
}

function getOrCreateCart(store, userId) {
  if (!store.carts[userId]) {
    store.carts[userId] = {
      id: `cart-${userId}`,
      userId,
      items: [],
    };
  }
  return store.carts[userId];
}

function toCartResponse(store, cart) {
  const items = cart.items.map((item) => {
    const product = store.products.find((candidate) => candidate.id === item.productId);
    return {
      productId: item.productId,
      name: product?.name || "Unknown product",
      price: product?.price || 0,
      quantity: item.quantity,
      lineTotal: (product?.price || 0) * item.quantity,
    };
  });

  return {
    cartId: cart.id,
    userId: cart.userId,
    items,
    total: items.reduce((sum, item) => sum + item.lineTotal, 0),
  };
}

module.exports = { createCartRouter, getOrCreateCart, toCartResponse };
