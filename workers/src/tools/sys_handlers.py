import json
import uuid
from typing import Dict, Any, List

class CognitivePauseInterrupt(Exception):
    """
    Custom control-flow exception. Used to instantly break out of the 
    agent reasoning loop, preserve context, and prevent downstream execution.
    """
    def __init__(self, node_id: str, payload: Dict[str, Any]):
        super().__init__(f"Cognitive intercept triggered on node: {node_id}")
        self.node_id = node_id
        self.payload = payload


class HumanInterventionHandler:
    """
    Handles the execution isolation, validation, and serialization formatting
    when an agent requests human operator support.
    """
    def __init__(self, node_id: str, instance_id: str):
        self.node_id = node_id
        self.instance_id = instance_id

    def sys_human_intervention(self, clarification_prompt: str, expected_response_schema: Dict[str, Any], current_memory_log: List[Dict[str, str]]) -> None:
        """
        The formal tool invoked by the agent when it cannot process unstructured ambiguity.
        
        CRITICAL BUG FIX: We pass a deep copy snapshot of the current memory log 
        to ensure subsequent background garbage collection doesn't contaminate 
        the exact state of the agent's mind at the point of suspension.
        """
        print(f"\n[Cognitive Intercept] Agent on Node '{self.node_id}' requested human routing.")
        print(f"  -> Reason: \"{clarification_prompt}\"")

        # 1. Structural Sanity Checks to avoid UI rendering crashes on the dashboard
        if not expected_response_schema or "type" not in expected_response_schema:
            # Fallback schema to ensure the human can always unblock the workflow
            expected_response_schema = {
                "type": "object",
                "properties": {"manual_override_text": {"type": "string", "description": "Raw text input to override agent state."}},
                "required": ["manual_override_text"]
            }

        # 2. Package the suspension payload matching the database schema specifications
        suspension_package = {
            "workflow_instance_id": self.instance_id,
            "node_id": self.node_id,
            "status": "awaiting_human",
            "intercept_metadata": {
                "ticket_id": f"HITL_TKT_{uuid.uuid4().hex[:8].upper()}",
                "reason_raised": clarification_prompt,
                "required_input_schema": expected_response_schema
            },
            # Deep snapshot preservation
            "serialized_memory_snapshot": json.loads(json.dumps(current_memory_log))
        }

        # 3. Raise the control exception to break out of any nested retry loop loops instantly
        raise CognitivePauseInterrupt(node_id=self.node_id, payload=suspension_package)

    def process_human_rehydration(self, serialized_snapshot: List[Dict[str, str]], human_input_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Rehydrates a frozen memory state and injects the human's response payload
        as a virtual message, prepping it for queue re-entry.
        """
        print(f"\n[Rehydration Core] Reconstituting state for instance: {self.instance_id}")
        
        # Deep copy back to life
        hydrated_memory = json.loads(json.dumps(serialized_snapshot))
        
        # Format the injection precisely to guide the agent's next action step smoothly
        human_injection_message = {
            "role": "user",
            "content": f"HUMAN_OPERATOR_CLARIFICATION_RESPONSE: {json.dumps(human_input_data)}"
        }
        
        hydrated_memory.append(human_injection_message)
        print("  -> Human payload successfully appended as a system instruction event vector.")
        return hydrated_memory


# --- Standalone Testing/Validation Routine ---
if __name__ == "__main__":
    print("="*60)
    print("RUNNING COGNITIVE PAUSE AND REHYDRATION LIFECYCLE TESTS:")
    print("="*60)

    # Mock identifiers matching our PostgreSQL expectations
    MOCK_INSTANCE = "b4f91011-abcd-ef01-2345-6789abcdef12"
    MOCK_NODE = "NODE_CONTRACT_NEGOTIATION_02"
    
    handler = HumanInterventionHandler(node_id=MOCK_NODE, instance_id=MOCK_INSTANCE)
    
    # Simulate a deep execution trace log
    dummy_memory_state = [
        {"role": "system", "content": "You are a legal contract review agent."},
        {"role": "user", "content": "Review contract v2."},
        {"role": "assistant", "content": "Analyzing payment liability clauses. Indemnity limits undefined."}
    ]

    # Target form parameters for the Admin Canvas UI fields
    target_schema = {
        "type": "object",
        "properties": {
            "approved_liability_cap_usd": {"type": "integer", "description": "Maximum legal cap value allowed."}
        },
        "required": ["approved_liability_cap_usd"]
    }

    frozen_payload = None

    # Step A: Simulate Agent triggering the pause
    try:
        handler.sys_human_intervention(
            clarification_prompt="The client removed the $1M indemnity cap. I cannot accept unlimited risk parameters.",
            expected_response_schema=target_schema,
            current_memory_log=dummy_memory_state
        )
    except CognitivePauseInterrupt as intercept:
        print("\n[SUCCESS] Execution broken safely via CognitivePauseInterrupt.")
        frozen_payload = intercept.payload

    # Step B: Simulate the Webhook / Dashboard Response cycle occurring hours later
    print("\n--- Simulating Dashboard Interaction Window ---")
    mock_human_ui_submission = {
        "approved_liability_cap_usd": 500000
    }

    # Rehydrate the state and pass it down the pipeline
    active_memory_now = handler.process_human_rehydration(
        serialized_snapshot=frozen_payload["serialized_memory_snapshot"],
        human_input_data=mock_human_ui_submission
    )

    print("\n" + "="*60)
    print("VERIFICATION COMPLETE: Next-hop memory stack successfully generated:")
    print(json.dumps(active_memory_now, indent=2))
    print("="*60)