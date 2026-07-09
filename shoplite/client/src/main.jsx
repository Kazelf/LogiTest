import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Bell,
  ChevronLeft,
  CreditCard,
  Heart,
  History,
  Home,
  LogOut,
  Package,
  Search,
  ShieldCheck,
  ShoppingBag,
  ShoppingCart,
  SlidersHorizontal,
  Star,
  Store,
  Tag,
  Truck,
  UserRound,
  Wrench
} from "lucide-react";
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
      requestAnimationFrame(() => window.scrollTo({ top: 0 }));
    }
  }

  async function openOrder(orderId) {
    const detail = await run(() => api(`/api/orders/${orderId}`));
    if (detail) {
      setSelectedOrder(detail);
      setView("order-detail");
      requestAnimationFrame(() => window.scrollTo({ top: 0 }));
    }
  }

  const brands = useMemo(() => [...new Set(products.map((product) => product.brand))].sort(), [products]);
  const cartCount = cart?.items?.reduce((total, item) => total + item.quantity, 0) || 0;

  return (
    <div className="shop-app">
      <header className="market-header">
        <div className="header-inner">
          <button className="brand" onClick={() => setView("products")} type="button">
            <ShoppingBag />
            <span>ShopLite</span>
          </button>
          <label className="global-search">
            <Search />
            <input
              placeholder="Search in ShopLite"
              value={filters.keyword}
              onChange={(event) => {
                const next = { ...filters, keyword: event.target.value };
                setFilters(next);
                loadProducts(next);
                setView("products");
              }}
            />
          </label>
          <nav className="header-actions">
            <button className={view === "products" ? "active" : ""} onClick={() => setView("products")} type="button"><Home /> Home</button>
            <button className={view === "cart" ? "active" : ""} onClick={() => { loadCart(); setView("cart"); }} type="button">
              <ShoppingCart /> Cart <span className="cart-badge">{cartCount}</span>
            </button>
            <button className={view === "orders" ? "active" : ""} onClick={() => { loadOrders(); setView("orders"); }} type="button"><History /> Orders</button>
            <button className={view === "admin" ? "active" : ""} onClick={() => setView("admin")} type="button"><Wrench /> Admin</button>
            {user ? <button onClick={logout} type="button"><LogOut /> Logout</button> : <button onClick={() => setView("login")} type="button"><UserRound /> Login</button>}
          </nav>
        </div>
        <div className="shop-strip">
          <span><ShieldCheck /> Buyer protection</span>
          <span><Truck /> Fast delivery</span>
          <span><Bell /> Live demo logs enabled</span>
          {user ? <span className="user-chip"><UserRound /> {user.email}</span> : null}
        </div>
      </header>

      <main className="market-main">
        {view !== "products" && (
          <header className="page-head">
            <div>
              <h1>{viewTitle(view)}</h1>
              <p>{user ? user.email : "Login with a demo user to create journey logs."}</p>
            </div>
            {user && <span className="role">{user.role}</span>}
          </header>
        )}

        {message && <div className="alert">{message}</div>}
        {!user && !["products", "detail", "login"].includes(view) ? <Login onLogin={login} /> : null}
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

function Cart({ cart, onLoad, onUpdate, onRemove, onVoucher, onCheckout }) {
  useEffect(() => { onLoad(); }, []);
  if (!cart) return null;
  return (
    <section className="panel">
      {cart.items.map((item) => (
        <div className="line-item" key={item.cart_item_id}>
          <div><strong>{item.name}</strong><span>{money(item.price)} / stock {item.stock}</span></div>
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
      <p>Status: {order?.order_status} / Payment: {order?.payment_status}</p>
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
      <p>{order.order_status} / {order.payment_status}</p>
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

function ProductArt({ product, large = false }) {
  return (
    <div className={`product-art ${large ? "large" : ""}`}>
      <span>{product.brand.slice(0, 2)}</span>
      <small>{product.category}</small>
    </div>
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
      <section className="market-hero">
        <div>
          <h1>ShopLite Mall</h1>
          <p>Flash deals, stocked inventory, and checkout flows wired for LogiTest journey mining.</p>
          <div className="hero-badges">
            <span><Star /> Top rated demo store</span>
            <span><Tag /> SALE50 voucher ready</span>
          </div>
        </div>
        <div className="hero-card">
          <strong>{products.length}</strong>
          <span>products available</span>
          <small>Every click still writes precise request logs.</small>
        </div>
      </section>

      <section className="category-rail">
        <button className={!filters.category ? "active" : ""} onClick={() => change("category", "")} type="button"><Store /> All</button>
        {categories.map((category) => (
          <button
            className={filters.category === category.name ? "active" : ""}
            key={category.category_id}
            onClick={() => change("category", category.name)}
            type="button"
          >
            <Package /> {category.name}
          </button>
        ))}
      </section>

      <section className="toolbar">
        <label><Search /> <input placeholder="Search keyword" value={filters.keyword} onChange={(event) => change("keyword", event.target.value)} /></label>
        <label><SlidersHorizontal /> Brand
          <select value={filters.brand} onChange={(event) => change("brand", event.target.value)}>
            <option value="">All brands</option>
            {brands.map((brand) => <option key={brand}>{brand}</option>)}
          </select>
        </label>
        <label>Sort
          <select value={filters.sort} onChange={(event) => change("sort", event.target.value)}>
            <option value="">Recommended</option>
            <option value="price_asc">Price asc</option>
            <option value="price_desc">Price desc</option>
          </select>
        </label>
      </section>

      <section className="product-grid">
        {products.map((product) => (
          <article className="product-card" key={product.product_id}>
            <button className="favorite" aria-label="Save product" type="button"><Heart /></button>
            <ProductArt product={product} />
            <div className="product-copy">
              <h2>{product.name}</h2>
              <p>{product.brand} / {product.category}</p>
              <div className="rating"><Star /> 4.8 <span>Sold 1.2k</span></div>
              <div className="price-row">
                <strong>{money(product.price)}</strong>
                <span>Stock {product.stock}</span>
              </div>
            </div>
            <div className="card-actions">
              <button onClick={() => onSelect(product)} type="button">View</button>
              <button className="primary" onClick={() => onAdd(product)} type="button"><ShoppingCart /> Add</button>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}

function ProductDetail({ product, onBack, onAdd }) {
  const [quantity, setQuantity] = useState(1);

  return (
    <section className="product-detail">
      <div className="detail-gallery">
        <button className="back-link" onClick={onBack} type="button"><ChevronLeft /> Back to shop</button>
        <ProductArt product={product} large />
        <div className="thumb-row">
          <ProductArt product={product} />
          <ProductArt product={product} />
          <ProductArt product={product} />
        </div>
      </div>
      <div className="detail-info">
        <p className="store-line"><Store /> {product.brand} official store</p>
        <h2>{product.name}</h2>
        <div className="detail-rating"><Star /> 4.8 <span>2.4k ratings</span><span>8.6k sold</span></div>
        <p className="description">{product.description}</p>
        <dl className="specs">
          <dt>Product ID</dt><dd>{product.product_id}</dd>
          <dt>Category</dt><dd>{product.category}</dd>
          <dt>Brand</dt><dd>{product.brand}</dd>
          <dt>Stock</dt><dd>{product.stock}</dd>
        </dl>
      </div>
      <aside className="buy-box">
        <span className="voucher"><Tag /> SALE50 available</span>
        <strong>{money(product.price)}</strong>
        <label>Quantity
          <input
            min="1"
            max={product.stock || 99}
            type="number"
            value={quantity}
            onChange={(event) => setQuantity(Math.max(1, Number(event.target.value) || 1))}
          />
        </label>
        <button className="primary" onClick={() => onAdd(product, quantity)} type="button"><ShoppingCart /> Add to cart</button>
        <button onClick={() => onAdd(product, quantity)} type="button"><ShoppingBag /> Buy now</button>
        <p><ShieldCheck /> Protected checkout and request logging.</p>
      </aside>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
