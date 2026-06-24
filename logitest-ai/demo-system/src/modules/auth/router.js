const express = require("express");

const { fail, ok } = require("../../shared/response");

function createAuthRouter(store) {
  const router = express.Router();

  router.post("/login", (req, res) => {
    const { username, password } = req.body || {};
    const user = store.users.find(
      (candidate) => candidate.username === username && candidate.password === password,
    );

    if (!user) {
      res.status(401).json(fail("INVALID_CREDENTIALS", "Username or password is invalid."));
      return;
    }

    req.user = user;
    const token = `demo-token-${user.id}`;

    res.json(
      ok({
        userId: user.id,
        username: user.username,
        name: user.name,
        role: user.role,
        token,
      }),
    );
  });

  return router;
}

module.exports = { createAuthRouter };
