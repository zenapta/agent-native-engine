const { Pool } = require('pg');
const { createClient } = require('redis');
const crypto = require('crypto');

// Establish Real Live PostgreSQL Connection Pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// Establish Real Live Redis Client
const redisClient = createClient({
  url: process.env.REDIS_URL
});
redisClient.on('error', (err) => console.error('[Redis Client Error]', err));
redisClient.connect();

/**
 * Handles incoming external B2B webhooks
 */
const handleInboundTrigger = async (req, res) => {
  try {
    const { event_type, payload } = req.body;
    console.log(`\n[Gateway Ingress] Inbound Webhook Received: Trigger Event [${event_type}]`);

    if (!event_type || !payload) {
      return res.status(400).json({ error: "Invalid schema payload contract." });
    }

    // ARCHITECTURAL FIX: Both tracking IDs must conform to the UUID schema specification
    const workflowDefinitionId = crypto.randomUUID(); 
    const instanceId = crypto.randomUUID(); 

    console.log(`[Gateway Ingress] Schema Validated IDs -> Def: ${workflowDefinitionId} | Inst: ${instanceId}`);

    // Writing real data to the live PostgreSQL container tables
    await pool.query(
      `INSERT INTO workflow_instances (id, workflow_definition_id, status, global_context) VALUES ($1, $2, 'running', $3);`,
      [instanceId, workflowDefinitionId, JSON.stringify(payload)]
    );

    await pool.query(
      `INSERT INTO node_states (instance_id, node_id, status) VALUES ($1, $2, 'pending');`,
      [instanceId, "NODE_TRIAGE_01"]
    );

    // Broadcasting a real message packet over the live Redis cluster channels
    const queuePayload = {
      workflow_instance_id: instanceId,
      node_id: "NODE_TRIAGE_01",
      inbound_context: payload
    };
    await redisClient.publish("agent.exec.data-processing", JSON.stringify(queuePayload));

    return res.status(202).json({
      message: "Workflow ingestion lifecycle initialized successfully.",
      workflow_instance_id: instanceId
    });

  } catch (error) {
    console.error(`[Gateway Error] Ingestion failure:`, error);
    return res.status(500).json({ error: "Internal engine ingestion failure." });
  }
};

/**
 * Handles Human-in-the-Loop Resumption submissions
 */
const handleHumanResumption = async (req, res) => {
  const { workflow_instance_id, node_id, human_input_data } = req.body;
  const lockKey = `lock:workflow:instance:${workflow_instance_id}`;

  try {
    const acquired = await redisClient.set(lockKey, "locked", { NX: true, PX: 5000 });
    if (!acquired) {
      return res.status(423).json({ error: "Resource locked." });
    }

    const stateRes = await pool.query(
      `SELECT agent_memory_log, status FROM node_states WHERE instance_id = $1 AND node_id = $2;`,
      [workflow_instance_id, node_id]
    );

    if (stateRes.rows.length === 0 || stateRes.rows[0].status !== "awaiting_human") {
      await redisClient.del(lockKey);
      return res.status(400).json({ error: "Target node is not in suspended state." });
    }

    let activeMemoryLog = stateRes.rows[0].agent_memory_log || [];
    activeMemoryLog.push({
      role: "user",
      content: `HUMAN_OPERATOR_RESPONSE: ${JSON.stringify(human_input_data)}`
    });

    await pool.query(
      `UPDATE node_states SET status = 'pending', agent_memory_log = $1 WHERE instance_id = $2 AND node_id = $3;`,
      [JSON.stringify(activeMemoryLog), workflow_instance_id, node_id]
    );

    await pool.query(
      `UPDATE workflow_instances SET status = 'running' WHERE id = $1;`,
      [workflow_instance_id]
    );

    const taskPayload = { workflow_instance_id, node_id, inbound_context: human_input_data };
    await redisClient.publish("agent.exec.data-processing", JSON.stringify(taskPayload));

    await redisClient.del(lockKey);
    return res.status(200).json({ message: "Cognitive pause cleared.", current_node_status: "pending" });

  } catch (error) {
    console.error(`[Gateway Error] State rehydration sequence crashed:`, error);
    await redisClient.del(lockKey);
    return res.status(500).json({ error: "State rehydration process collapse." });
  }
};

module.exports = { handleInboundTrigger, handleHumanResumption };
