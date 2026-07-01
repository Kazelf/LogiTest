const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const { prisma } = require("../../config/prisma");
const { env } = require("../../config/env");
const { authMiddleware } = require("../../middlewares/authMiddleware");
const { createHttpError } = require("../../middlewares/errorHandler");

const router = express.Router();

function publicUser(user) {
  return {
    user_id: user.id,
    email: user.email,
    name: user.name,
    role: user.role,
    address: user.address
  };
}

router.post("/register", async (req, res, next) => {
  try {
    const { email, password, name } = req.body;
    if (!email || !password) {
      throw createHttpError(400, "VALIDATION_ERROR", "Email and password are required");
    }

    const passwordHash = await bcrypt.hash(password, 10);
    const user = await prisma.user.create({
      data: { email, passwordHash, name: name || email.split("@")[0] }
    });
    res.status(201).json(publicUser(user));
  } catch (error) {
    if (error.code === "P2002") {
      next(createHttpError(409, "EMAIL_ALREADY_EXISTS", "Email already exists"));
      return;
    }
    next(error);
  }
});

router.post("/login", async (req, res, next) => {
  try {
    const { email, password } = req.body;
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
      throw createHttpError(401, "INVALID_CREDENTIALS", "Invalid email or password");
    }

    const accessToken = jwt.sign({ sub: user.id, role: user.role }, env.jwtSecret, { expiresIn: "8h" });
    res.json({
      user: publicUser(user),
      accessToken
    });
  } catch (error) {
    next(error);
  }
});

router.post("/logout", authMiddleware, async (req, res) => {
  res.json({ message: "Logged out" });
});

module.exports = router;
