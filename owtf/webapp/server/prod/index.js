const express = require('express');
const path = require('path');
const logger = require('./logger');
const proxyMiddleware = require('http-proxy-middleware');
const app = express();
const port = 8019;
const host = "localhost";
// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, '../../build')));

// Wildcard route to serve index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../../build/index.html'));
});

app.listen(port, (err) => {
    if (err) {
      return logger.error(err.message);
    }
  
    logger.appStarted(port, host);
  });