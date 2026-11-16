#!/usr/bin/env node
/**
 * Mai Dashboard — Dev Server
 * Simple static file server for local development.
 *
 * Usage: node server.js [port]
 *   Default port: 8080
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = parseInt(process.argv[2] || '8080', 10);
const dir = __dirname;
const mimeTypes = {
  '.html': 'text/html',
  '.json': 'application/json',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
};

http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://localhost').pathname; // strip ?query before resolving a file
  const filePath = path.join(dir, pathname === '/' ? 'dashboard.html' : pathname);
  const ext = path.extname(filePath);
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'text/plain' });
    res.end(data);
  });
}).listen(PORT, () => console.log(`Dashboard running on http://localhost:${PORT}`));
