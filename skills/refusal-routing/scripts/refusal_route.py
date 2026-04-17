#!/usr/bin/env python3
"""Refusal Routing — Per-task model fallback chain within Ollama Cloud.

Detects refusals, timeouts, and errors in model output and routes to the
next model in the fallback chain. Designed to be called after each model
attempt in a NecroSwarm council deliberation.

Usage:
    python refusal_route.py --task complex --model "kimi-k2.5:cloud" --response "I cannot help with..."
    python refusal_route.py --task code --model "qwen3-coder:480b:cloud" --error "timeout"
    python refusal_route.py --chain moderate

Returns:
    Next model to try, or final failure verdict.
"""

import sys
import json
import argparse


# ── Refusal Detection ──────────────────────────────────────────────────

REFUSAL_PATTERNS = [
    "i cannot",
    "i can't",
    "i'm unable",
    "i'm not able",
    "i apologize but",
    "as an ai",
    "as a language model",
    "i must decline",
    "against my guidelines",
    "not appropriate",
    "content policy",
    "i won't be able to",
    "i'm not going to",
    "i'm sorry, but i can't",
    "against my",
    "ethical guidelines",
    "harmful or",
]

DEAD_MODELS = ["qwen3.5:cloud"]  # Permanently dead, skip immediately

EMPTY_RESPONSE_THRESHOLD = 20  # Characters below this = suspiciously short


def is_refusal(response: str) -> bool:
    """Check if a model response is a refusal."""
    lower = response.strip().lower()
    if len(lower) < EMPTY_RESPONSE_THRESHOLD:
        return True  # Suspiciously short
    return any(pattern in lower for pattern in REFUSAL_PATTERNS)


def classify_error(error_type: str, response: str = "") -> str:
    """Classify the type of failure.
    
    Returns: REFUSAL, TIMEOUT, EMPTY, ERROR, or DEAD_MODEL
    """
    if error_type == "dead_model":
        return "DEAD_MODEL"
    
    if error_type == "timeout":
        return "TIMEOUT"
    
    if error_type == "empty" or (response and len(response.strip()) < EMPTY_RESPONSE_THRESHOLD):
        return "EMPTY"
    
    if error_type == "error":
        return "ERROR"
    
    # Check for refusal in response text
    if response and is_refusal(response):
        return "REFUSAL"
    
    return "UNKNOWN"


# ── Fallback Chains ────────────────────────────────────────────────────

FALLBACK_CHAINS = {
    "complex": [
        "kimi-k2.5:cloud",
        "deepseek-v3.1:671b:cloud",
        "glm-5.1:cloud",
        "devstral-2:123b:cloud",
    ],
    "moderate": [
        "minimax-m2.5:cloud",
        "mistral-large-3:675b:cloud",
        "glm-5.1:cloud",
    ],
    "simple": [
        "gemma3:27b:cloud",
        "glm-5.1:cloud",
        "ministral-3:3b:cloud",
    ],
    "code": [
        "qwen3-coder:480b:cloud",
        "deepseek-v3.1:671b:cloud",
        "devstral-2:123b:cloud",
    ],
    "research": [
        "minimax-m2.5:cloud",
        "kimi-k2.5:cloud",
        "mistral-large-3:675b:cloud",
    ],
    "thinking": [
        "kimi-k2:1t:cloud",
        "deepseek-v3.1:671b:cloud",
        "kimi-k2.5:cloud",
    ],
}

# NecroSwarm dimension mapping — when a council seat refuses, route to an
# adjacent dimension rather than a flat list
DIMENSION_FALLBACK = {
    "D1_synthesis": ["deepseek-v3.1:671b:cloud", "glm-5.1:cloud"],
    "D2_deep_reason": ["kimi-k2.5:cloud", "glm-5.1:cloud"],
    "D3_code": ["deepseek-v3.1:671b:cloud", "devstral-2:123b:cloud"],
    "D4_vision": [],  # Vision is specialized, limited fallback
    "D5_strategy": ["kimi-k2.5:cloud", "deepseek-v3.1:671b:cloud"],
    "D6_analysis": ["kimi-k2.5:cloud", "glm-5.1:cloud"],
    "D7_general": ["kimi-k2.5:cloud", "minimax-m2.5:cloud"],
    "D8_verification": ["deepseek-v3.1:671b:cloud", "glm-5.1:cloud"],
    "D9_research": ["kimi-k2.5:cloud", "mistral-large-3:675b:cloud"],
    "D10_think": ["deepseek-v3.1:671b:cloud", "kimi-k2.5:cloud"],
}

MAX_FALLBACKS = 3


def get_next_model(
    chain_name: str,
    current_model: str,
    error_type: str = "refusal",
    dimension: str | None = None,
    response: str = "",
) -> dict:
    """Get the next model to try in the fallback chain.
    
    Args:
        chain_name: Task type (complex, moderate, simple, code, research, thinking).
        current_model: The model that just failed.
        error_type: Type of failure (refusal, timeout, empty, error, dead_model).
        dimension: Optional NecroSwarm dimension for dimension-aware routing.
        response: The model's actual response (for refusal detection).
    
    Returns:
        Dict with next_model, fallback_index, remaining_fallbacks, and verdict.
    """
    # Classify the error
    classified = classify_error(error_type, response)
    
    # Skip dead models immediately
    if current_model in DEAD_MODELS:
        classified = "DEAD_MODEL"
    
    # Use dimension-aware routing if dimension is specified
    if dimension and dimension in DIMENSION_FALLBACK:
        chain = DIMENSION_FALLBACK[dimension]
        if not chain:
            # No fallback for this dimension
            return {
                "next_model": None,
                "fallback_index": 0,
                "remaining_fallbacks": 0,
                "error_class": classified,
                "verdict": "NO_FALLBACK",
                "message": f"No fallback available for dimension {dimension}",
            }
    else:
        # Use task-type chain
        chain = FALLBACK_CHAINS.get(chain_name, FALLBACK_CHAINS["moderate"])
    
    # Find current model in chain
    try:
        current_idx = chain.index(current_model)
        next_idx = current_idx + 1
    except ValueError:
        # Current model not in chain — start from beginning
        next_idx = 0
    
    # Check if we've exhausted fallbacks
    remaining = len(chain) - next_idx
    
    if next_idx >= len(chain) or remaining <= 0:
        return {
            "next_model": None,
            "fallback_index": next_idx,
            "remaining_fallbacks": 0,
            "error_class": classified,
            "verdict": "EXHAUSTED",
            "message": f"All {len(chain)} models in '{chain_name}' chain exhausted",
        }
    
    # More than MAX_FALLBACKS means we should stop
    if next_idx >= MAX_FALLBACKS:
        return {
            "next_model": None,
            "fallback_index": next_idx,
            "remaining_fallbacks": 0,
            "error_class": classified,
            "verdict": "MAX_FALLBACKS_REACHED",
            "message": f"Maximum {MAX_FALLBACKS} fallbacks reached for '{chain_name}' chain",
        }
    
    next_model = chain[next_idx]
    
    return {
        "next_model": next_model,
        "fallback_index": next_idx,
        "remaining_fallbacks": remaining - 1,
        "error_class": classified,
        "verdict": "FALLBACK",
        "message": f"Routing from {current_model} to {next_model} ({classified})",
    }


def format_human(result: dict) -> str:
    """Format result as human-readable text."""
    lines = []
    lines.append(f"⛓️ Refusal Routing Result")
    lines.append("")
    lines.append(f"  Error class: {result['error_class']}")
    lines.append(f"  Verdict: {result['verdict']}")
    lines.append(f"  Message: {result['message']}")
    
    if result['next_model']:
        lines.append(f"  Next model: {result['next_model']}")
        lines.append(f"  Fallback index: {result['fallback_index']}")
        lines.append(f"  Remaining fallbacks: {result['remaining_fallbacks']}")
    else:
        lines.append(f"  No more fallbacks available")
        if result['verdict'] == "EXHAUSTED":
            lines.append(f"  → Accept partial results and explain limitations")
        elif result['verdict'] == "MAX_FALLBACKS_REACHED":
            lines.append(f"  → Maximum fallback depth reached")
        elif result["verdict"] == "NO_FALLBACK":
            lines.append(f"  → Specialized dimension with no generic fallback")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Refusal routing for model fallback chains")
    parser.add_argument("--task", choices=list(FALLBACK_CHAINS.keys()), default="moderate",
                        help="Task type for chain selection")
    parser.add_argument("--model", required=False, help="Current model that failed")
    parser.add_argument("--response", default="", help="Model response text (for refusal detection)")
    parser.add_argument("--error", default="refusal", 
                        choices=["refusal", "timeout", "empty", "error", "dead_model"],
                        help="Type of error")
    parser.add_argument("--dimension", required=False,
                        choices=list(DIMENSION_FALLBACK.keys()),
                        help="NecroSwarm dimension for dimension-aware routing")
    parser.add_argument("--chain", action="store_true", help="Print the full fallback chain for the task type")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Print chain if requested
    if args.chain:
        chain = FALLBACK_CHAINS[args.task]
        result = {
            "task_type": args.task,
            "chain": chain,
            "chain_length": len(chain),
            "max_fallbacks": MAX_FALLBACKS,
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"⛓️ Fallback chain for '{args.task}':")
            for i, model in enumerate(chain):
                print(f"  {i+1}. {model}")
            print(f"\nMax fallbacks: {MAX_FALLBACKS}")
        return
    
    if not args.model:
        print("Error: --model is required when not using --chain", file=sys.stderr)
        sys.exit(1)
    
    result = get_next_model(
        chain_name=args.task,
        current_model=args.model,
        error_type=args.error,
        dimension=args.dimension,
        response=args.response,
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))
    
    # Exit 0 if fallback available, 1 if exhausted
    sys.exit(0 if result["next_model"] else 1)


if __name__ == "__main__":
    main()