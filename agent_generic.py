import argparse
import time

from utils import STREAM_KEY, build_smart_context, get_ai_response, publish_message, r

ROLES_CONFIG = {
    "analyst": """
    ROLE: Tech Analyst.
    OUTPUT: Markdown List ONLY.
    CONTENT: 1. Goal, 2. Tech Constraints, 3. Features (Must-Have).
    CONSTRAINTS: No intro/outro. Dense info.
    """,
    "architect": """
    ROLE: Architect.
    OUTPUT: Markdown File Tree & Stack.
    CONTEXT: Python, WSL.
    CONSTRAINTS: No explanations. Just structure.
    """,
    "coder": """
    ROLE: Python Dev.
    OUTPUT: Full Code in ```python ... ``` blocks.
    CONSTRAINTS: 
    - NO EXPLANATIONS.
    - NO "Here is the code".
    - Include comments in code.
    """,
    "reviewer": """
    ROLE: Auditor.
    OUTPUT: "VALIDATED" if good. Bullet list of fixes if bad.
    CONSTRAINTS: Strict.
    """,
}


def run_agent(role):
    print(f"👤 AGENT {role.upper()} (SILENT MODE)", flush=True)
    system_prompt = ROLES_CONFIG.get(role, "")
    my_tag = f"@{role.capitalize()}"
    last_id = "$"

    while True:
        try:
            messages = r.xread({STREAM_KEY: last_id}, count=1, block=5000)
            if messages:
                stream, msgs = messages[0]
                last_id = msgs[0][0]
                data = msgs[0][1]

                sender = data.get("sender", "")
                content = data.get("content", "")
                req_id = data.get("request_id")
                status = data.get("status", "DONE")

                if sender != role and my_tag in content and req_id and status == "DONE":
                    print(f"⚡ [{role}] Processing...", flush=True)

                    if role == "reviewer":
                        context = f"CODE:\n{content}\nROLE:{system_prompt}"
                    else:
                        smart = build_smart_context(req_id)
                        context = f"CTX:\n{smart}\nIN:\n{content}\nROLE:{system_prompt}"

                    response = get_ai_response(role, content, context)
                    msg_type = "code" if role == "coder" else "data"

                    publish_message(role, response, msg_type, req_id, status="DONE")
                    print(f"✅ [{role}] Sent.", flush=True)
        except Exception as e:
            print(f"Err {role}: {e}", flush=True)
            time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True)
    args = parser.parse_args()
    run_agent(args.role)
