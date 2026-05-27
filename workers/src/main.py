import os
import sys
import json
import time
import random

# Ensure Python can locate internal modules if executed from the repository root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.execution_loop import AgenticNodeRuntime

class AgentWorkerDaemon:
    """
    Asynchronous Worker process that listens to centralized queues, 
    hydrates agent environments, and coordinates execution with the DB.
    """
    def __init__(self, queue_topic: str):
        self.queue_topic = queue_topic
        self.is_running = True
        print(f"[Worker Core] Initialized cluster process targeting queue: '{self.queue_topic}'")

    def mock_pull_task_from_queue(self) -> dict:
        """
        Simulates fetching an inbound workflow orchestration payload from a Redis/Temporal queue.
        """
        # In production, this would block using a Redis BRPOP or a Temporal worker poll
        time.sleep(2) 
        
        # We simulate a real payload containing database tracking IDs and execution contexts
        return {
            "workflow_instance_id": "a3b8c9d0-1234-5678-90ab-cdef12345678",
            "node_id": "NODE_TRIAGE_01",
            "max_retries": 5,
            "system_persona": (
                "You are an enterprise support triage agent. Clean incoming unstructured email blocks "
                "using 'format_complaint' and categorize the underlying intent."
            ),
            "inbound_context": {
                "email_body": "CRITICAL: Our database sync tool crashed on production. Lost connection token."
            }
        }

    def update_database_state(self, instance_id: str, node_id: str, status: str, payload: dict):
        """
        Simulates updating the state machine tracking logs in PostgreSQL (node_states table).
        """
        print(f"[DB Sync] UPDATE node_states SET status='{status}', updated_at=NOW()")
        if status in ['failed', 'awaiting_human']:
            print(f"    -> Logging diagnostic context / errors: {list(payload.keys())}")
        else:
            print(f"    -> Mutating global context payload array with success metrics.")

    def run(self):
        """
        The continuous background process execution loop.
        """
        print(f"[Worker Core] Daemon loop entered. Waiting for pipeline triggers...")
        
        # Limit loop iteration for this verification script so it completes cleanly
        cycles = 1 
        
        while self.is_running and cycles > 0:
            cycles -= 1
            try:
                # 1. Pull dynamic execution packet from the event bus
                task = self.mock_pull_task_from_queue()
                print(f"\n[Job Received] Processing Node [{task['node_id']}] for Instance [{task['workflow_instance_id']}]")
                
                # 2. Synchronize immediate state to Postgres -> Flip node to 'processing'
                self.update_database_state(
                    task["workflow_instance_id"], 
                    task["node_id"], 
                    "processing", 
                    {}
                )

                # 3. Instantiate the isolated runtime brain we verified in Step 2
                runtime = AgenticNodeRuntime(
                    node_id=task["node_id"],
                    system_persona=task["system_persona"],
                    max_retries=task["max_retries"]
                )

                # 4. Handoff context processing directly to the probabilistic reasoner
                execution_status, result_payload = runtime.execute(task["inbound_context"])

                # 5. Process state outcomes cleanly according to schema requirements
                if execution_status == "success":
                    self.update_database_state(
                        task["workflow_instance_id"], 
                        task["node_id"], 
                        "success", 
                        {"global_context_mutation": result_payload}
                    )
                elif execution_status == "awaiting_human":
                    self.update_database_state(
                        task["workflow_instance_id"], 
                        task["node_id"], 
                        "awaiting_human", 
                        {"serialized_memory": result_payload}
                    )
                else:
                    self.update_database_state(
                        task["workflow_instance_id"], 
                        task["node_id"], 
                        "failed", 
                        {"error_trace": result_payload}
                    )

            except Exception as e:
                print(f"[CRITICAL FAILURE] Worker crashed during process handling: {str(e)}")
                # Fail gracefully back to dead-letter storage tracking queues if processing fails hard
                
        print("\n[Worker Core] Daemon cycle verification finished processing.")

if __name__ == "__main__":
    # Start the daemon pointing to our data-processing worker partition
    daemon = AgentWorkerDaemon(queue_topic="agent.exec.data-processing")
    daemon.run()