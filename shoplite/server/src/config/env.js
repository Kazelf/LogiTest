require("dotenv").config();

const env = {
  port: Number(process.env.PORT || 4000),
  jwtSecret: process.env.JWT_SECRET || "shoplite-dev-secret",
  clientOrigin: process.env.CLIENT_ORIGIN || "http://localhost:5173",
  environment: process.env.ENVIRONMENT || "production-demo",
  paymentRegressionBug: String(process.env.ENABLE_PAYMENT_REGRESSION_BUG || "false") === "true"
};

module.exports = { env };
