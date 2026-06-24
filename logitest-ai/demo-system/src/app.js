const express = require("express");

const { createAuthRouter } = require("./modules/auth/router");
const { createCartRouter } = require("./modules/cart/router");
const { createOrdersRouter } = require("./modules/orders/router");
const { createPaymentsRouter } = require("./modules/payments/router");
const { createProductsRouter } = require("./modules/products/router");
const { requestContext } = require("./middlewares/request-context.middleware");
const { loggingMiddleware } = require("./middlewares/logging.middleware");
const { createStore } = require("./data/seed");
const { ok } = require("./shared/response");

function createApp(options = {}) {
  const app = express();
  const store = options.store || createStore();
  const regressionMode = options.regressionMode ?? process.env.REGRESSION_MODE === "true";

  app.locals.store = store;
  app.locals.regressionMode = regressionMode;

  app.use(express.json());
  app.use(requestContext());
  app.use(loggingMiddleware());

  app.get("/health", (req, res) => {
    res.json(ok({ service: "demo-ecommerce", regressionMode }));
  });

  app.use("/api/auth", createAuthRouter(store));
  app.use("/api/products", createProductsRouter(store));
  app.use("/api/cart", createCartRouter(store));
  app.use("/api/orders", createOrdersRouter(store, { regressionMode }));
  app.use("/api/payments", createPaymentsRouter(store));

  app.use((req, res) => {
    res.status(404).json({
      success: false,
      error: {
        code: "NOT_FOUND",
        message: `Route ${req.method} ${req.path} was not found.`,
      },
    });
  });

  app.use((err, req, res, next) => {
    if (res.headersSent) {
      next(err);
      return;
    }

    res.status(err.statusCode || 500).json({
      success: false,
      error: {
        code: err.code || "INTERNAL_ERROR",
        message: err.message || "Unexpected demo backend error.",
      },
    });
  });

  return app;
}

module.exports = { createApp };
