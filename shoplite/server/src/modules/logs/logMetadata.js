const ROUTE_METADATA = [
  ["POST", /^\/api\/auth\/register$/, ["REGISTER", "USER", "AUTHENTICATION", null, "LOGIN"]],
  ["POST", /^\/api\/auth\/login$/, ["LOGIN", "USER", "AUTHENTICATION", null, "VIEW_PRODUCTS"]],
  ["POST", /^\/api\/auth\/logout$/, ["LOGOUT", "USER", "AUTHENTICATION", null, null]],
  ["GET", /^\/api\/users\/me$/, ["GET_PROFILE", "USER", "AUTHENTICATION", "LOGIN", null]],
  ["PUT", /^\/api\/users\/me\/address$/, ["UPDATE_ADDRESS", "USER", "PROFILE_FLOW", "GET_PROFILE", "CHECKOUT"]],
  ["GET", /^\/api\/products$/, ["VIEW_PRODUCTS", "PRODUCT", "PRODUCT_DISCOVERY", null, "VIEW_PRODUCT_DETAIL"]],
  ["GET", /^\/api\/products\/:id$/, ["VIEW_PRODUCT_DETAIL", "PRODUCT", "PRODUCT_DISCOVERY", "SEARCH_PRODUCTS", "ADD_TO_CART"]],
  ["GET", /^\/api\/categories$/, ["LIST_CATEGORIES", "CATEGORY", "PRODUCT_DISCOVERY", null, "SEARCH_PRODUCTS"]],
  ["GET", /^\/api\/cart$/, ["VIEW_CART", "CART", "CART_MANAGEMENT", "ADD_TO_CART", "CHECKOUT"]],
  ["POST", /^\/api\/cart\/items$/, ["ADD_TO_CART", "CART_ITEM", "CART_MANAGEMENT", "VIEW_PRODUCT_DETAIL", "VIEW_CART"]],
  ["PUT", /^\/api\/cart\/items\/:id$/, ["UPDATE_CART_ITEM", "CART_ITEM", "CART_MANAGEMENT", "VIEW_CART", "CHECKOUT"]],
  ["DELETE", /^\/api\/cart\/items\/:id$/, ["REMOVE_CART_ITEM", "CART_ITEM", "CART_MANAGEMENT", "VIEW_CART", "CHECKOUT"]],
  ["DELETE", /^\/api\/cart$/, ["CLEAR_CART", "CART", "CART_MANAGEMENT", "VIEW_CART", "VIEW_PRODUCTS"]],
  ["POST", /^\/api\/vouchers\/apply$/, ["APPLY_VOUCHER", "VOUCHER", "CHECKOUT_FLOW", "VIEW_CART", "CHECKOUT"]],
  ["DELETE", /^\/api\/vouchers\/remove$/, ["REMOVE_VOUCHER", "VOUCHER", "CHECKOUT_FLOW", "APPLY_VOUCHER", "CHECKOUT"]],
  ["POST", /^\/api\/checkout$/, ["CHECKOUT", "CART", "CHECKOUT_FLOW", "VIEW_CART", "CREATE_ORDER"]],
  ["POST", /^\/api\/orders$/, ["CREATE_ORDER", "ORDER", "CHECKOUT_FLOW", "CHECKOUT", "PAYMENT"]],
  ["GET", /^\/api\/orders$/, ["VIEW_ORDER_HISTORY", "ORDER", "ORDER_TRACKING", "PAYMENT", "VIEW_ORDER_DETAIL"]],
  ["GET", /^\/api\/orders\/:id$/, ["VIEW_ORDER_DETAIL", "ORDER", "ORDER_TRACKING", "PAYMENT", null]],
  ["POST", /^\/api\/orders\/:id\/cancel$/, ["CANCEL_ORDER", "ORDER", "ORDER_TRACKING", "VIEW_ORDER_DETAIL", null]],
  ["POST", /^\/api\/payments\/simulate-success$/, ["PAYMENT_SUCCESS", "PAYMENT", "PAYMENT_FLOW", "CREATE_ORDER", "VIEW_ORDER_DETAIL"]],
  ["POST", /^\/api\/payments\/simulate-failed$/, ["PAYMENT_FAILED", "PAYMENT", "PAYMENT_FLOW", "CREATE_ORDER", "VIEW_ORDER_DETAIL"]],
  ["POST", /^\/api\/payments\/webhook$/, ["PAYMENT_WEBHOOK", "PAYMENT", "PAYMENT_FLOW", "PAYMENT_PROVIDER", "VIEW_ORDER_DETAIL"]],
  ["POST", /^\/api\/admin\/products$/, ["ADMIN_CREATE_PRODUCT", "PRODUCT", "ADMIN_INVENTORY_FLOW", null, null]],
  ["PUT", /^\/api\/admin\/products\/:id\/stock$/, ["ADMIN_UPDATE_STOCK", "PRODUCT", "ADMIN_INVENTORY_FLOW", null, null]],
  ["POST", /^\/api\/admin\/products\/:id\/decrease-stock$/, ["ADMIN_DECREASE_STOCK", "PRODUCT", "ADMIN_INVENTORY_FLOW", null, "CHECKOUT"]]
];

function getLogMetadata(method, path, query = {}, responseBody) {
  const match = ROUTE_METADATA.find(([routeMethod, pattern]) => routeMethod === method && pattern.test(path));
  if (!match) return {};

  const [, , [baseActionName, businessEntity, journeyHint, previousStep, nextExpectedStep]] = match;
  const actionName = method === "GET" && path === "/api/products" ? classifyProductListAction(query) : baseActionName;
  return {
    action_name: actionName,
    business_entity: businessEntity,
    business_entity_id: inferEntityId(responseBody),
    journey_hint: journeyHint,
    previous_step: previousStep,
    next_expected_step: nextExpectedStep
  };
}

function classifyProductListAction(query = {}) {
  if (hasQueryValue(query.sort)) return "SORT_PRODUCTS";
  if (
    hasQueryValue(query.brand) ||
    hasQueryValue(query.category) ||
    hasQueryValue(query.minPrice) ||
    hasQueryValue(query.maxPrice)
  ) {
    return "FILTER_PRODUCTS";
  }
  if (hasQueryValue(query.keyword)) return "SEARCH_PRODUCTS";
  return "VIEW_PRODUCTS";
}

function hasQueryValue(value) {
  if (Array.isArray(value)) return value.some(hasQueryValue);
  return value !== undefined && value !== null && String(value).trim() !== "";
}

function inferEntityId(body) {
  if (!body || typeof body !== "object") return null;
  return body.order_id || body.payment_id || body.cart_item_id || body.cart_id || body.product_id || body.user_id || body.id || null;
}

module.exports = { getLogMetadata, classifyProductListAction };
