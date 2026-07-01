require("dotenv").config();

const env = {
  port: Number(process.env.PORT || 4000),
  jwtSecret: process.env.JWT_SECRET || "shoplite-dev-secret",
  clientOrigin: process.env.CLIENT_ORIGIN || "http://localhost:5173",
  environment: process.env.ENVIRONMENT || "production-demo",
  paymentRegressionBug: String(process.env.ENABLE_PAYMENT_REGRESSION_BUG || "false") === "true",
  elasticsearchLogging: String(process.env.ENABLE_ELASTICSEARCH_LOGGING || "false") === "true",
  elasticsearchUrl: process.env.ELASTICSEARCH_URL || "",
  shopliteLogIndex: process.env.SHOPLITE_LOG_INDEX || "logitest-demo-logs"
};

module.exports = { env };
