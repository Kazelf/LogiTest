const demoRegression = {
  missingOrderId: false,
  paymentSuccessOrderNotPaid: false
};

function setDemoRegressionBug(bug, enabled) {
  if (bug === "missing_order_id") {
    demoRegression.missingOrderId = Boolean(enabled);
    return true;
  }
  if (bug === "payment_success_order_not_paid") {
    demoRegression.paymentSuccessOrderNotPaid = Boolean(enabled);
    return true;
  }
  return false;
}

module.exports = { demoRegression, setDemoRegressionBug };
