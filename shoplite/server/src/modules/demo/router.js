const express = require("express");
const { env } = require("../../config/env");
const { demoRegression, setDemoRegressionBug } = require("../../config/demoRegression");
const { createHttpError } = require("../../middlewares/errorHandler");
const { resetDemoData } = require("../../prisma/seed");

const router = express.Router();

function requireDemoControl(req, _res, next) {
  if (!env.demoControlToken || req.headers["x-demo-control-token"] === env.demoControlToken) {
    return next();
  }
  return next(createHttpError(401, "UNAUTHORIZED_DEMO_CONTROL", "Demo control token is required."));
}

router.use(requireDemoControl);

router.post("/regression-toggle", (req, res, next) => {
  try {
    const { bug, enabled } = req.body || {};
    if (!setDemoRegressionBug(bug, enabled)) {
      throw createHttpError(400, "UNKNOWN_DEMO_BUG", "Supported demo bugs: missing_order_id, payment_success_order_not_paid");
    }
    res.json({ demo_only: true, bug, enabled: Boolean(enabled), state: demoRegression });
  } catch (error) {
    next(error);
  }
});

router.get("/regression-toggle", (req, res) => {
  res.json({ demo_only: true, state: demoRegression });
});

router.post("/reset-state", async (req, res, next) => {
  try {
    await resetDemoData();
    res.json({ demo_only: true, reset: true });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
