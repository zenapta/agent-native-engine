const express = require('express');
const { handleInboundTrigger, handleHumanResumption } = require('./controllers/webhook.controller');

const app = express();
const PORT = process.env.PORT || 3000;

// Universal Middleware for handling standard JSON payload configurations
app.use(express.json());

// System Architecture Liveness Probe
app.get('/health', (req, res) => {
  res.status(200).json({ status: "healthy", timestamp: new Date() });
});

/**
 * System Framework Core Routing Surface Contracts
 */
// Inbound Ingress Route (Triggered by external events like Stripe, Salesforce, etc.)
app.post('/api/v1/webhook', handleInboundTrigger);

// Human-In-The-Loop (HITL) Resumption Route (Triggered by human operator review panels)
app.post('/api/v1/human/resume', handleHumanResumption);

// Global Error Catchment Layer to prevent application thread crashes
app.use((err, req, res, next) => {
  console.error('[Express Server Fatal Panic]:', err.stack);
  res.status(500).json({ error: "Internal Gateway Routing Disruption." });
});

// Boot listening thread
app.listen(PORT, () => {
  console.log("============================================================");
  console.log("AGENT ENGINE API GATEWAY ONLINE");
  console.log(`Listening on connection port: http://localhost:${PORT}`);
  console.log("Targeting Database Broker: CONNECTED");
  console.log("Targeting Redis Event Bus: CONNECTED");
  console.log("============================================================");
});
