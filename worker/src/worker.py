import os
import sys
import json
import time
import signal
import redis
import psycopg2
from psycopg2.extras import Json

def main():
    print("============================================================")
    print("STARTING AGENT NATIVE PYTHON COGNITIVE WORKER")
    print("============================================================")

    redis_url = os.getenv("REDIS_URL")
    database_url = os.getenv("DATABASE_URL")

    if not redis_url or not database_url:
        print("[Worker Error] Missing critical REDIS_URL or DATABASE_URL env variables.")
        sys.exit(1)

    try:
        db_conn = psycopg2.connect(database_url)
        db_conn.autocommit = True
        cursor = db_conn.cursor()
        print("Targeting Database Broker: CONNECTED")
    except Exception as e:
        print(f"[Worker Error] PostgreSQL target unreachable: {e}")
        sys.exit(1)

    try:
        rdb = redis.Redis.from_url(redis_url, decode_responses=True)
        rdb.ping()
        print("Targeting Redis Event Bus: CONNECTED")
    except Exception as e:
        print(f"[Worker Error] Redis Event Bus unreachable: {e}")
        sys.exit(1)

    print("============================================================")

    target_channel = "agent.worker.triage"
    pubsub = rdb.pubsub()
    pubsub.subscribe(target_channel)
    print(f"[Worker Core] Listening on Channel: [{target_channel}]")
    print("[Worker Core] Awaiting execution packets from Go Orchestrator...")

    def handle_shutdown(signum, frame):
        print("\n[Worker] Termination intercept. Closing broker links and shutting down...")
        cursor.close()
        db_conn.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    for message in pubsub.listen():
        if message['type'] != 'message':
            continue

        try:
            payload = json.loads(message['data'])
            instance_id = payload.get("workflow_instance_id")
            node_id = payload.get("node_id")
            context_data = payload.get("inbound_context", {})

            print(f"\n[Worker Intercept] Processing Task -> Instance: {instance_id} | Node: {node_id}")
            print(f"[Worker Compute] Evaluating payload data parameters: {json.dumps(context_data)}")

            time.sleep(1.5) 
            priority = context_data.get("priority", "low")
            
            agent_evaluation = {
                "triage_decision": "approved_for_review" if priority == "high" else "auto_resolved",
                "confidence_score": 0.94,
                "engine_timestamp": time.time()
            }

            memory_log = [
                {"role": "system", "content": "Triage evaluation layer activated."},
                {"role": "assistant", "content": f"Evaluation complete. Action taken: {agent_evaluation['triage_decision']}"}
            ]

            print("[Worker Ledger] Updating node tracking state to 'completed'...")
            cursor.execute(
                """
                UPDATE node_states 
                SET status = 'completed', 
                    agent_memory_log = %s, 
                    updated_at = NOW() 
                WHERE instance_id = %s AND node_id = %s;
                """,
                (Json(memory_log), instance_id, node_id)
            )

            cursor.execute(
                """
                UPDATE workflow_instances 
                SET status = 'completed', 
                    updated_at = NOW() 
                WHERE id = %s;
                """,
                (instance_id,)
            )

            print(f"[Worker Success] Transaction cycle finalized for instance: {instance_id}")

        except Exception as err:
            print(f"[Worker Loop Error] Failed to process event package: {err}")

if __name__ == "__main__":
    main()
