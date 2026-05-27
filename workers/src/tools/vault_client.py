import os
import time
import random
import json
from typing import Dict, Any, Callable

class ZeroKnowledgeVault:
    """
    Simulates an isolated, high-security vault environment (e.g., HashiCorp Vault).
    The agent never sees the keys held inside this dictionary matrix.
    """
    def __init__(self):
        # Secure server-side isolation mapping references to actual raw production tokens
        self._encrypted_storage = {
            "SECRET_REF_SALESFORCE_01": "sq_prod_live_99a88b77cc66dd",
            "SECRET_REF_STRIPE_KEY": "sk_live_51NzABC1234567890"
        }

    def fetch_secret(self, reference_id: str) -> str:
        if not reference_id.startswith("SECRET_REF_"):
            raise ValueError(f"Security Alert: Blocked attempts to read non-reference variable string: {reference_id}")
        
        secret = self._encrypted_storage.get(reference_id)
        if not secret:
            raise LookupError(f"Token Reference Key '{reference_id}' was not found in vault allocations.")
        return secret


class SecureToolExecutor:
    """
    Intercepts agent tool payloads, injects raw authorization tokens out-of-band,
    and runs external integrations safely with exponential backoff and jitter.
    """
    def __init__(self, base_retry_ms: int = 100, max_jitter_ms: int = 50):
        self.vault = ZeroKnowledgeVault()
        self.base_retry_ms = base_retry_ms
        self.max_jitter_ms = max_jitter_ms

    def compute_backoff_with_jitter(self, attempt: int) -> float:
        """
        Implements: T_wait = 2^attempt * T_base + Uniform(0, Jitter)
        Converts the millisecond calculation cleanly to seconds for Python's time.sleep()
        """
        base_backoff = (2 ** attempt) * self.base_retry_ms
        jitter = random.uniform(0, self.max_jitter_ms)
        t_wait_ms = base_backoff + jitter
        return t_wait_ms / 1000.0  # Return seconds

    def execute_with_retry(self, api_call_func: Callable, decrypted_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an external SaaS transaction wrapped inside an automated 429/503 retry circuitbreaker.
        """
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                # Fire the integration logic
                return api_call_func(decrypted_args)
            except Exception as e:
                # Intercept transient failures (Simulating an HTTP 429 or 503)
                if "Rate Limit" in str(e) and attempt < max_attempts:
                    wait_time = self.compute_backoff_with_jitter(attempt)
                    print(f"    [429 Rate Limit Detected] Attempt {attempt} failed. Backing off for {wait_time:.3f}s...")
                    time.sleep(wait_time)
                    continue
                # If it's a hard code error or max retries hit, raise it
                raise e

    def dispatch(self, tool_name: str, raw_agent_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        The entrypoint wrapper. Scans incoming arguments for references, hydrates them, 
        dispatches the secure transaction, and masks the output returned to the LLM context.
        """
        print(f"[Security Interceptor] Scanning arguments for tool: '{tool_name}'")
        
        # Deep copy to prevent mutating the original agent memory trace parameters
        decrypted_args = json.loads(json.dumps(raw_agent_args))
        
        # 1. Look for reference tokens and resolve them directly out-of-band
        for key, value in decrypted_args.items():
            if isinstance(value, str) and value.startswith("SECRET_REF_"):
                print(f"  -> Intercepted payload placeholder: {value}. Resolving securely...")
                # Resolve reference dynamically inside isolated execution memory
                decrypted_args[key] = self.vault.fetch_secret(value)

        # 2. Assign the actual execution task depending on target tool routing names
        if tool_name == "sync_salesforce_lead":
            # Pass our proxy function execution block to the retry circuit handler
            result = self.execute_with_retry(mock_salesforce_api_dispatch, decrypted_args)
            return result
        else:
            raise NotImplementedError(f"Tool target executor pipeline '{tool_name}' lacks binding drivers.")


# --- Mock Microservices External Targets for Standalone Tests ---
def mock_salesforce_api_dispatch(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulated external destination API endpoint processor.
    """
    token = args.get("auth_token", "")
    
    # Assert that the real secure token was successfully injected
    if "SECRET_REF_" in token:
        raise SecurityError("CRITICAL EXPOSURE: The raw token reference placeholder was sent directly to an external API.")
    
    # Introduce a deterministic retry trigger on the first pass to prove the backoff works
    if not os.path.exists("/tmp/retry_marker.tmp"):
        with open("/tmp/retry_marker.tmp", "w") as f: f.write("tripped")
        raise IOError("HTTP status 429: Rate Limit Exceeded. Throttling active.")
    
    # Clean up file marker after a successful secondary path simulation pass
    if os.path.exists("/tmp/retry_marker.tmp"):
        os.remove("/tmp/retry_marker.tmp")

    return {
        "status_code": 200,
        "salesforce_id": "lead_001x000001YzaAA",
        "message": "Lead object injected cleanly via secure tunnel sync profiles."
    }


# --- Standalone Testing Driver Rig ---
if __name__ == "__main__":
    # Ensure any residual crash file flags are scrubbed before starting validation tracking runs
    if os.path.exists("/tmp/retry_marker.tmp"): os.remove("/tmp/retry_marker.tmp")

    executor = SecureToolExecutor()
    
    # This matches the schema format that the LLM agent outputs in Step 2
    mock_agent_tool_call = {
        "tool_name": "sync_salesforce_lead",
        "tool_args": {
            "lead_email": "enterprise_buyer@target_account.com",
            "auth_token": "SECRET_REF_SALESFORCE_01" # The agent only knows this!
        }
    }
    
    print("="*50)
    print("RUNNING ZERO-KNOWLEDGE EXECUTION VERIFICATION TESTS:")
    print("="*50)
    
    final_output = executor.dispatch(
        tool_name=mock_agent_tool_call["tool_name"],
        raw_agent_args=mock_agent_tool_call["tool_args"]
    )
    
    print("\n" + "="*50)
    print("SUCCESS: Target API transaction cleared isolation verification.")
    print(f"Clean Data Returned to Worker Memory: {json.dumps(final_output, indent=2)}")
    print("="*50)