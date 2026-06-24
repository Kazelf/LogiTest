const express = require("express");

const { getOrCreateCart, toCartResponse } = require("../cart/router");
const { fail, ok } = require("../../shared/response");

const DEFAULT_USER_ID = "user-buyer-001";

function createOrdersRouter(store, options = {}) {
  const router = express.Router();
  const regressionMode = Boolean(options.regressionMode);

  router.post("/", (req, res) => {
    const userId = req.header("x-user-id") || DEFAULT_USER_ID;
    const cart = getOrCreateCart(store, userId);
    const cartResponse = toCartResponse(store, cart);

    if (cartResponse.items.length === 0) {
      res.status(422).json(fail("EMPTY_CART", "Cannot create an order from an empty cart."));
      return;
    }

    const orderNumber = String(store.counters.order).padStart(3, "0");
    store.counters.order += 1;
    const orderId = `order-${orderNumber}`;
    const order = {
      orderId,
      userId,
      cartId: cart.id,
      status: "created",
      items: cartResponse.items,
      total: cartResponse.total,
      currency: "VND",
    };

    store.orders[orderId] = order;
    cart.items = [];

    res.status(201).json(ok(order));
  });

  router.get("/:orderId", (req, res) => {
    const order = store.orders[req.params.orderId];
    if (!order) {
      res.status(404).json(fail("ORDER_NOT_FOUND", "Order was not found."));
      return;
    }

    const response = regressionMode
      ? {
          ...order,
          status: "pending",
        }
      : order;

    res.json(ok(response));
  });

  return router;
}

module.exports = { createOrdersRouter };
