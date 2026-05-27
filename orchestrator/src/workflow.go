package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	_ "github.com/lib/pq"
	"github.com/redis/go-redis/v9"
)

// Pipeline Payload Packet Contracts
type WorkflowPacket struct {
	WorkflowInstanceID string                 `json:"workflow_instance_id"`
	NodeID             string                 `json:"node_id"`
	InboundContext     map[string]interface{} `json:"inbound_context"`
}

func main() {
	log.Println("============================================================")
	log.Println("STARTING AGENT NATIVE GO STATE ORCHESTRATOR")
	log.Println("============================================================")

	ctx := context.Background()
	dbURL := os.Getenv("DATABASE_URL")
	redisURL := os.Getenv("REDIS_URL")

	if dbURL == "" || redisURL == "" {
		log.Fatal("[Orchestrator Fatal] Missing DATABASE_URL or REDIS_URL environment variables.")
	}

	// 1. Resilient PostgreSQL Connection Handle
	var db *sql.DB
	var err error
	for i := 1; i <= 5; i++ {
		log.Printf("Connecting to Ledger Database (Attempt %d/5)...", i)
		db, err = sql.Open("postgres", dbURL)
		if err == nil {
			err = db.Ping()
		}
		if err == nil {
			break
		}
		log.Printf("Database not ready: %v. Retrying in 3 seconds...", err)
		time.Sleep(3 * time.Second)
	}
	if err != nil {
		log.Fatalf("[Orchestrator Fatal] Could not connect to Postgres Ledger: %v", err)
	}
	log.Println("Targeting Database Broker: CONNECTED")

	// 2. Resilient Redis Connection Handle
	var rdb *redis.Client
	for i := 1; i <= 5; i++ {
		log.Printf("Connecting to Redis Event Bus (Attempt %d/5)...", i)
		opt, redisErr := redis.ParseURL(redisURL)
		if redisErr == nil {
			rdb = redis.NewClient(opt)
			err = rdb.Ping(ctx).Err()
		} else {
			err = redisErr
		}
		if err == nil {
			break
		}
		log.Printf("Redis not ready: %v. Retrying in 3 seconds...", err)
		time.Sleep(3 * time.Second)
	}
	if err != nil {
		log.Fatalf("[Orchestrator Fatal] Could not connect to Redis Bus: %v", err)
	}
	log.Println("Targeting Redis Event Bus: CONNECTED")
	log.Println("============================================================")

	// 3. Subscribe to Inbound Gateway Signals
	inputChannel := "agent.workflow.trigger"
	workerChannel := "agent.worker.triage"
	pubsub := rdb.Subscribe(ctx, inputChannel)
	defer pubsub.Close()

	log.Printf("[Orchestrator Core] Active. Listening for Gateway events on channel: [%s]", inputChannel)

	ch := pubsub.Channel()
	for msg := range ch {
		log.Printf("[Event Intercept] Inbound trigger caught on channel: %s", inputChannel)

		// Parse the incoming event registration packet
		var packet WorkflowPacket
		if err := json.Unmarshal([]byte(msg.Payload), &packet); err != nil {
			log.Printf("[Orchestrator Error] Failed to decode payload packet structure: %v", err)
			continue
		}

		log.Printf("[State Machine] Initializing Node State Ledger for Instance: %s | Node: %s", packet.WorkflowInstanceID, packet.NodeID)

		// 4. Record the Node Lifecycle State into PostgreSQL
		query := `
			INSERT INTO node_states (instance_id, node_id, status, created_at, updated_at)
			VALUES ($1, $2, 'processing', NOW(), NOW())
			ON CONFLICT (instance_id, node_id) 
			DO UPDATE SET status = 'processing', updated_at = NOW();
		`
		_, err = db.Exec(query, packet.WorkflowInstanceID, packet.NodeID)
		if err != nil {
			log.Printf("[Ledger Error] Failed to write initial state tracking row: %v", err)
			continue
		}

		// 5. Handshake the execution sequence payload out to the Python Worker channel
		workerPayload, _ := json.Marshal(packet)
		err = rdb.Publish(ctx, workerChannel, workerPayload).Err()
		if err != nil {
			log.Printf("[Orchestrator Error] Failed to dispatch packet to worker mesh: %v", err)
			continue
		}

		log.Printf("[State Machine Success] Dispatched Task payload forward onto Channel: [%s]", workerChannel)
	}
}
