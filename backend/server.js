const http = require('http');
const { URL } = require('url');

const port = process.env.PORT || 8080;
const version = process.env.APP_VERSION || '0.1.0';

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  console.log(`${new Date().toISOString()} ${req.method} ${url.pathname}`);

  // Zdraví
  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify({ ok: true }));
  }

  // Verze
  if (url.pathname === '/version') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify({ version }));
  }

  // Jednoduchý text pro ověření zobrazení
  if (url.pathname === '/plain') {
    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' });
    return res.end('ROOT PLAIN OK');
  }

  // Debug – vrátí hlavičky a cestu
  if (url.pathname === '/debug') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify({ path: url.pathname, headers: req.headers }, null, 2));
  }

  // Favicon – ať nezaclání v logu
  if (url.pathname === '/favicon.ico') {
    res.writeHead(204);
    return res.end();
  }

  // Root: plné HTML (světlé barvy, žádné triky)
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store'
  });
  res.end(`<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="only light">
  <title>moneyagario-api</title>
  <style>
    :root { color-scheme: light; }
    html, body { background:#ffffff; color:#111111; margin:0; font:16px system-ui; }
    main { padding:24px; line-height:1.5; }
    a { color:#0b5dd7; }
    code { background:#f4f4f4; padding:2px 6px; border-radius:4px }
  </style>
</head>
<body>
  <main>
    <h1>moneyagario-api</h1>
    <p>Server běží ✅</p>
    <ul>
      <li><a href="/health">/health</a></li>
      <li><a href="/version">/version</a></li>
      <li><a href="/plain">/plain</a></li>
      <li><a href="/debug">/debug</a></li>
    </ul>
  </main>
</body>
</html>`);
});

// Naslouchat na všech rozhraních
server.listen(port, '0.0.0.0', () => {
  console.log(`Listening on ${port}`);
});
