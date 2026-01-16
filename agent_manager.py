import json
import os
import re
import time
import uuid

from utils import STREAM_KEY, build_smart_context, get_ai_response, publish_message, r
from routing import (
    determine_next_agent,
    register_routing_decision,
    get_workflow_state,
    publish_routing_decision,
    check_routing_connection,
    AGENT_REGISTRY,
)


def get_last_coder_content(request_id):
    """Retrieve the last coder message content from the stream for a given request."""
    if not request_id:
        return ""
    messages = r.xrevrange(STREAM_KEY, count=100)
    for msg_id, data in messages:
        if data.get("request_id") == request_id and data.get("sender") == "coder":
            return data.get("content", "")
    return ""


def save_artifacts(content, request_id):
    pattern = r"```python(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)
    saved_files = []
    if matches:
        if not os.path.exists("livrables"):
            os.makedirs("livrables")
        for idx, code in enumerate(matches):
            filename = f"livrables/projet_{request_id[:8]}_script_{idx+1}.py"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code.strip())
            saved_files.append(filename)
    return saved_files


def decide_next_step(sender, content, request_id):
    """
    Enhanced routing decision using the routing module.

    This function uses both rule-based routing and AI-assisted routing
    to determine the next agent in the workflow.
    """
    # Quick check for validation completion
    if sender == "reviewer" and "VALIDATED" in content:
        # Log the routing decision to the routing stream
        register_routing_decision(
            request_id=request_id,
            source=sender,
            target="finish",
            content_summary=content[:100]
        )
        return "FINISH", "OK"

    # Get workflow state for context
    workflow_state = get_workflow_state(request_id)

    # First, try rule-based routing for deterministic flow
    rule_target, rule_reason = determine_next_agent(sender, content)

    # Build context for AI-assisted routing decision
    smart_context = build_smart_context(request_id)

    # Get available agents information for the AI
    agents_info = "\n".join([
        f"- @{name.capitalize()}: {info['description']}"
        for name, info in AGENT_REGISTRY.items()
    ])

    system_prompt = f"""
    ROLE: Intelligent Workflow Router.
    GOAL: Route the request to the most appropriate agent.

    AVAILABLE AGENTS:
    {agents_info}

    WORKFLOW STATE:
    - Current Stage: {workflow_state.get('stage', 'initial')}
    - Agents Involved: {', '.join(workflow_state.get('participating_agents', []))}
    - Decision Count: {workflow_state.get('decision_count', 0)}

    ROUTING RULES:
    1. User Input -> @Analyst (Extract Requirements)
    2. Specifications -> @Architect (Design System)
    3. Architecture -> @Coder (Implement Code)
    4. Code -> @Reviewer (Quality Audit)
    5. Review Fail -> @Coder (Fix Issues)
    6. Review Pass -> FINISH

    SUGGESTED ROUTE: {rule_target} - {rule_reason}

    OUTPUT: JSON {{"target": "@Role", "instruction": "Direct Command for the agent"}}
    """

    user_prompt = f"""
    STATE: {smart_context}
    LAST_EVENT: {sender} completed their task.
    DETERMINE NEXT STEP.
    """

    try:
        response = get_ai_response("manager", user_prompt, system_prompt)
        clean_json = response.replace("```json", "").replace("```", "").strip()
        decision = json.loads(clean_json)
        target = decision["target"]
        instruction = decision["instruction"]

        # Register the routing decision
        register_routing_decision(
            request_id=request_id,
            source=sender,
            target=target.replace("@", "").lower(),
            content_summary=content[:100] if content else ""
        )

        return target, instruction
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Decision parsing error: {e}, using rule-based routing")
        # Fallback to rule-based routing
        formatted_target = register_routing_decision(
            request_id=request_id,
            source=sender,
            target=rule_target,
            content_summary=content[:100] if content else ""
        )
        return formatted_target, f"Process the input from {sender}"


def run_manager():
    print("MANAGER (INDUSTRIAL MODE)")

    # Check routing Redis connection
    if check_routing_connection():
        print("Routing Redis (port 6381): Connected")
    else:
        print("Warning: Routing Redis (port 6381) not available, using fallback routing")

    last_id = "$"

    while True:
        try:
            messages = r.xread({STREAM_KEY: last_id}, count=1, block=5000)
            if messages:
                stream, msgs = messages[0]
                last_id = msgs[0][0]
                data = msgs[0][1]

                sender = data.get("sender", "")
                req_id = data.get("request_id")
                status = data.get("status", "DONE")

                if status != "DONE":
                    continue

                if sender == "user" and not req_id:
                    new_guid = str(uuid.uuid4())
                    print(f"[NEW JOB] {new_guid}")
                    publish_message(
                        "manager",
                        f"EXECUTE: {data['content']}",
                        "cmd",
                        request_id=new_guid,
                        status="DONE",
                    )

                elif req_id and sender != "manager":
                    target, instruction = decide_next_step(sender, data["content"], req_id)

                    if target == "FINISH":
                        coder_content = get_last_coder_content(req_id)
                        files = save_artifacts(coder_content, req_id)
                        publish_message(
                            "manager", f"DONE. Files: {len(files)}", "end", req_id, status="DONE"
                        )
                    else:
                        print(f"[ROUTING] -> {target}")
                        publish_message("manager", instruction, "cmd", req_id, status="DONE")
        except Exception as e:
            print(f"Err: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_manager()
