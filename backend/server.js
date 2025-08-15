const express = require('express');

const app = express();
const port = process.env.PORT || 8080;

app.get('/', (_req, res) => {
  res.json({ ok: true, message: 'moneyagario-api is running' });
});

app.listen(port, () => {
  console.log(`Listening on port ${port}`);
});
