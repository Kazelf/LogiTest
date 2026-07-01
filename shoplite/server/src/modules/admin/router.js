const express = require("express");
const { prisma } = require("../../config/prisma");
const { authMiddleware, adminOnly } = require("../../middlewares/authMiddleware");
const { createHttpError } = require("../../middlewares/errorHandler");

const router = express.Router();
router.use(authMiddleware);

router.post("/products", adminOnly, async (req, res, next) => {
  try {
    const { name, brand, category, description = "", price, stock, image_url } = req.body;
    const categoryRecord = await prisma.category.upsert({
      where: { name: category },
      update: {},
      create: { name: category }
    });
    const product = await prisma.product.create({
      data: {
        name,
        brand,
        description,
        price: Number(price),
        stock: Number(stock),
        imageUrl: image_url,
        categoryId: categoryRecord.id
      },
      include: { category: true }
    });
    res.status(201).json({
      product_id: product.id,
      name: product.name,
      stock: product.stock
    });
  } catch (error) {
    next(error);
  }
});

router.put("/products/:id/stock", adminOnly, async (req, res, next) => {
  try {
    const stock = Number(req.body.stock);
    if (!Number.isInteger(stock) || stock < 0) throw createHttpError(400, "INVALID_STOCK", "Stock must be non-negative");
    const product = await prisma.product.update({
      where: { id: req.params.id },
      data: { stock }
    });
    await prisma.inventoryTransaction.create({
      data: { productId: product.id, type: "ADJUSTMENT", quantity: stock, reason: req.body.reason || "Admin stock update" }
    });
    res.json({ product_id: product.id, stock: product.stock });
  } catch (error) {
    next(error);
  }
});

router.post("/products/:id/decrease-stock", async (req, res, next) => {
  try {
    const quantity = Number(req.body.quantity || 1);
    const product = await prisma.product.findUnique({ where: { id: req.params.id } });
    if (!product) throw createHttpError(404, "PRODUCT_NOT_FOUND", "Product not found");
    const nextStock = Math.max(product.stock - quantity, 0);
    const updated = await prisma.product.update({
      where: { id: product.id },
      data: { stock: nextStock }
    });
    await prisma.inventoryTransaction.create({
      data: { productId: product.id, type: "DECREASE", quantity, reason: req.body.reason || "Admin decrease stock" }
    });
    res.json({ product_id: updated.id, stock: updated.stock });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
