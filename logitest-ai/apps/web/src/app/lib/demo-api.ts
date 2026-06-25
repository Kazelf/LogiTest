export const DEMO_API_BASE_URL =
  process.env.NEXT_PUBLIC_DEMO_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:3001";

type DemoContext = {
  sessionId: string;
  traceId: string;
  requestId: string;
  userId?: string;
};

type DemoEnvelope<T> = {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
  meta?: Record<string, unknown>;
};

export type DemoUser = {
  userId: string;
  username: string;
  name: string;
  role: string;
  token: string;
};

export type DemoProduct = {
  id: string;
  name: string;
  category: string;
  price: number;
  stock: number;
};

export type DemoProductSearch = {
  items: DemoProduct[];
  total: number;
};

export type DemoCartItem = {
  productId: string;
  name: string;
  price: number;
  quantity: number;
  lineTotal: number;
};

export type DemoCart = {
  cartId: string;
  userId: string;
  items: DemoCartItem[];
  total: number;
};

export type DemoOrder = {
  orderId: string;
  userId: string;
  cartId: string;
  status: string;
  items: DemoCartItem[];
  total: number;
  currency: string;
};

type QueryValue = string | number | boolean | null | undefined;

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const url = new URL(`${DEMO_API_BASE_URL}${path}`);
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

function contextHeaders(context: DemoContext) {
  return {
    "x-session-id": context.sessionId,
    "x-trace-id": context.traceId,
    "x-request-id": context.requestId,
    ...(context.userId ? { "x-user-id": context.userId } : {}),
  };
}

async function demoRequest<T>(
  path: string,
  context: DemoContext,
  options: RequestInit & { query?: Record<string, QueryValue> } = {},
) {
  const { query, headers, ...init } = options;
  const response = await fetch(buildUrl(path, query), {
    ...init,
    headers: {
      "content-type": "application/json",
      ...contextHeaders(context),
      ...headers,
    },
  });

  const body = (await response.json().catch(() => null)) as DemoEnvelope<T> | null;
  if (!response.ok || !body?.success) {
    const message = body?.error?.message ?? response.statusText;
    throw new Error(`${response.status} ${message}`);
  }

  return body.data as T;
}

export const demoApi = {
  login: (credentials: { username: string; password: string }, context: DemoContext) =>
    demoRequest<DemoUser>("/api/auth/login", context, {
      method: "POST",
      body: JSON.stringify(credentials),
    }),
  searchProducts: (keyword: string, context: DemoContext) =>
    demoRequest<DemoProductSearch>("/api/products", context, {
      query: { keyword },
    }),
  getProduct: (productId: string, context: DemoContext) =>
    demoRequest<DemoProduct>(`/api/products/${productId}`, context),
  getCart: (context: DemoContext) => demoRequest<DemoCart>("/api/cart", context),
  addCartItem: (productId: string, quantity: number, context: DemoContext) =>
    demoRequest<DemoCart>("/api/cart/items", context, {
      method: "POST",
      body: JSON.stringify({ productId, quantity }),
    }),
  createOrder: (context: DemoContext) =>
    demoRequest<DemoOrder>("/api/orders", context, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  getOrder: (orderId: string, context: DemoContext) =>
    demoRequest<DemoOrder>(`/api/orders/${orderId}`, context),
};

export type { DemoContext };
