const express = require("express");

const { fail, ok } = require("../../shared/response");

function createPaymentsRouter(store) {
  const router = express.Router();

  router.post("/", (req, res) => {
    const { orderId, method = "mock_card" } = req.body || {};
    const order = store.orders[orderId];

    if (!order) {
      res.status(404).json(fail("ORDER_NOT_FOUND", "Order was not found."));
      return;
    }

    const paymentNumber = String(store.counters.payment).padStart(3, "0");
    store.counters.payment += 1;
    const payment = {
      paymentId: `payment-${paymentNumber}`,
      orderId,
      method,
      status: "paid",
      amount: order.total,
      currency: order.currency,
    };

    store.payments[payment.paymentId] = payment;
    order.status = "paid";

    res.status(201).json(ok(payment));
  });

  router.post("/payment-callback", (req, res) => {
    const { paymentId, status = "paid" } = req.body || {};
    const payment = store.payments[paymentId];

    if (!payment) {
      res.status(404).json(fail("PAYMENT_NOT_FOUND", "Payment was not found."));
      return;
    }

    payment.status = status;
    const order = store.orders[payment.orderId];
    if (order) {
      order.status = status === "paid" ? "paid" : "payment_failed";
    }

    res.json(ok(payment));
  });

  return router;
}

module.exports = { createPaymentsRouter };
