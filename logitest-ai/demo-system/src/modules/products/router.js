const express = require("express");

const { fail, ok } = require("../../shared/response");

function createProductsRouter(store) {
  const router = express.Router();

  router.get("/", (req, res) => {
    const keyword = String(req.query.keyword || req.query.query || "").toLowerCase();
    const items = store.products.filter((product) => {
      if (!keyword) {
        return true;
      }
      return (
        product.name.toLowerCase().includes(keyword) ||
        product.category.toLowerCase().includes(keyword)
      );
    });

    res.json(
      ok(
        {
          items,
          total: items.length,
        },
        { keyword },
      ),
    );
  });

  router.get("/:productId", (req, res) => {
    const product = store.products.find((candidate) => candidate.id === req.params.productId);
    if (!product) {
      res.status(404).json(fail("PRODUCT_NOT_FOUND", "Product was not found."));
      return;
    }

    res.json(ok(product));
  });

  return router;
}

module.exports = { createProductsRouter };
