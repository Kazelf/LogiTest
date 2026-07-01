const express = require("express");
const { prisma } = require("../../config/prisma");
const { createHttpError } = require("../../middlewares/errorHandler");

const router = express.Router();
const categoriesRouter = express.Router();

function serializeProduct(product) {
  return {
    product_id: product.id,
    name: product.name,
    brand: product.brand,
    category: product.category.name,
    description: product.description,
    price: product.price,
    stock: product.stock,
    image_url: product.imageUrl
  };
}

router.get("/", async (req, res, next) => {
  try {
    const { keyword, category, brand, minPrice, maxPrice, sort } = req.query;
    const where = {
      AND: [
        keyword
          ? {
              OR: [
                { name: { contains: String(keyword), mode: "insensitive" } },
                { description: { contains: String(keyword), mode: "insensitive" } }
              ]
            }
          : {},
        category ? { category: { name: { equals: String(category), mode: "insensitive" } } } : {},
        brand ? { brand: { equals: String(brand), mode: "insensitive" } } : {},
        minPrice ? { price: { gte: Number(minPrice) } } : {},
        maxPrice ? { price: { lte: Number(maxPrice) } } : {}
      ]
    };

    const products = await prisma.product.findMany({
      where,
      include: { category: true },
      orderBy: sort === "price_asc" ? { price: "asc" } : sort === "price_desc" ? { price: "desc" } : { name: "asc" }
    });

    res.json({
      products: products.map(serializeProduct),
      count: products.length
    });
  } catch (error) {
    next(error);
  }
});

router.get("/:id", async (req, res, next) => {
  try {
    const product = await prisma.product.findUnique({
      where: { id: req.params.id },
      include: { category: true }
    });
    if (!product) throw createHttpError(404, "PRODUCT_NOT_FOUND", "Product not found");
    res.json(serializeProduct(product));
  } catch (error) {
    next(error);
  }
});

categoriesRouter.get("/", async (req, res, next) => {
  try {
    const categories = await prisma.category.findMany({ orderBy: { name: "asc" } });
    res.json({
      categories: categories.map((category) => ({
        category_id: category.id,
        name: category.name
      }))
    });
  } catch (error) {
    next(error);
  }
});

router.categoriesRouter = categoriesRouter;
module.exports = router;
