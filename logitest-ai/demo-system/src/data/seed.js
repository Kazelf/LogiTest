const seed = {
  users: [
    {
      id: "user-buyer-001",
      username: "buyer_001",
      password: "password123",
      name: "Demo Buyer",
      role: "customer",
    },
  ],
  products: [
    {
      id: "prod-headphone-001",
      name: "Wireless Headphones",
      category: "audio",
      price: 1290000,
      stock: 12,
    },
    {
      id: "prod-keyboard-001",
      name: "Mechanical Keyboard",
      category: "accessories",
      price: 890000,
      stock: 8,
    },
    {
      id: "prod-mouse-001",
      name: "Ergonomic Mouse",
      category: "accessories",
      price: 420000,
      stock: 20,
    },
  ],
  carts: {
    "user-buyer-001": {
      id: "cart-buyer-001",
      userId: "user-buyer-001",
      items: [],
    },
  },
  orders: {},
  payments: {},
  counters: {
    order: 1,
    payment: 1,
  },
};

function createStore() {
  return JSON.parse(JSON.stringify(seed));
}

module.exports = { createStore };
