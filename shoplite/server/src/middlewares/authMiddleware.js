const jwt = require("jsonwebtoken");
const { prisma } = require("../config/prisma");
const { env } = require("../config/env");
const { createHttpError } = require("./errorHandler");

async function authMiddleware(req, res, next) {
  try {
    const header = req.headers.authorization;
    if (!header || !header.startsWith("Bearer ")) {
      throw createHttpError(401, "UNAUTHORIZED", "Missing bearer token");
    }

    const token = header.slice("Bearer ".length);
    const payload = jwt.verify(token, env.jwtSecret);
    const user = await prisma.user.findUnique({ where: { id: payload.sub } });

    if (!user) {
      throw createHttpError(401, "UNAUTHORIZED", "User not found");
    }

    req.user = user;
    next();
  } catch (error) {
    if (error.name === "JsonWebTokenError" || error.name === "TokenExpiredError") {
      next(createHttpError(401, "UNAUTHORIZED", "Invalid token"));
      return;
    }
    next(error);
  }
}

function adminOnly(req, res, next) {
  if (!req.user || req.user.role !== "ADMIN") {
    next(createHttpError(403, "FORBIDDEN", "Admin role is required"));
    return;
  }
  next();
}

module.exports = { authMiddleware, adminOnly };
