const demoRegression = {
  missingOrderId: false
};

function setDemoRegressionBug(bug, enabled) {
  if (bug !== "missing_order_id") return false;
  demoRegression.missingOrderId = Boolean(enabled);
  return true;
}

module.exports = { demoRegression, setDemoRegressionBug };
