const http = require('http');
const port = process.env.PORT || 8080;

const server = http.createServer((_req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ ok: true, message: 'moneyagario-api is running' }));
});

server.listen(port, () => {
  console.log(`Listening on ${port}`);
});
