import json
import os
import sys
from typing import Dict, Any, List, Tuple

# Mock or lightweight client wrapper to ensure standalone execution.
# In production, replace with: from openai import OpenAI
class MockLLMClient:
    """
    A deterministic mock client mimicking structured LLM function-calling outputs.
    Allows testing the entire execution loop, self-correction, and state mutation
    without needing active cloud API credentials or network connections.
    """
    def __init__(self):
        self.call_count = 0

    def generate_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        self.call_count += 1
        last_message = messages[-1]["content"] if messages else ""
        
        # Scenario A: Simulated Tool Failure & Self-Correction Test
        if "FAILED" in last_message and self.call_count < 3:
            return json.dumps({
                "action": "execute_tool",
                "tool_name": "format_complaint",
                "tool_args": {"raw_text": "Fixed: Customer is upset about a late shipment."}
            })
            
        # Scenario B: Initial Tool Call
        if self.call_count == 1:
            return json.dumps({
                "action": "execute_tool",
                "tool_name": "format_complaint",
                "tool_args": {"invalid_key_to_trigger_error": "This will break intentionally"}
            })
            
        # Scenario C: Final Valid Output
        return json.dumps({
            "action": "complete_node",
            "output_data": {
                "category": "shipping_delay",
                "priority": "high",
                "summary": "Customer shipment delayed by 5 days. Needs immediate tracking review."
            }
        })


# --- Mock Tool Registry Implementation ---
def tool_format_complaint(raw_text: str) -> Dict[str, Any]:
    if "Fixed" not in raw_text:
        raise ValueError("Missing required operational string pattern context.")
    return {"status": "success", "processed_text": raw_text.strip()}

TOOL_REGISTRY = {
    "format_complaint": tool_format_complaint
}


# --- Core Agentic Node Runtime Engine ---
class AgenticNodeRuntime:
    def __init__(self, node_id: str, system_persona: str, max_retries: int = 5):
        self.node_id = node_id
        self.system_persona = system_persona
        self.max_retries = max_retries
        self.llm = MockLLMClient()  # Swap with actual API instance in production

    def execute(self, inbound_context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Executes the probabilistic reasoning loop for a single workflow node block.
        """
        print(f"[Node {self.node_id}] Initiating execution loop...")
        
        # 1. Hydrate Local Agent Memory & Context state
        agent_memory_log: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_persona},
            {"role": "user", "content": f"Inbound Context Payload: {json.dumps(inbound_context)}"}
        ]
        
        execution_depth = 0
        
        # 2. Main Probabilistic Reasoning Loop
        while execution_depth < self.max_retries:
            execution_depth += 1
            print(f"\n[Depth {execution_depth}/{self.max_retries}] Computing next action...")
            
            # Compute Next Action (Simulated or Real LLM Inference Cycle)
            response_string = self.llm.generate_chat_completion(agent_memory_log)
            
            # Commit raw response into local scratchpad memory array
            agent_memory_log.append({"role": "assistant", "content": response_string})
            
            try:
                # Structure parsing validation check
                parsed_response = json.loads(response_string)
                action_type = parsed_response.get("action")
                
                # Branch A: Agent requests a Tool execution
                if action_type == "execute_tool":
                    tool_name = parsed_response.get("tool_name")
                    tool_args = parsed_response.get("tool_args", {})
                    
                    print(f" -> Action Identified: Tool Invocation [{tool_name}]")
                    
                    if tool_name not in TOOL_REGISTRY:
                        raise LookupError(f"Requested tool '{tool_name}' is missing from the Registry.")
                    
                    # Execute tool natively (Zero-Knowledge reference parsing occurs here in Step 4)
                    tool_result = TOOL_REGISTRY[tool_name](**tool_args)
                    
                    # Append response straight to localized context memory
                    agent_memory_log.append({
                        "role": "user", 
                        "content": f"Tool Execution [{tool_name}] Result: {json.dumps(tool_result)}"
                    })
                    print(f" -> Tool execution succeeded. Appending output to local scratchpad.")
                
                # Branch B: Agent claims node completion target met
                elif action_type == "complete_node":
                    output_data = parsed_response.get("output_data", {})
                    print(f" -> Action Identified: Node Target Met. Terminating execution path successfully.")
                    
                    # Return final status and mutation payload maps to caller
                    return "success", output_data
                
                # Branch C: Internal Cognitive Pause requested
                elif action_type == "paused_human":
                    print(f" -> Action Identified: Cognitive Intercept Triggered (sys_human_intervention).")
                    return "awaiting_human", {"memory_snapshot": agent_memory_log}
                    
                else:
                    raise ValueError(f"Unknown or unstructured execution routing action type: '{action_type}'")
                    
            except Exception as e:
                # --- The Self-Correction Engine Circuit ---
                error_message = f"EXECUTION_FAILED: Exception type [{type(e).__name__}]. Error Context Details: {str(e)}"
                print(f" -> ERROR encountered: {error_message}")
                print(f" -> Activating Self-Correction Loop routing protocols...")
                
                # Feed error traces right back to the agent memory frame to rewrite steps
                correction_prompt = (
                    f"Your previous action failed with structural errors. Analyze this trace and alter inputs: "
                    f"{error_message}. You must correct your schema parameters or payload formatting rules."
                )
                agent_memory_log.append({"role": "user", "content": correction_prompt})
        
        # Max depths exceeded loop breakout crash handling
        print(f"\n[CRITICAL] Maximum retry depth configuration limit of {self.max_retries} breached without resolutions.")
        return "failed", {"error_stack": f"Execution loop collapsed due to excessive structural mutations across {execution_depth} attempts."}


# --- Standalone Verification Driver Routine ---
if __name__ == "__main__":
    # Standard engineering debug flags
    os.environ["DEV_MODE"] = "true"
    
    test_persona = (
        "You are an AI triage coordinator. Your objective is to process incoming strings, "
        "format raw strings cleanly using the tool 'format_complaint', and classify output parameters. "
        "You must return clear JSON schemas matching { 'action': 'execute_tool' | 'complete_node', ... }"
    )
    
    # Initialize standalone node infrastructure
    runtime = AgenticNodeRuntime(node_id="NODE_TRIAGE_01", system_persona=test_persona, max_retries=5)
    
    # Execute with dirty raw inbound user information
    mock_inbound = {"email_body": "Hey!! My order is totally missing, tracking hasn't updated in forever fix it!"}
    final_status, state_mutation = runtime.execute(mock_inbound)
    
    print("\n" + "="*40)
    print("FINAL RUNTSTAGE VERIFICATION SUMMARY:")
    print(f"Status Target: {final_status}")
    print(f"Mutated State Output: {json.dumps(state_mutation, indent=2)}")
    print("="*40)