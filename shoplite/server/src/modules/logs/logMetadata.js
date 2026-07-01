const ROUTE_METADATA = [
  ["POST", /^\/api\/auth\/register$/, ["REGISTER", "USER", "AUTH_FLOW", null, "LOGIN"]],
  ["POST", /^\/api\/auth\/login$/, ["LOGIN", "USER", "AUTH_FLOW", null, "BROWSE_PRODUCTS"]],
  ["POST", /^\/api\/auth\/logout$/, ["LOGOUT", "USER", "AUTH_FLOW", null, null]],
  ["GET", /^\/api\/users\/me$/, ["GET_PROFILE", "USER", "AUTH_FLOW", "LOGIN", null]],
  ["PUT", /^\/api\/users\/me\/address$/, ["UPDATE_ADDRESS", "USER", "PROFILE_FLOW", "GET_PROFILE", "CHECKOUT"]],
  ["GET", /^\/api\/products$/, ["SEARCH_PRODUCTS", "PRODUCT", "BROWSE_FLOW", null, "VIEW_PRODUCT_DETAIL"]],
  ["GET", /^\/api\/products\/[^/]+$/, ["VIEW_PRODUCT_DETAIL", "PRODUCT", "BROWSE_FLOW", "SEARCH_PRODUCTS", "ADD_TO_CART"]],
  ["GET", /^\/api\/categories$/, ["LIST_CATEGORIES", "CATEGORY", "BROWSE_FLOW", null, "SEARCH_PRODUCTS"]],
  ["GET", /^\/api\/cart$/, ["VIEW_CART", "CART", "CART_FLOW", "ADD_TO_CART", "CHECKOUT"]],
  ["POST", /^\/api\/cart\/items$/, ["ADD_CART_ITEM", "CART_ITEM", "CART_FLOW", "VIEW_PRODUCT_DETAIL", "VIEW_CART"]],
  ["PUT", /^\/api\/cart\/items\/[^/]+$/, ["UPDATE_CART_ITEM", "CART_ITEM", "CART_FLOW", "VIEW_CART", "CHECKOUT"]],
  ["DELETE", /^\/api\/cart\/items\/[^/]+$/, ["REMOVE_CART_ITEM", "CART_ITEM", "CART_FLOW", "VIEW_CART", "CHECKOUT"]],
  ["DELETE", /^\/api\/cart$/, ["CLEAR_CART", "CART", "CART_FLOW", "VIEW_CART", "BROWSE_PRODUCTS"]],
  ["POST", /^\/api\/vouchers\/apply$/, ["APPLY_VOUCHER", "VOUCHER", "CHECKOUT_FLOW", "VIEW_CART", "CHECKOUT"]],
  ["DELETE", /^\/api\/vouchers\/remove$/, ["REMOVE_VOUCHER", "VOUCHER", "CHECKOUT_FLOW", "APPLY_VOUCHER", "CHECKOUT"]],
  ["POST", /^\/api\/checkout$/, ["CHECKOUT", "CART", "CHECKOUT_FLOW", "VIEW_CART", "CREATE_ORDER"]],
  ["POST", /^\/api\/orders$/, ["CREATE_ORDER", "ORDER", "CHECKOUT_FLOW", "CHECKOUT", "PAYMENT"]],
  ["GET", /^\/api\/orders$/, ["LIST_ORDERS", "ORDER", "ORDER_HISTORY_FLOW", "PAYMENT", "VIEW_ORDER_DETAIL"]],
  ["GET", /^\/api\/orders\/[^/]+$/, ["VIEW_ORDER_DETAIL", "ORDER", "ORDER_HISTORY_FLOW", "PAYMENT", null]],
  ["POST", /^\/api\/orders\/[^/]+\/cancel$/, ["CANCEL_ORDER", "ORDER", "ORDER_FLOW", "VIEW_ORDER_DETAIL", null]],
  ["POST", /^\/api\/payments\/simulate-success$/, ["PAYMENT_SUCCESS", "PAYMENT", "PAYMENT_FLOW", "CREATE_ORDER", "VIEW_ORDER_DETAIL"]],
  ["POST", /^\/api\/payments\/simulate-failed$/, ["PAYMENT_FAILED", "PAYMENT", "PAYMENT_FLOW", "CREATE_ORDER", "VIEW_ORDER_DETAIL"]],
  ["POST", /^\/api\/payments\/webhook$/, ["PAYMENT_WEBHOOK", "PAYMENT", "PAYMENT_FLOW", "PAYMENT_PROVIDER", "VIEW_ORDER_DETAIL"]],
  ["POST", /^\/api\/admin\/products$/, ["ADMIN_CREATE_PRODUCT", "PRODUCT", "ADMIN_INVENTORY_FLOW", null, null]],
  ["PUT", /^\/api\/admin\/products\/[^/]+\/stock$/, ["ADMIN_UPDATE_STOCK", "PRODUCT", "ADMIN_INVENTORY_FLOW", null, null]],
  ["POST", /^\/api\/admin\/products\/[^/]+\/decrease-stock$/, ["ADMIN_DECREASE_STOCK", "PRODUCT", "ADMIN_INVENTORY_FLOW", null, "CHECKOUT"]]
];

function getLogMetadata(method, path, responseBody) {
  const match = ROUTE_METADATA.find(([routeMethod, pattern]) => routeMethod === method && pattern.test(path));
  if (!match) return {};

  const [, , [actionName, businessEntity, journeyHint, previousStep, nextExpectedStep]] = match;
  return {
    action_name: actionName,
    business_entity: businessEntity,
    business_entity_id: inferEntityId(responseBody),
    journey_hint: journeyHint,
    previous_step: previousStep,
    next_expected_step: nextExpectedStep
  };
}

function inferEntityId(body) {
  if (!body || typeof body !== "object") return null;
  return body.order_id || body.payment_id || body.cart_item_id || body.cart_id || body.product_id || body.user_id || body.id || null;
}

module.exports = { getLogMetadata };
