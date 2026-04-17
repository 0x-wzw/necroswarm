#!/usr/bin/env python3
"""Signal Detection — Extract entities, preferences, and patterns from messages.

Usage:
    python detect.py "Update voidtether readme and include gbrain"
    python detect.py --json "Don't ask me for approval, just execute"
    python detect.py --memory-only "I prefer autonomous execution"

Returns:
    Extracted signals with classification (HIGH/MEDIUM/LOW) and memory recommendations.
"""

import sys
import json
import re
from typing import Any


# ── Entity Patterns ─────────────────────────────────────────────────────

ENTITY_PATTERNS = {
    "github_repo": re.compile(r'\b([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)\b'),
    "url": re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
    "file_path": re.compile(r'(?:~?/[\w./-]+\.[\w]+)|(?:~?/[\w./-]+/[\w./-]*)'),
    "model_name": re.compile(r'\b(kimi-k2(?:\.5)?|deepseek-v3\.1|glm-5\.1|qwen3-coder|minimax-m2\.5|mistral-large-3|devstral-2|gemma[34]?|nemotron|ministral)\b', re.IGNORECASE),
    "tool_name": re.compile(r'\b(gh|himalaya|mcporter|git|docker|python|node|npm|curl)\b'),
    "project_name": re.compile(r'\b(VoidTether|NecroSwarm|HyperFrames?|OpenClaw|Hermes|clawXiv)\b', re.IGNORECASE),
    "tech_concept": re.compile(r'\b(JSON-RPC|MCP|A2A|LLM|RAG|FTS5|RRF|API|REST|gRPC|WebSocket)\b'),
}


# ── Preference Patterns ────────────────────────────────────────────────

PREFERENCE_PATTERNS = [
    (re.compile(r"(?:I prefer|I like|my preference|I'd rather)\s+(.+)", re.IGNORECASE), "preference"),
    (re.compile(r"(?:don't|do not|never|stop)\s+(?:ask|prompt|request)\s+(?:me\s+)?(?:for\s+)?(.+)", re.IGNORECASE), "correction"),
    (re.compile(r"(?:always|must|should|need to)\s+(.+)", re.IGNORECASE), "directive"),
    (re.compile(r"(?:that worked|that's perfect|great job|nice)\b", re.IGNORECASE), "praise"),
    (re.compile(r"(?:this keeps|keeps on|again|still)\s+(.+)", re.IGNORECASE), "frustration"),
    (re.compile(r"(?:actually|rather|instead)\s+(.+)", re.IGNORECASE), "correction"),
]


# ── Memory Decision Matrix ─────────────────────────────────────────────

MEMORY_RULES = {
    "HIGH": {
        "patterns": ["preference", "correction", "directive"],
        "action": "SAVE immediately to memory",
        "examples": [
            "User prefers autonomous execution",
            "Don't ask for approval, just execute",
            "Always add MIT license to repos",
        ],
    },
    "MEDIUM": {
        "patterns": ["praise", "entity_project", "entity_model"],
        "action": "SAVE to memory if durable, skip if transient",
        "examples": [
            "VoidTether is the agent interop project",
            "glm-5.1 is the default model",
        ],
    },
    "LOW": {
        "patterns": ["frustration", "entity_file", "entity_url"],
        "action": "SKIP — will resurface if important",
        "examples": [
            "This keeps failing",
            "File path mentioned once",
        ],
    },
}


def detect_entities(text: str) -> list[dict[str, Any]]:
    """Extract named entities from text."""
    entities = []
    seen = set()
    
    for entity_type, pattern in ENTITY_PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group(0)
            key = f"{entity_type}:{value}"
            if key not in seen:
                seen.add(key)
                entities.append({
                    "type": entity_type,
                    "value": value,
                    "position": match.start(),
                })
    
    return entities


def detect_preferences(text: str) -> list[dict[str, Any]]:
    """Extract preference and correction signals from text."""
    preferences = []
    
    for pattern, signal_type in PREFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            captured = match.group(1) if match.lastindex else match.group(0)
            preferences.append({
                "type": signal_type,
                "text": match.group(0),
                "captured": captured,
                "position": match.start(),
            })
    
    return preferences


def classify_signals(entities: list[dict], preferences: list[dict]) -> list[dict[str, Any]]:
    """Classify all signals by memory priority."""
    signals = []
    
    # Classify entities
    for entity in entities:
        etype = entity["type"]
        if etype in ("project_name", "model_name"):
            priority = "MEDIUM"
        elif etype in ("url", "file_path"):
            priority = "LOW"
        else:
            priority = "LOW"
        
        signals.append({
            "kind": "entity",
            "type": etype,
            "value": entity["value"],
            "priority": priority,
            "memory_action": MEMORY_RULES[priority]["action"],
        })
    
    # Classify preferences
    for pref in preferences:
        ptype = pref["type"]
        if ptype in ("preference", "correction", "directive"):
            priority = "HIGH"
        elif ptype == "praise":
            priority = "MEDIUM"
        elif ptype == "frustration":
            priority = "LOW"
        else:
            priority = "LOW"
        
        # Generate memory save suggestion for HIGH priority
        save_suggestion = None
        if priority == "HIGH":
            # Create a concise memory-worthy fact
            captured = pref.get("captured", pref["text"])
            save_suggestion = captured.strip().rstrip(".")
        
        signals.append({
            "kind": "preference",
            "type": ptype,
            "value": pref["text"],
            "priority": priority,
            "memory_action": MEMORY_RULES[priority]["action"],
            "save_suggestion": save_suggestion,
        })
    
    # Sort by priority (HIGH first, then MEDIUM, then LOW)
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    signals.sort(key=lambda s: priority_order.get(s["priority"], 3))
    
    return signals


def detect(text: str, json_output: bool = False) -> dict:
    """Run full signal detection on text.
    
    Args:
        text: Input message to analyze.
        json_output: If True, return JSON. If False, return human-readable.
    
    Returns:
        Detection results with entities, preferences, signals, and memory actions.
    """
    entities = detect_entities(text)
    preferences = detect_preferences(text)
    signals = classify_signals(entities, preferences)
    
    high_signals = [s for s in signals if s["priority"] == "HIGH"]
    medium_signals = [s for s in signals if s["priority"] == "MEDIUM"]
    low_signals = [s for s in signals if s["priority"] == "LOW"]
    
    memory_saves = [
        s["save_suggestion"] for s in high_signals if s.get("save_suggestion")
    ]
    
    return {
        "input": text,
        "entities": entities,
        "preferences": preferences,
        "signals": signals,
        "summary": {
            "total_signals": len(signals),
            "high": len(high_signals),
            "medium": len(medium_signals),
            "low": len(low_signals),
        },
        "memory_actions": {
            "save_now": memory_saves,
            "consider_saving": [s["value"] for s in medium_signals],
            "skip": [s["value"] for s in low_signals],
        },
    }


def format_human(result: dict) -> str:
    """Format result as human-readable text."""
    lines = []
    lines.append(f"👁️ Signal Detection: \"{result['input'][:80]}{'...' if len(result['input']) > 80 else ''}\"")
    lines.append("")
    
    summary = result["summary"]
    lines.append(f"Signals: {summary['total_signals']} total "
                 f"(🔴 {summary['high']} HIGH / 🟡 {summary['medium']} MEDIUM / ⚪ {summary['low']} LOW)")
    
    # Show HIGH priority signals
    high_signals = [s for s in result["signals"] if s["priority"] == "HIGH"]
    if high_signals:
        lines.append("")
        lines.append("🔴 HIGH PRIORITY (save to memory):")
        for s in high_signals:
            lines.append(f"  • {s['kind']}/{s['type']}: \"{s['value']}\"")
            if s.get("save_suggestion"):
                lines.append(f"    → Save: \"{s['save_suggestion']}\"")
    
    # Show MEDIUM priority signals
    medium_signals = [s for s in result["signals"] if s["priority"] == "MEDIUM"]
    if medium_signals:
        lines.append("")
        lines.append("🟡 MEDIUM PRIORITY (consider saving):")
        for s in medium_signals:
            lines.append(f"  • {s['kind']}/{s['type']}: \"{s['value']}\"")
    
    # Show LOW priority signals (brief)
    low_signals = [s for s in result["signals"] if s["priority"] == "LOW"]
    if low_signals:
        lines.append("")
        lines.append(f"⚪ LOW PRIORITY ({len(low_signals)} signals, skip):")
        for s in low_signals[:5]:  # Show max 5
            lines.append(f"  • {s['kind']}/{s['type']}: \"{s['value']}\"")
        if len(low_signals) > 5:
            lines.append(f"  ... and {len(low_signals) - 5} more")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python detect.py \"<message>\" [--json]", file=sys.stderr)
        print("Example: python detect.py \"I prefer autonomous execution\"", file=sys.stderr)
        sys.exit(1)
    
    text = sys.argv[1]
    json_output = "--json" in sys.argv
    
    result = detect(text, json_output=json_output)
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))


if __name__ == "__main__":
    main()