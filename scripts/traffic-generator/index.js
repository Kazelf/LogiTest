#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { randomUUID } = require("crypto");

const FIXTURES = require("./fixtures.json");

const JOURNEYS = [
  "login_success",
  "login_failed",
  "browse_products",
  "search_product",
  "view_product_detail",
  "add_to_cart",
  "checkout_success",
  "checkout_failed",
  "view_order_status"
];

const SMOKE_JOURNEYS = ["browse_products", "login_success", "checkout_failed"];

const JOURNEY_REQUEST_ESTIMATES = {
  login_success: 1,
  login_failed: 1,
  browse_products: 2,
  search_product: 1,
  view_product_detail: 2,
  add_to_cart: 4,
  checkout_success: 6,
  checkout_failed: 3,
  view_order_status: 7
};

const MODE_DEFAULTS = {
  smoke: { targetLogs: 40, concurrency: 1, minDelayMs: 0, maxDelayMs: 25 },
  demo: { targetLogs: 360, concurrency: 3, minDelayMs: 80, maxDelayMs: 250 },
  load: { targetLogs: 2000, concurrency: 10, minDelayMs: 20, maxDelayMs: 120 }
};

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    const item = argv[i];
    if (!item.startsWith("--")) continue;
    const [rawKey, inlineValue] = item.slice(2).split("=");
    const key = rawKey.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    const next = argv[i + 1];
    args[key] = inlineValue ?? (next && !next.startsWith("--") ? argv[++i] : "true");
  }
  return args;
}

function loadDotEnv(filePath) {
  if (!fs.existsSync(filePath)) return;
  for (const line of fs.readFileSync(filePath, "utf8").split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
    const index = trimmed.indexOf("=");
    const key = trimmed.slice(0, index).trim();
    const value = trimmed
      .slice(index + 1)
      .trim()
      .replace(/^['"]|['"]$/g, "");
    if (key && process.env[key] === undefined) process.env[key] = value;
  }
}

function envValue(key, args, fallback) {
  const camel = key.toLowerCase().replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
  return args[camel] ?? process.env[key] ?? fallback;
}

function hasValue(key, args) {
  const camel = key.toLowerCase().replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
  return args[camel] !== undefined || process.env[key] !== undefined;
}

function numberValue(key, args, fallback) {
  const value = Number(envValue(key, args, fallback));
  return Number.isFinite(value) ? value : fallback;
}

function makeRandom(seed) {
  let state = 2166136261;
  for (const char of String(seed)) {
    state ^= char.charCodeAt(0);
    state = Math.imul(state, 16777619);
  }
  return () => {
    state += 0x6d2b79f5;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick(items, random) {
  return items[Math.floor(random() * items.length)];
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function buildConfig(args) {
  const requestedMode = String(envValue("MODE", args, "demo")).toLowerCase();
  const mode = MODE_DEFAULTS[requestedMode] ? requestedMode : "demo";
  const defaults = MODE_DEFAULTS[mode] || MODE_DEFAULTS.demo;
  const targetLogs = Math.max(1, numberValue("TARGET_LOGS", args, defaults.targetLogs));
  const totalSessions = hasValue("TARGET_LOGS", args)
    ? 0
    : Math.max(0, numberValue("TOTAL_SESSIONS", args, 0));

  return {
    baseUrl: String(envValue("BASE_URL", args, "http://localhost:4000")).replace(/\/$/, ""),
    mode,
    totalSessions,
    targetLogs,
    concurrency: Math.max(1, numberValue("CONCURRENCY", args, defaults.concurrency)),
    minDelayMs: Math.max(0, numberValue("MIN_DELAY_MS", args, defaults.minDelayMs)),
    maxDelayMs: Math.max(0, numberValue("MAX_DELAY_MS", args, defaults.maxDelayMs)),
    seed: String(envValue("SEED", args, "synthetic-traffic")),
    userPoolSize: Math.max(1, numberValue("USER_POOL_SIZE", args, FIXTURES.users.length)),
    outputSummaryPath: String(
      envValue(
        "OUTPUT_SUMMARY_PATH",
        args,
        path.join("reports", "synthetic-traffic", `traffic-summary-${timestamp()}.json`)
      )
    )
  };
}

function statusOk(status, expectedStatuses) {
  return expectedStatuses.includes(status);
}

function initSummary(config) {
  return {
    total_sessions: 0,
    total_requests: 0,
    success_requests: 0,
    expected_failed_requests: 0,
    unexpected_failed_requests: 0,
    journey_distribution: {},
    avg_latency_ms: 0,
    p95_latency_ms: 0,
    generated_at: new Date().toISOString(),
    base_url: config.baseUrl,
    mode: config.mode,
    list_of_generated_session_id: [],
    errors: []
  };
}

class TrafficClient {
  constructor(config, summary, random) {
    this.config = config;
    this.summary = summary;
    this.random = random;
  }

  async request(session, method, route, { body, token, expectedStatuses = [200, 201] } = {}) {
    const url = `${this.config.baseUrl}${route}`;
    const traceId = `trace_${session.id}_${String(session.requestIndex += 1).padStart(3, "0")}`;
    const headers = {
      "content-type": "application/json",
      "x-session-id": session.id,
      "x-trace-id": traceId,
      "x-journey-type": session.journey,
      "x-traffic-source": "synthetic-generator"
    };
    if (token) headers.authorization = `Bearer ${token}`;

    const started = Date.now();
    let status = 0;
    let payload = {};
    let errorMessage = "";

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body)
      });
      status = response.status;
      payload = await response.json().catch(() => ({}));
    } catch (error) {
      errorMessage = error.message;
    }

    const latency = Date.now() - started;
    const ok = statusOk(status, expectedStatuses);
    this.summary.total_requests += 1;
    this.summary._latencies.push(latency);
    if (ok && status >= 400) this.summary.expected_failed_requests += 1;
    else if (ok) this.summary.success_requests += 1;
    else {
      this.summary.unexpected_failed_requests += 1;
      this.summary.errors.push({
        session_id: session.id,
        journey_type: session.journey,
        method,
        route,
        status,
        error: errorMessage || payload.error_code || payload.message || "Unexpected response"
      });
    }

    const marker = ok && status >= 400 ? "expected-fail" : ok ? "ok" : "unexpected-fail";
    console.log(
      `[${session.id}] ${session.journey} ${method} ${route} -> ${status || "ERR"} ${latency}ms ${marker}${
        errorMessage ? ` ${errorMessage}` : ""
      }`
    );

    await this.pause();
    return { ok, status, payload, latency };
  }

  async pause() {
    const { minDelayMs, maxDelayMs } = this.config;
    const delay = minDelayMs + Math.floor(this.random() * Math.max(1, maxDelayMs - minDelayMs + 1));
    if (delay > 0) await sleep(delay);
  }
}

async function login(client, session, user) {
  const response = await client.request(session, "POST", "/api/auth/login", {
    body: { email: user.email, password: user.password }
  });
  return response.payload.accessToken || null;
}

async function loginAdmin(client, ctx) {
  if (ctx.adminToken) return ctx.adminToken;
  const session = makeSession("admin_setup", ctx.runId);
  ctx.adminToken = await login(client, session, FIXTURES.admin);
  return ctx.adminToken;
}

async function ensureUserPool(client, ctx, config) {
  while (ctx.users.length < config.userPoolSize) {
    const index = ctx.users.length + 1;
    const user = {
      email: `synthetic_user_${ctx.runId}_${index}@example.com`,
      password: "Password123"
    };
    const session = makeSession("register_synthetic_user", ctx.runId);
    const response = await client.request(session, "POST", "/api/auth/register", {
      body: {
        email: user.email,
        password: user.password,
        name: `synthetic_user_${index}`
      },
      expectedStatuses: [201, 409]
    });
    if (!response.ok) break;
    ctx.users.push(user);
  }
}

async function ensureSyntheticProduct(client, ctx, stock = FIXTURES.syntheticProduct.stock) {
  if (ctx.syntheticProduct && ctx.syntheticProduct.stock >= stock) return ctx.syntheticProduct;
  const token = await loginAdmin(client, ctx);
  if (!token) return null;
  const product = FIXTURES.syntheticProduct;
  const session = makeSession("admin_create_synthetic_product", ctx.runId);
  const response = await client.request(session, "POST", "/api/admin/products", {
    token,
    body: {
      name: `${product.namePrefix}_${ctx.runId}_${stock}`,
      brand: product.brand,
      category: product.category,
      description: product.description,
      price: product.price,
      stock,
      image_url: `/products/${product.namePrefix}.jpg`
    }
  });
  if (!response.ok) return null;
  ctx.syntheticProduct = {
    product_id: response.payload.product_id,
    name: response.payload.name,
    stock
  };
  return ctx.syntheticProduct;
}

async function firstProduct(client, session, query = "") {
  const response = await client.request(session, "GET", `/api/products${query}`);
  return response.payload.products?.[0] || null;
}

async function clearCart(client, session, token) {
  await client.request(session, "DELETE", "/api/cart", { token });
}

async function addProduct(client, session, token, product, quantity = 1, expectedStatuses = [201]) {
  return client.request(session, "POST", "/api/cart/items", {
    token,
    body: { product_id: product.product_id, quantity },
    expectedStatuses
  });
}

async function createOrderFlow(client, session, ctx) {
  const token = await login(client, session, pick(ctx.users, ctx.random));
  if (!token) return null;
  const product = await ensureSyntheticProduct(client, ctx);
  if (!product) return null;
  await clearCart(client, session, token);
  await addProduct(client, session, token, product, pick(FIXTURES.quantities.valid, ctx.random));
  await client.request(session, "POST", "/api/checkout", {
    token,
    body: { shipping_address: pick(FIXTURES.addresses, ctx.random) }
  });
  const order = await client.request(session, "POST", "/api/orders", {
    token,
    body: { shipping_address: pick(FIXTURES.addresses, ctx.random) }
  });
  return { token, orderId: order.payload.order_id };
}

const journeyHandlers = {
  async login_success(client, session, ctx) {
    await login(client, session, pick(ctx.users, ctx.random));
  },

  async login_failed(client, session) {
    await client.request(session, "POST", "/api/auth/login", {
      body: { email: "synthetic_wrong_user@example.com", password: "bad-password" },
      expectedStatuses: [401]
    });
  },

  async browse_products(client, session) {
    await client.request(session, "GET", "/api/categories");
    await client.request(session, "GET", "/api/products");
  },

  async search_product(client, session, ctx) {
    await client.request(session, "GET", `/api/products?keyword=${encodeURIComponent(pick(FIXTURES.keywords, ctx.random))}`);
  },

  async view_product_detail(client, session) {
    const product = await firstProduct(client, session);
    if (product) await client.request(session, "GET", `/api/products/${product.product_id}`);
  },

  async add_to_cart(client, session, ctx) {
    const token = await login(client, session, pick(ctx.users, ctx.random));
    const product = await ensureSyntheticProduct(client, ctx);
    if (token && product) {
      await clearCart(client, session, token);
      await addProduct(client, session, token, product, 1);
      await client.request(session, "GET", "/api/cart", { token });
    }
  },

  async checkout_success(client, session, ctx) {
    const order = await createOrderFlow(client, session, ctx);
    if (!order?.orderId) return;
    await client.request(session, "POST", "/api/payments/simulate-success", {
      token: order.token,
      body: { order_id: order.orderId }
    });
  },

  async checkout_failed(client, session, ctx) {
    const token = await login(client, session, pick(ctx.users, ctx.random));
    if (!token) return;
    await clearCart(client, session, token);
    await client.request(session, "POST", "/api/checkout", {
      token,
      body: {},
      expectedStatuses: [400]
    });
  },

  async view_order_status(client, session, ctx) {
    const order = await createOrderFlow(client, session, ctx);
    if (!order?.orderId) return;
    await client.request(session, "GET", "/api/orders", { token: order.token });
    await client.request(session, "GET", `/api/orders/${order.orderId}`, { token: order.token });
  }
};

function makeSession(journey, runId) {
  return {
    id: `sess_synthetic_${runId}_${randomUUID().slice(0, 8)}`,
    journey,
    requestIndex: 0
  };
}

function buildSessions(config, random) {
  const journeys = config.mode === "smoke" ? SMOKE_JOURNEYS : JOURNEYS;
  const totalSessions = config.totalSessions || sessionsForTargetLogs(journeys, config.targetLogs, config.mode);

  return Array.from({ length: totalSessions }, (_, index) => {
    const journey = config.mode === "load" ? pick(journeys, random) : journeys[index % journeys.length];
    return { journey };
  });
}

function sessionsForTargetLogs(journeys, targetLogs, mode) {
  let total = 0;
  let requests = 0;
  while (requests < targetLogs || (mode === "demo" && total < journeys.length * 2)) {
    const journey = journeys[total % journeys.length];
    requests += JOURNEY_REQUEST_ESTIMATES[journey] || 1;
    total += 1;
  }
  return total;
}

function buildUsers(config) {
  return FIXTURES.users.slice(0, Math.min(config.userPoolSize, FIXTURES.users.length));
}

async function runSession(client, ctx, sessionDef) {
  const session = makeSession(sessionDef.journey, ctx.runId);
  ctx.summary.total_sessions += 1;
  ctx.summary.list_of_generated_session_id.push(session.id);
  ctx.summary.journey_distribution[session.journey] = (ctx.summary.journey_distribution[session.journey] || 0) + 1;
  console.log(`[${session.id}] start ${session.journey}`);
  try {
    await journeyHandlers[session.journey](client, session, ctx);
  } catch (error) {
    ctx.summary.unexpected_failed_requests += 1;
    ctx.summary.errors.push({
      session_id: session.id,
      journey_type: session.journey,
      error: error.message
    });
    console.log(`[${session.id}] ${session.journey} error ${error.message}`);
  }
}

async function runPool(items, concurrency, worker) {
  let next = 0;
  const workers = Array.from({ length: Math.min(concurrency, items.length) }, async () => {
    while (next < items.length) {
      const item = items[next++];
      await worker(item);
    }
  });
  await Promise.all(workers);
}

function finalizeSummary(summary) {
  const latencies = summary._latencies.sort((a, b) => a - b);
  const sum = latencies.reduce((total, value) => total + value, 0);
  summary.avg_latency_ms = latencies.length ? Math.round(sum / latencies.length) : 0;
  summary.p95_latency_ms = latencies.length ? latencies[Math.floor((latencies.length - 1) * 0.95)] : 0;
  delete summary._latencies;
  return summary;
}

async function main() {
  loadDotEnv(path.resolve(process.cwd(), ".env"));
  loadDotEnv(path.resolve(__dirname, ".env"));
  const args = parseArgs(process.argv);
  const config = buildConfig(args);
  const random = makeRandom(config.seed);
  const summary = initSummary(config);
  summary._latencies = [];

  const ctx = {
    runId: timestamp().replace(/-/g, "").slice(0, 15),
    random,
    users: buildUsers(config),
    summary,
    adminToken: "",
    syntheticProduct: null
  };
  const client = new TrafficClient(config, summary, random);
  const sessions = buildSessions(config, random);

  console.log(
    `Synthetic traffic: mode=${config.mode} base=${config.baseUrl} sessions=${sessions.length} target_logs=${config.targetLogs}`
  );
  await ensureUserPool(client, ctx, config);
  await runPool(sessions, config.concurrency, (session) => runSession(client, ctx, session));

  const finalSummary = finalizeSummary(summary);
  const outputPath = path.resolve(process.cwd(), config.outputSummaryPath);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, `${JSON.stringify(finalSummary, null, 2)}\n`);

  console.log("");
  console.log(JSON.stringify(finalSummary, null, 2));
  console.log(`Traffic summary written to ${outputPath}`);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}

module.exports = {
  JOURNEYS,
  MODE_DEFAULTS,
  buildConfig,
  buildSessions,
  finalizeSummary,
  makeRandom,
  sessionsForTargetLogs
};
