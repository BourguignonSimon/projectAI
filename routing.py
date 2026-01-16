"""
Routing module for the orchestrator.

This module provides a dedicated Redis channel on port 6381 for routing decisions.
The orchestrator uses this channel to decide which agent should handle each request.
"""

import os
import json
import redis
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Routing Redis connection on port 6381
ROUTING_PORT = int(os.getenv("REDIS_ROUTING_PORT", 6381))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

routing_redis = redis.Redis(
    host=REDIS_HOST,
    port=ROUTING_PORT,
    decode_responses=True
)

# Routing stream key
ROUTING_STREAM_KEY = "routing_decisions_stream"

# Agent registry with capabilities and priorities
AGENT_REGISTRY = {
    "analyst": {
        "capabilities": ["requirements", "analysis", "specifications", "user_input"],
        "priority": 1,
        "description": "Extracts requirements and specifications from user input",
        "triggers": ["new_request", "clarification_needed", "requirements_update"]
    },
    "architect": {
        "capabilities": ["design", "architecture", "structure", "planning"],
        "priority": 2,
        "description": "Designs system architecture and file structure",
        "triggers": ["specs_ready", "design_update", "restructure"]
    },
    "coder": {
        "capabilities": ["implementation", "coding", "development", "fix"],
        "priority": 3,
        "description": "Implements code based on architecture",
        "triggers": ["architecture_ready", "code_fix_needed", "implementation"]
    },
    "reviewer": {
        "capabilities": ["review", "audit", "quality", "validation"],
        "priority": 4,
        "description": "Reviews and validates code quality",
        "triggers": ["code_ready", "review_needed", "validation"]
    }
}

# Routing rules based on workflow state
ROUTING_RULES = {
    "user": {
        "default_target": "analyst",
        "description": "User input should go to analyst for requirements extraction"
    },
    "analyst": {
        "default_target": "architect",
        "description": "Analyst output should go to architect for design"
    },
    "architect": {
        "default_target": "coder",
        "description": "Architecture should go to coder for implementation"
    },
    "coder": {
        "default_target": "reviewer",
        "description": "Code should go to reviewer for validation"
    },
    "reviewer": {
        "conditions": {
            "VALIDATED": "finish",
            "default": "coder"
        },
        "description": "Reviewer validates or sends back to coder for fixes"
    }
}


def get_routing_connection():
    """Get the routing Redis connection."""
    return routing_redis


def publish_routing_decision(request_id, source_agent, target_agent, reason, metadata=None):
    """
    Publish a routing decision to the routing stream.

    Args:
        request_id: The request identifier
        source_agent: The agent that produced the current output
        target_agent: The agent that should handle the next step
        reason: The reason for this routing decision
        metadata: Optional additional metadata
    """
    decision = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or "",
        "source_agent": source_agent,
        "target_agent": target_agent,
        "reason": reason,
        "metadata": json.dumps(metadata) if metadata else "{}"
    }
    routing_redis.xadd(ROUTING_STREAM_KEY, decision)
    return decision


def get_routing_history(request_id, count=50):
    """
    Get routing history for a specific request.

    Args:
        request_id: The request identifier
        count: Maximum number of entries to retrieve

    Returns:
        List of routing decisions for the request
    """
    messages = routing_redis.xrevrange(ROUTING_STREAM_KEY, count=count)
    history = []
    for msg_id, data in messages:
        if data.get("request_id") == request_id:
            history.append({
                "id": msg_id,
                "timestamp": data.get("timestamp"),
                "source": data.get("source_agent"),
                "target": data.get("target_agent"),
                "reason": data.get("reason")
            })
    return history


def get_agent_capabilities(agent_name):
    """Get the capabilities of a specific agent."""
    agent = AGENT_REGISTRY.get(agent_name.lower())
    if agent:
        return agent.get("capabilities", [])
    return []


def get_suitable_agents(task_type):
    """
    Find suitable agents for a given task type.

    Args:
        task_type: The type of task (e.g., "coding", "review", "analysis")

    Returns:
        List of agent names sorted by priority
    """
    suitable = []
    for agent_name, agent_info in AGENT_REGISTRY.items():
        if task_type.lower() in agent_info["capabilities"]:
            suitable.append((agent_name, agent_info["priority"]))

    # Sort by priority (lower is higher priority)
    suitable.sort(key=lambda x: x[1])
    return [agent[0] for agent in suitable]


def determine_next_agent(source_agent, content):
    """
    Determine the next agent based on routing rules and content analysis.

    Args:
        source_agent: The agent that produced the current output
        content: The content of the message

    Returns:
        Tuple of (target_agent, reason)
    """
    source = source_agent.lower()
    rule = ROUTING_RULES.get(source)

    if not rule:
        return "analyst", "Unknown source, defaulting to analyst"

    # Check for conditional routing (like reviewer)
    if "conditions" in rule:
        for condition, target in rule["conditions"].items():
            if condition == "default":
                continue
            if condition.upper() in content.upper():
                return target, f"Condition '{condition}' matched in content"
        return rule["conditions"]["default"], "Default condition applied"

    return rule["default_target"], rule["description"]


def register_routing_decision(request_id, source, target, content_summary):
    """
    Register a routing decision with full context.

    This function logs the decision to the routing stream and returns
    the formatted target for use by the manager.

    Args:
        request_id: The request identifier
        source: Source agent
        target: Target agent
        content_summary: Brief summary of the content being routed

    Returns:
        Formatted target string (e.g., "@Analyst")
    """
    if target == "finish":
        publish_routing_decision(
            request_id=request_id,
            source_agent=source,
            target_agent="FINISH",
            reason="Workflow completed - validation passed",
            metadata={"content_summary": content_summary[:100]}
        )
        return "FINISH"

    formatted_target = f"@{target.capitalize()}"
    publish_routing_decision(
        request_id=request_id,
        source_agent=source,
        target_agent=target,
        reason=f"Routing from {source} to {target}",
        metadata={"content_summary": content_summary[:100] if content_summary else ""}
    )
    return formatted_target


def get_workflow_state(request_id):
    """
    Get the current workflow state for a request.

    Returns information about:
    - Current stage in the workflow
    - Agents that have participated
    - Number of routing decisions made

    Args:
        request_id: The request identifier

    Returns:
        Dictionary with workflow state information
    """
    history = get_routing_history(request_id, count=100)

    if not history:
        return {
            "stage": "initial",
            "participating_agents": [],
            "decision_count": 0,
            "last_agent": None
        }

    agents_seen = set()
    for entry in history:
        if entry.get("source"):
            agents_seen.add(entry["source"])
        if entry.get("target") and entry["target"] != "FINISH":
            agents_seen.add(entry["target"])

    # Most recent entry is first (xrevrange)
    last_entry = history[0] if history else None

    return {
        "stage": last_entry.get("target", "unknown") if last_entry else "initial",
        "participating_agents": list(agents_seen),
        "decision_count": len(history),
        "last_agent": last_entry.get("target") if last_entry else None
    }


def clear_routing_history(request_id=None):
    """
    Clear routing history.

    Args:
        request_id: If provided, only clear history for this request.
                   If None, clear all routing history.
    """
    if request_id is None:
        routing_redis.delete(ROUTING_STREAM_KEY)
    else:
        # For specific request, we'd need to filter - not directly supported
        # by Redis streams, so we just log a note
        pass


def check_routing_connection():
    """Check if the routing Redis connection is available."""
    try:
        routing_redis.ping()
        return True
    except redis.ConnectionError:
        return False
