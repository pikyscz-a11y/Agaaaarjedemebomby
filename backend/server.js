const http = require('http');
const { URL } = require('url');

const port = process.env.PORT || 8080;
const version = process.env.APP_VERSION || '0.1.0';

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ ok: true }));
  }

  if (url.pathname === '/version') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ version }));
  }

  // Jednoduchá HTML stránka pro kořenovou URL
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(`
    <!doctype html>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>body{font:16px system-ui;margin:24px;line-height:1.4}</style>
    <h1>moneyagario-api</h1>
    <p>Server běží ✅</p>
    <ul>
      <li><a href="/health">/health</a></li>
      <li><a href="/version">/version</a></li>
    </ul>
  `);
});

server.listen(port, () => {
  console.log(`Listening on ${port}`);
});
