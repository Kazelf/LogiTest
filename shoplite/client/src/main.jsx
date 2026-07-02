import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { CreditCard, History, LogOut, Package, Search, ShoppingCart, Tag, UserRound, Wrench } from "lucide-react";
import { api, setToken } from "./services/api";
import { money } from "./utils/format";
import "./styles.css";

const demoUsers = [
  "normal_buyer@example.com",
  "browser_user@example.com",
  "hesitant_buyer@example.com",
  "voucher_hunter@example.com",
  "error_case_user@example.com",
  "admin@example.com"
];

function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("products");
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [cart, setCart] = useState(null);
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [paymentResult, setPaymentResult] = useState(null);
  const [filters, setFilters] = useState({ keyword: "", brand: "", category: "", sort: "" });
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadProducts();
    api("/api/categories").then((data) => setCategories(data.categories)).catch(() => {});
  }, []);

  async function run(action) {
    setMessage("");
    try {
      return await action();
    } catch (error) {
      setMessage(`${error.status || ""} ${error.payload?.error_code || "ERROR"}: ${error.payload?.message || error.message}`);
      return null;
    }
  }

  async function login(email) {
    const data = await run(() => api("/api/auth/login", { method: "POST", body: { email, password: "Password123" } }));
    if (!data) return;
    setToken(data.accessToken);
    setUser(data.user);
    setView("products");
    await loadCart();
  }

  function logout() {
    setToken(null);
    setUser(null);
    setCart(null);
    setOrders([]);
    setView("login");
  }

  async function loadProducts(nextFilters = filters) {
    const query = new URLSearchParams(Object.entries(nextFilters).filter(([, value]) => value));
    const data = await run(() => api(`/api/products${query.toString() ? `?${query}` : ""}`));
    if (data) setProducts(data.products);
  }

  async function loadCart() {
    const data = await run(() => api("/api/cart"));
    if (data) setCart(data);
  }

  async function loadOrders() {
    const data = await run(() => api("/api/orders"));
    if (data) setOrders(data.orders);
  }

  async function addToCart(product, quantity = 1) {
    const data = await run(() => api("/api/cart/items", { method: "POST", body: { product_id: product.product_id, quantity } }));
    if (data) {
      setCart(data.cart);
      setView("cart");
    }
  }

  async function updateCartItem(item, quantity) {
    const data = await run(() => api(`/api/cart/items/${item.cart_item_id}`, { method: "PUT", body: { quantity } }));
    if (data) setCart(data.cart);
  }

  async function removeCartItem(item) {
    const data = await run(() => api(`/api/cart/items/${item.cart_item_id}`, { method: "DELETE" }));
    if (data) setCart(data.cart);
  }

  async function applyVoucher() {
    const data = await run(() => api("/api/vouchers/apply", { method: "POST", body: { code: "SALE50" } }));
    if (data) setCart(data.cart);
  }

  async function checkout() {
    const data = await run(() => api("/api/checkout", { method: "POST", body: {} }));
    if (data) setView("checkout");
  }

  async function createOrder() {
    const data = await run(() => api("/api/orders", { method: "POST", body: { shipping_address: user.address || "Demo Address" } }));
    if (data) {
      setSelectedOrder(data);
      setView("payment");
      await loadCart();
    }
  }

  async function pay(success) {
    const data = await run(() =>
      api(success ? "/api/payments/simulate-success" : "/api/payments/simulate-failed", {
        method: "POST",
        body: { order_id: selectedOrder.order_id }
      })
    );
    if (data) {
      setPaymentResult(data);
      const detail = await api(`/api/orders/${selectedOrder.order_id}`);
      setSelectedOrder(detail);
    }
  }

  async function openProduct(productId) {
    const detail = await run(() => api(`/api/products/${productId}`));
    if (detail) {
      setSelectedProduct(detail);
      setView("detail");
    }
  }

  async function openOrder(orderId) {
    const detail = await run(() => api(`/api/orders/${orderId}`));
    if (detail) {
      setSelectedOrder(detail);
      setView("order-detail");
    }
  }

  const brands = useMemo(() => [...new Set(products.map((product) => product.brand))].sort(), [products]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">ShopLite</div>
        <button className={view === "products" ? "active" : ""} onClick={() => setView("products")}><Package /> Products</button>
        <button className={view === "cart" ? "active" : ""} onClick={() => { loadCart(); setView("cart"); }}><ShoppingCart /> Cart</button>
        <button className={view === "orders" ? "active" : ""} onClick={() => { loadOrders(); setView("orders"); }}><History /> Orders</button>
        <button className={view === "admin" ? "active" : ""} onClick={() => setView("admin")}><Wrench /> Admin</button>
        <div className="spacer" />
        {user ? <button onClick={logout}><LogOut /> Logout</button> : <button onClick={() => setView("login")}><UserRound /> Login</button>}
      </aside>

      <main>
        <header className="topbar">
          <div>
            <h1>{viewTitle(view)}</h1>
            <p>{user ? user.email : "Login with a demo user to create journey logs."}</p>
          </div>
          {user && <span className="role">{user.role}</span>}
        </header>

        {message && <div className="alert">{message}</div>}
        {!user && view !== "products" ? <Login onLogin={login} /> : null}
        {view === "login" && <Login onLogin={login} />}
        {view === "products" && (
          <Products
            products={products}
            filters={filters}
            setFilters={setFilters}
            categories={categories}
            brands={brands}
            onSearch={loadProducts}
            onSelect={(product) => openProduct(product.product_id)}
            onAdd={addToCart}
          />
        )}
        {view === "detail" && selectedProduct && <ProductDetail product={selectedProduct} onBack={() => setView("products")} onAdd={addToCart} />}
        {view === "cart" && <Cart cart={cart} onLoad={loadCart} onUpdate={updateCartItem} onRemove={removeCartItem} onVoucher={applyVoucher} onCheckout={checkout} />}
        {view === "checkout" && <Checkout cart={cart} onCreateOrder={createOrder} />}
        {view === "payment" && <Payment order={selectedOrder} result={paymentResult} onPay={pay} onDetail={() => openOrder(selectedOrder.order_id)} />}
        {view === "orders" && <Orders orders={orders} onOpen={openOrder} />}
        {view === "order-detail" && selectedOrder && <OrderDetail order={selectedOrder} />}
        {view === "admin" && <Admin products={products} onDone={() => loadProducts()} />}
      </main>
    </div>
  );
}

function viewTitle(view) {
  return {
    login: "Login",
    products: "Product List",
    detail: "Product Detail",
    cart: "Cart",
    checkout: "Checkout",
    payment: "Payment Result",
    orders: "Order History",
    "order-detail": "Order Detail",
    admin: "Admin Inventory"
  }[view] || "ShopLite";
}

function Login({ onLogin }) {
  return (
    <section className="panel login-grid">
      {demoUsers.map((email) => (
        <button className="login-user" key={email} onClick={() => onLogin(email)}>
          <UserRound />
          <span>{email}</span>
          <small>Password123</small>
        </button>
      ))}
    </section>
  );
}

function Products({ products, filters, setFilters, categories, brands, onSearch, onSelect, onAdd }) {
  function change(key, value) {
    const next = { ...filters, [key]: value };
    setFilters(next);
    onSearch(next);
  }
  return (
    <>
      <section className="toolbar">
        <label><Search /> <input placeholder="Search keyword" value={filters.keyword} onChange={(event) => change("keyword", event.target.value)} /></label>
        <select value={filters.category} onChange={(event) => change("category", event.target.value)}>
          <option value="">All categories</option>
          {categories.map((category) => <option key={category.category_id}>{category.name}</option>)}
        </select>
        <select value={filters.brand} onChange={(event) => change("brand", event.target.value)}>
          <option value="">All brands</option>
          {brands.map((brand) => <option key={brand}>{brand}</option>)}
        </select>
        <select value={filters.sort} onChange={(event) => change("sort", event.target.value)}>
          <option value="">Default sort</option>
          <option value="price_asc">Price asc</option>
          <option value="price_desc">Price desc</option>
        </select>
      </section>
      <section className="product-grid">
        {products.map((product) => (
          <article className="product-card" key={product.product_id}>
            <div className="product-art">{product.brand.slice(0, 2)}</div>
            <h2>{product.name}</h2>
            <p>{product.brand} · {product.category}</p>
            <strong>{money(product.price)}</strong>
            <span>Stock {product.stock}</span>
            <div className="row">
              <button onClick={() => onSelect(product)}>Detail</button>
              <button className="primary" onClick={() => onAdd(product)}>Add</button>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}

function ProductDetail({ product, onBack, onAdd }) {
  return (
    <section className="panel split">
      <div className="product-art large">{product.brand.slice(0, 2)}</div>
      <div>
        <button onClick={onBack}>Back</button>
        <h2>{product.name}</h2>
        <p>{product.description}</p>
        <dl>
          <dt>Product ID</dt><dd>{product.product_id}</dd>
          <dt>Brand</dt><dd>{product.brand}</dd>
          <dt>Price</dt><dd>{money(product.price)}</dd>
          <dt>Stock</dt><dd>{product.stock}</dd>
        </dl>
        <button className="primary" onClick={() => onAdd(product)}>Add to cart</button>
      </div>
    </section>
  );
}

function Cart({ cart, onLoad, onUpdate, onRemove, onVoucher, onCheckout }) {
  useEffect(() => { onLoad(); }, []);
  if (!cart) return null;
  return (
    <section className="panel">
      {cart.items.map((item) => (
        <div className="line-item" key={item.cart_item_id}>
          <div><strong>{item.name}</strong><span>{money(item.price)} · stock {item.stock}</span></div>
          <input type="number" min="1" value={item.quantity} onChange={(event) => onUpdate(item, Number(event.target.value))} />
          <strong>{money(item.line_total)}</strong>
          <button onClick={() => onRemove(item)}>Remove</button>
        </div>
      ))}
      <Totals cart={cart} />
      <div className="row">
        <button onClick={onVoucher}><Tag /> Apply SALE50</button>
        <button className="primary" onClick={onCheckout}>Checkout</button>
      </div>
    </section>
  );
}

function Totals({ cart }) {
  return (
    <div className="totals">
      <span>Subtotal {money(cart.subtotal_amount)}</span>
      <span>Discount {money(cart.discount_amount)}</span>
      <strong>Total {money(cart.total_amount)}</strong>
    </div>
  );
}

function Checkout({ cart, onCreateOrder }) {
  return (
    <section className="panel">
      <h2>Ready to create order</h2>
      {cart && <Totals cart={cart} />}
      <button className="primary" onClick={onCreateOrder}>Create order</button>
    </section>
  );
}

function Payment({ order, result, onPay, onDetail }) {
  return (
    <section className="panel">
      <h2>Order {order?.order_id}</h2>
      <p>Status: {order?.order_status} · Payment: {order?.payment_status}</p>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
      <div className="row">
        <button className="primary" onClick={() => onPay(true)}><CreditCard /> Simulate success</button>
        <button onClick={() => onPay(false)}>Simulate failed</button>
        <button onClick={onDetail}>View order detail</button>
      </div>
    </section>
  );
}

function Orders({ orders, onOpen }) {
  return (
    <section className="panel">
      {orders.map((order) => (
        <button className="order-row" key={order.order_id} onClick={() => onOpen(order.order_id)}>
          <span>{order.order_id}</span>
          <strong>{order.order_status}</strong>
          <span>{money(order.total_amount)}</span>
        </button>
      ))}
    </section>
  );
}

function OrderDetail({ order }) {
  return (
    <section className="panel">
      <h2>{order.order_id}</h2>
      <p>{order.order_status} · {order.payment_status}</p>
      {order.items.map((item) => (
        <div className="line-item" key={item.order_item_id}>
          <strong>{item.name}</strong>
          <span>Qty {item.quantity}</span>
          <span>{money(item.line_total)}</span>
        </div>
      ))}
      <Totals cart={order} />
    </section>
  );
}

function Admin({ products, onDone }) {
  const [target, setTarget] = useState("");
  const [stock, setStock] = useState(0);
  async function updateStock() {
    if (!target) return;
    await api(`/api/admin/products/${target}/stock`, { method: "PUT", body: { stock } });
    onDone();
  }
  return (
    <section className="panel">
      <select value={target} onChange={(event) => setTarget(event.target.value)}>
        <option value="">Choose product</option>
        {products.map((product) => <option key={product.product_id} value={product.product_id}>{product.name}</option>)}
      </select>
      <input type="number" min="0" value={stock} onChange={(event) => setStock(Number(event.target.value))} />
      <button className="primary" onClick={updateStock}>Update stock</button>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
