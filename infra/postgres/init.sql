-- Enable UUID generation capabilities (Native in PG 13+, but good practice to ensure availability)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create Enums for Workflow and Node State Machine Tracking
CREATE TYPE workflow_status AS ENUM (
    'idle', 
    'running', 
    'paused_human', 
    'failed', 
    'completed'
);

CREATE TYPE node_status AS ENUM (
    'pending', 
    'processing', 
    'awaiting_tool', 
    'awaiting_human', 
    'success', 
    'failed'
);

-- 2. Master Table for Parent Workflow Tracking
CREATE TABLE workflow_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id UUID NOT NULL,
    status workflow_status DEFAULT 'idle',
    global_context JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Granular Table for Individual Agentic Node Contexts & Memory Logs
CREATE TABLE node_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    status node_status DEFAULT 'pending',
    agent_memory_log JSONB NOT NULL DEFAULT '[]', -- Ephemeral scratchpad + context history
    execution_depth INT DEFAULT 0,                 -- Tracks self-correction loops to avoid token burn
    max_retries INT DEFAULT 5,
    error_stack TEXT,                             -- Captured stack traces for LLM analysis
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_node_per_instance UNIQUE (instance_id, node_id)
);

-- 4. High-Performance Indexes for Orchestrator Queries
-- The Go Orchestrator and Redis Bus will pull status fields thousands of times a minute.
CREATE INDEX idx_workflow_instances_status ON workflow_instances(status);
CREATE INDEX idx_node_states_instance_id ON node_states(instance_id);
CREATE INDEX idx_node_states_status ON node_states(status);

-- 5. Automated Trigger Function to maintain 'updated_at' accurately
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach Triggers to ensure timelines don't mismatch during race conditions
CREATE TRIGGER update_workflow_instances_modtime
    BEFORE UPDATE ON workflow_instances
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_node_states_modtime
    BEFORE UPDATE ON node_states
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();