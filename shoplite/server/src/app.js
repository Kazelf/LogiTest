const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const morgan = require("morgan");
const { env } = require("./config/env");
const { requestLogger } = require("./middlewares/requestLogger");
const { errorHandler, notFoundHandler } = require("./middlewares/errorHandler");

const authRouter = require("./modules/auth/router");
const usersRouter = require("./modules/users/router");
const productsRouter = require("./modules/products/router");
const cartRouter = require("./modules/cart/router");
const vouchersRouter = require("./modules/vouchers/router");
const checkoutRouter = require("./modules/checkout/router");
const ordersRouter = require("./modules/orders/router");
const paymentsRouter = require("./modules/payments/router");
const adminRouter = require("./modules/admin/router");

const app = express();

app.use(helmet());
app.use(cors({ origin: env.clientOrigin, credentials: true }));
app.use(express.json());
app.use(morgan("dev"));
app.use(requestLogger);

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "shoplite-api" });
});

app.use("/api/auth", authRouter);
app.use("/api/users", usersRouter);
app.use("/api/products", productsRouter);
app.use("/api/categories", productsRouter.categoriesRouter);
app.use("/api/cart", cartRouter);
app.use("/api/vouchers", vouchersRouter);
app.use("/api/checkout", checkoutRouter);
app.use("/api/orders", ordersRouter);
app.use("/api/payments", paymentsRouter);
app.use("/api/admin", adminRouter);

app.use(notFoundHandler);
app.use(errorHandler);

module.exports = { app };
