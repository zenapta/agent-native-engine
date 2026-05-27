-- Ensure modern cryptographic extensions are live for random UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Main Global Workflow Instance Schema Registry
CREATE TABLE IF NOT EXISTS workflow_instances (
    id UUID PRIMARY KEY,
    workflow_definition_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'suspended', 'completed', 'failed')),
    global_context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. State Step/Node Tracking Execution Ledger Schema
CREATE TABLE IF NOT EXISTS node_states (
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'processing', 'awaiting_human', 'completed', 'failed')),
    agent_memory_log JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (instance_id, node_id)
);
