import json
import os
import re
import time
import uuid

from utils import STREAM_KEY, build_smart_context, get_ai_response, publish_message, r


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
    if sender == "reviewer" and "VALIDATED" in content:
        return "FINISH", "OK"

    smart_context = build_smart_context(request_id)

    system_prompt = """
    ROLE: Workflow Logic Router.
    GOAL: Move ticket to next stage.
    STATES: 
    1. User Input -> @Analyst (Get Specs)
    2. Specs -> @Architect (Get Plan)
    3. Plan -> @Coder (Get Code)
    4. Code -> @Reviewer (Audit)
    5. Review Fail -> @Coder (Fix)
    6. Review Pass -> FINISH
    
    OUTPUT: JSON {"target": "@Role", "instruction": "Direct Command"}
    """

    user_prompt = f"""
    STATE: {smart_context}
    LAST_EVENT: {sender} sent data.
    NEXT STEP?
    """

    try:
        response = get_ai_response("manager", user_prompt, system_prompt)
        clean_json = response.replace("```json", "").replace("```", "").strip()
        decision = json.loads(clean_json)
        return decision["target"], decision["instruction"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Decision parsing error: {e}")
        return "@Analyst", "Analyze status."


def run_manager():
    print("🤖 MANAGER (MODE INDUSTRIEL)")
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
                    print(f"✨ NEW JOB: {new_guid}")
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
                        print(f"👉 {target}")
                        publish_message("manager", instruction, "cmd", req_id, status="DONE")
        except Exception as e:
            print(f"Err: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_manager()
