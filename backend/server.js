const http = require('http');
const { URL } = require('url');

const port = process.env.PORT || 8080;
const version = process.env.APP_VERSION || '0.1.0';

function send(res, status, body, headers = {}) {
  const isJson = typeof body !== 'string';
  res.writeHead(status, {
    'Cache-Control': 'no-store',
    ...(isJson ? { 'Content-Type': 'application/json; charset=utf-8' } : { 'Content-Type': 'text/plain; charset=utf-8' }),
    ...headers,
  });
  res.end(isJson ? JSON.stringify(body) : body);
}

function corsHeaders(req) {
  const origin = req.headers.origin || '*';
  return {
    'Access-Control-Allow-Origin': origin,
    'Vary': 'Origin',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '600',
  };
}

async function readJson(req) {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (chunk) => (data += chunk));
    req.on('end', () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch {
        resolve({});
      }
    });
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  console.log(`${new Date().toISOString()} ${req.method} ${url.pathname}`);

  // CORS preflight
  if (req.method === 'OPTIONS') {
    return send(res, 204, '', corsHeaders(req));
  }

  // Health
  if (url.pathname === '/health') {
    return send(res, 200, { ok: true }, corsHeaders(req));
  }

  // Version
  if (url.pathname === '/version') {
    return send(res, 200, { version }, corsHeaders(req));
  }

  // Plain text (rychlý test)
  if (url.pathname === '/plain') {
    return send(res, 200, 'ROOT PLAIN OK', corsHeaders(req));
  }

  // Debug
  if (url.pathname === '/debug') {
    return send(
      res,
      200,
      { path: url.pathname, method: req.method, headers: req.headers },
      corsHeaders(req)
    );
  }

  // Jednoduché API pro test frontendu
  if (url.pathname === '/api/echo' && req.method === 'GET') {
    const msg = url.searchParams.get('msg') || 'hello';
    return send(res, 200, { ok: true, msg, ts: Date.now() }, corsHeaders(req));
  }

  if (url.pathname === '/api/echo' && req.method === 'POST') {
    const body = await readJson(req);
    return send(res, 200, { ok: true, received: body, ts: Date.now() }, corsHeaders(req));
  }

  // favicon – ať neplevelí logy
  if (url.pathname === '/favicon.ico') {
    res.writeHead(204);
    return res.end();
  }

  // Root: jednoduchá HTML stránka (světlá)
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store',
    ...corsHeaders(req),
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
    html, body { background:#fff; color:#111; margin:0; font:16px system-ui; }
    main { padding:24px; line-height:1.55; max-width:720px; }
    a { color:#0b5dd7; }
    code { background:#f4f4f4; padding:2px 6px; border-radius:4px }
    pre { background:#f7f7f7; padding:12px; border-radius:6px; overflow:auto }
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
      <li><a href="/api/echo?msg=Ahoj">/api/echo?msg=Ahoj</a></li>
    </ul>
    <h2>Test API z prohlížeče</h2>
    <pre><code>fetch('/api/echo', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ foo: 'bar' }) })
  .then(r => r.json()).then(console.log)</code></pre>
  </main>
</body>
</html>`);
});

// Naslouchat na všech rozhraních
server.listen(port, '0.0.0.0', () => {
  console.log(`Listening on ${port}`);
});
