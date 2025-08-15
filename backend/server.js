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

  // Kořenová stránka – vynutíme světlé barvy
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(`
    <!doctype html>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="only light">
    <style>
      :root { color-scheme: light; }
      body { background:#ffffff; color:#111111; font:16px system-ui; margin:24px; line-height:1.4 }
      a { color:#0b5dd7; }
      code { background:#f4f4f4; padding:2px 4px; border-radius:4px }
    </style>
    <h1>moneyagario-api</h1>
    <p>Server běží ✅</p>
    <ul>
      <li><a href="/health">/health</a></li>
      <li><a href="/version">/version</a></li>
    </ul>
  `);
});

server.listen(port, () => {
  console.log(\`Listening on \${port}\`);
});
