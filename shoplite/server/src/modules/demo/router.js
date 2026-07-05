const express = require("express");
const { demoRegression, setDemoRegressionBug } = require("../../config/demoRegression");
const { createHttpError } = require("../../middlewares/errorHandler");

const router = express.Router();

router.post("/regression-toggle", (req, res, next) => {
  try {
    const { bug, enabled } = req.body || {};
    if (!setDemoRegressionBug(bug, enabled)) {
      throw createHttpError(400, "UNKNOWN_DEMO_BUG", "Supported demo bug: missing_order_id");
    }
    res.json({ demo_only: true, bug, enabled: Boolean(enabled), state: demoRegression });
  } catch (error) {
    next(error);
  }
});

router.get("/regression-toggle", (req, res) => {
  res.json({ demo_only: true, state: demoRegression });
});

module.exports = router;
