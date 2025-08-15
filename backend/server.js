const http = require('http');
const { URL } = require('url');

const port = process.env.PORT || 8080;
const version = process.env.APP_VERSION || '0.1.0';

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  console.log(`${new Date().toISOString()} ${req.method} ${url.pathname}`);

  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify({ ok: true }));
  }

  if (url.pathname === '/version') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify({ version }));
  }

  // Pro root vrátíme úplně prostý text
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end('OK moneyagario-api');
});

// Naslouchat na všech rozhraních
server.listen(port, '0.0.0.0', () => {
  console.log(`Listening on ${port}`);
});
