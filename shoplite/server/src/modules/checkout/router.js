const express = require("express");
const { authMiddleware } = require("../../middlewares/authMiddleware");
const { createHttpError } = require("../../middlewares/errorHandler");
const { calculateCart, getOrCreateActiveCart, serializeCart } = require("../cart/service");

const router = express.Router();
router.use(authMiddleware);

router.post("/", async (req, res, next) => {
  try {
    const cart = await getOrCreateActiveCart(req.user.id);
    if (cart.items.length === 0) {
      throw createHttpError(400, "CART_EMPTY", "Cart is empty");
    }

    const outOfStock = cart.items.find((item) => item.product.stock < item.quantity);
    if (outOfStock) {
      throw createHttpError(409, "OUT_OF_STOCK", "Product is out of stock", {
        product_id: outOfStock.productId,
        available_stock: outOfStock.product.stock,
        requested_quantity: outOfStock.quantity
      });
    }

    res.json({
      checkout_ready: true,
      cart: serializeCart(cart),
      ...calculateCart(cart),
      shipping_address: req.body.shipping_address || req.user.address || "Demo Address"
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
