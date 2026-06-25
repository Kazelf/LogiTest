"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import {
  DEMO_API_BASE_URL,
  demoApi,
  type DemoCart,
  type DemoContext,
  type DemoOrder,
  type DemoProduct,
  type DemoUser,
} from "../lib/demo-api";

type Step = "login" | "search" | "product" | "checkout" | "result";
type Notice = { type: "ok" | "error"; text: string } | null;

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(value);
}

function nextRequestId(step: string) {
  return `req-web-${step}-${Date.now()}`;
}

export default function DemoPage() {
  const [step, setStep] = useState<Step>("login");
  const [sessionId] = useState(() => makeId("session-web-demo"));
  const [traceId] = useState(() => makeId("trace-web-checkout"));
  const [user, setUser] = useState<DemoUser | null>(null);
  const [username, setUsername] = useState("buyer_001");
  const [password, setPassword] = useState("password123");
  const [keyword, setKeyword] = useState("headphones");
  const [products, setProducts] = useState<DemoProduct[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<DemoProduct | null>(null);
  const [cart, setCart] = useState<DemoCart | null>(null);
  const [order, setOrder] = useState<DemoOrder | null>(null);
  const [orderDetail, setOrderDetail] = useState<DemoOrder | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState("");

  const contextBase = useMemo(
    () => ({
      sessionId,
      traceId,
      userId: user?.userId,
    }),
    [sessionId, traceId, user?.userId],
  );

  const makeContext = (action: string): DemoContext => ({
    ...contextBase,
    requestId: nextRequestId(action),
  });

  async function runAction(label: string, action: () => Promise<void>) {
    setBusy(label);
    setNotice(null);
    try {
      await action();
      setNotice({ type: "ok", text: `${label} completed.` });
    } catch (error) {
      setNotice({
        type: "error",
        text: `${label} failed: ${error instanceof Error ? error.message : String(error)}`,
      });
    } finally {
      setBusy("");
    }
  }

  const handleLogin = () =>
    runAction("Login", async () => {
      const result = await demoApi.login({ username, password }, makeContext("login"));
      setUser(result);
      setStep("search");
    });

  const handleSearch = () =>
    runAction("Search products", async () => {
      const result = await demoApi.searchProducts(keyword, makeContext("search"));
      setProducts(result.items);
    });

  const openProduct = (productId: string) =>
    runAction("Open product", async () => {
      const product = await demoApi.getProduct(productId, makeContext("product-detail"));
      setSelectedProduct(product);
      setStep("product");
    });

  const addToCart = () =>
    runAction("Add to cart", async () => {
      if (!selectedProduct) {
        throw new Error("Select a product first.");
      }
      const updatedCart = await demoApi.addCartItem(selectedProduct.id, 1, makeContext("add-cart"));
      setCart(updatedCart);
    });

  const loadCheckout = () =>
    runAction("Load checkout", async () => {
      const currentCart = await demoApi.getCart(makeContext("cart"));
      setCart(currentCart);
      setStep("checkout");
    });

  const placeOrder = () =>
    runAction("Place order", async () => {
      const createdOrder = await demoApi.createOrder(makeContext("create-order"));
      const detail = await demoApi.getOrder(createdOrder.orderId, makeContext("order-detail"));
      setOrder(createdOrder);
      setOrderDetail(detail);
      setStep("result");
    });

  return (
    <main className="min-h-screen bg-[#f6f7f9] text-slate-950">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-3 border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase text-slate-500">LogiTest web demo</p>
            <h1 className="text-2xl font-semibold">Real buyer flow log producer</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Complete this flow to make the Express demo backend emit structured logs, then import them on the pipeline dashboard.
            </p>
          </div>
          <Link
            className="inline-flex h-9 items-center justify-center border border-slate-900 bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800"
            href="/"
          >
            Pipeline Dashboard
          </Link>
        </header>

        <section className="grid gap-3 border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-3">
          <KeyValue label="Demo API" value={DEMO_API_BASE_URL} />
          <KeyValue label="Session" value={sessionId} />
          <KeyValue label="Trace" value={traceId} />
        </section>

        <StepNav active={step} />

        {notice ? (
          <div
            className={`border p-3 text-sm ${
              notice.type === "error"
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-emerald-200 bg-emerald-50 text-emerald-700"
            }`}
          >
            {notice.text}
          </div>
        ) : null}

        {step === "login" ? (
          <Panel title="Login">
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Username" value={username} onChange={setUsername} />
              <Field label="Password" type="password" value={password} onChange={setPassword} />
            </div>
            <ActionButton disabled={Boolean(busy)} label={busy || "Login"} onClick={handleLogin} />
          </Panel>
        ) : null}

        {step === "search" ? (
          <Panel title="Product search">
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="flex-1">
                <Field label="Keyword" value={keyword} onChange={setKeyword} />
              </div>
              <div className="flex items-end">
                <ActionButton disabled={Boolean(busy)} label={busy || "Search"} onClick={handleSearch} />
              </div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {products.map((product) => (
                <button
                  className="border border-slate-200 bg-slate-50 p-3 text-left hover:border-slate-900"
                  key={product.id}
                  onClick={() => openProduct(product.id)}
                  type="button"
                >
                  <p className="font-semibold">{product.name}</p>
                  <p className="mt-1 text-sm text-slate-500">{product.category}</p>
                  <p className="mt-2 text-sm font-medium">{formatMoney(product.price)}</p>
                </button>
              ))}
            </div>
          </Panel>
        ) : null}

        {step === "product" && selectedProduct ? (
          <Panel title="Product detail and cart">
            <div className="grid gap-4 md:grid-cols-[1fr_1fr]">
              <div className="border border-slate-200 bg-slate-50 p-3">
                <p className="text-lg font-semibold">{selectedProduct.name}</p>
                <p className="mt-1 text-sm text-slate-500">Product ID: {selectedProduct.id}</p>
                <p className="mt-1 text-sm text-slate-500">Stock: {selectedProduct.stock}</p>
                <p className="mt-3 text-xl font-semibold">{formatMoney(selectedProduct.price)}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <ActionButton disabled={Boolean(busy)} label={busy || "Add to cart"} onClick={addToCart} />
                  <SecondaryButton disabled={Boolean(busy) || !cart?.items.length} label="Checkout" onClick={loadCheckout} />
                </div>
              </div>
              <CartSummary cart={cart} />
            </div>
          </Panel>
        ) : null}

        {step === "checkout" ? (
          <Panel title="Checkout">
            <CartSummary cart={cart} />
            <div className="mt-4">
              <ActionButton disabled={Boolean(busy) || !cart?.items.length} label={busy || "Place order"} onClick={placeOrder} />
            </div>
          </Panel>
        ) : null}

        {step === "result" && orderDetail ? (
          <Panel title="Order result">
            <div className="grid gap-3 md:grid-cols-3">
              <KeyValue label="Order ID" value={orderDetail.orderId} />
              <KeyValue label="Status" value={orderDetail.status} />
              <KeyValue label="Total" value={formatMoney(orderDetail.total)} />
            </div>
            <div className="mt-4 border border-slate-200 bg-slate-50 p-3 text-sm">
              <p className="font-semibold">Next demo steps</p>
              <p className="mt-2 text-slate-600">
                Open the pipeline dashboard, click Import ES, then Analyze, Generate Jest, and Run Test.
              </p>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link
                className="inline-flex h-9 items-center justify-center border border-slate-900 bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800"
                href="/"
              >
                Open Pipeline Dashboard
              </Link>
              <SecondaryButton
                disabled={Boolean(busy)}
                label="Start another flow"
                onClick={() => {
                  setStep("login");
                  setUser(null);
                  setProducts([]);
                  setSelectedProduct(null);
                  setCart(null);
                  setOrder(null);
                  setOrderDetail(null);
                  setNotice(null);
                }}
              />
            </div>
            <pre className="mt-4 max-h-80 overflow-auto border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-800">
              {JSON.stringify({ createdOrder: order, orderDetail }, null, 2)}
            </pre>
          </Panel>
        ) : null}
      </div>
    </main>
  );
}

function StepNav({ active }: { active: Step }) {
  const steps: Step[] = ["login", "search", "product", "checkout", "result"];
  return (
    <nav className="grid gap-2 sm:grid-cols-5">
      {steps.map((step, index) => (
        <div
          className={`border p-2 text-sm ${
            active === step ? "border-slate-900 bg-white text-slate-950" : "border-slate-200 bg-slate-100 text-slate-500"
          }`}
          key={step}
        >
          <span className="font-mono text-xs">{index + 1}</span> {step}
        </div>
      ))}
    </nav>
  );
}

function Panel({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <section className="border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Field({
  label,
  onChange,
  type = "text",
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  type?: string;
  value: string;
}) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input
        className="mt-1 h-10 w-full border border-slate-300 bg-white px-3 text-slate-950 outline-none focus:border-slate-900"
        onChange={(event) => onChange(event.target.value)}
        type={type}
        value={value}
      />
    </label>
  );
}

function ActionButton({
  disabled,
  label,
  onClick,
}: {
  disabled: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className="h-10 border border-slate-900 bg-slate-950 px-4 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:border-slate-300 disabled:bg-slate-200 disabled:text-slate-500"
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  );
}

function SecondaryButton({
  disabled,
  label,
  onClick,
}: {
  disabled: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className="h-10 border border-slate-300 bg-white px-4 text-sm font-medium text-slate-950 hover:border-slate-900 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  );
}

function KeyValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 text-sm">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-1 break-all font-mono text-slate-950">{value}</p>
    </div>
  );
}

function CartSummary({ cart }: { cart: DemoCart | null }) {
  return (
    <div className="border border-slate-200 bg-white p-3">
      <p className="font-semibold">Cart</p>
      {cart?.items.length ? (
        <div className="mt-3 space-y-2">
          {cart.items.map((item) => (
            <div className="flex justify-between gap-3 border-b border-slate-100 pb-2 text-sm" key={item.productId}>
              <span>
                {item.name} x {item.quantity}
              </span>
              <span className="font-medium">{formatMoney(item.lineTotal)}</span>
            </div>
          ))}
          <div className="flex justify-between pt-2 font-semibold">
            <span>Total</span>
            <span>{formatMoney(cart.total)}</span>
          </div>
        </div>
      ) : (
        <p className="mt-2 text-sm text-slate-500">Cart is empty.</p>
      )}
    </div>
  );
}
