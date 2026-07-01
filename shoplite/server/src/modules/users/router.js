const express = require("express");
const { prisma } = require("../../config/prisma");
const { authMiddleware } = require("../../middlewares/authMiddleware");

const router = express.Router();

router.use(authMiddleware);

router.get("/me", (req, res) => {
  res.json({
    user_id: req.user.id,
    email: req.user.email,
    name: req.user.name,
    role: req.user.role,
    address: req.user.address
  });
});

router.put("/me/address", async (req, res, next) => {
  try {
    const user = await prisma.user.update({
      where: { id: req.user.id },
      data: { address: req.body.address || "" }
    });
    res.json({
      user_id: user.id,
      address: user.address
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
