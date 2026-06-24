const { createApp } = require("./app");

const port = Number(process.env.DEMO_BACKEND_PORT || process.env.PORT || 3001);
const app = createApp();

app.listen(port, () => {
  console.log(`Demo e-commerce backend listening on http://localhost:${port}`);
});
