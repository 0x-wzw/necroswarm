#!/usr/bin/env python3
"""RESOLVER — Intent-to-skill dispatch engine.

Usage:
    python resolve.py "debug the login error"
    python resolve.py "research transformer architectures"
    python resolve.py --json "deploy model to production"

Returns:
    Matching skill name(s) and complexity rating.
    Exit 0 if match found, exit 1 if no match.
"""

import sys
import json
import re
from pathlib import Path

# ── Dispatch Table ─────────────────────────────────────────────────────
# Each entry: (intent_patterns, skill_name, category, complexity)
# Complexity: TRIVIAL, SIMPLE, MODERATE, COMPLEX

DISPATCH_TABLE = [
    # Software Development
    (["code", "implement", "build app", "create feature", "refactor"], "subagent-driven-development", "software-dev", "COMPLEX"),
    (["code review", "review code", "PR review", "review PR"], "requesting-code-review", "software-dev", "MODERATE"),
    (["debug", "error", "failing", "broken", "fix bug", "traceback", "exception"], "systematic-debugging", "software-dev", "MODERATE"),
    (["test", "write test", "TDD", "unit test"], "test-driven-development", "software-dev", "MODERATE"),
    (["plan", "spec", "requirements", "design doc"], "writing-plans", "software-dev", "SIMPLE"),
    (["agent protocol", "A2A", "voidtether", "interoperability"], "agent-interop-bridge", "software-dev", "COMPLEX"),
    (["package", "release", "publish pypi", "semver"], "python-package-release", "software-dev", "MODERATE"),
    
    # Research
    (["research", "find papers", "arxiv", "paper search"], "arxiv", "research", "SIMPLE"),
    (["monitor blog", "RSS", "feed update"], "blogwatcher", "research", "SIMPLE"),
    (["prediction market", "polymarket", "betting odds"], "polymarket", "research", "SIMPLE"),
    (["write paper", "research paper", "submit paper"], "research-paper-writing", "research", "COMPLEX"),
    
    # Media
    (["summarize video", "transcript", "youtube"], "youtube-content", "media", "SIMPLE"),
    (["generate video", "render", "html video", "animation"], "hyperframe", "creative", "MODERATE"),
    (["ASCII art", "figlet", "cowsay", "text art"], "ascii-art", "creative", "TRIVIAL"),
    (["diagram", "architecture diagram", "SVG", "system diagram"], "architecture-diagram", "creative", "MODERATE"),
    (["excalidraw", "hand-drawn diagram"], "excalidraw", "creative", "MODERATE"),
    (["manim", "math animation", "3b1b", "explain video"], "manim-video", "creative", "COMPLEX"),
    (["p5.js", "generative art", "creative coding"], "p5js", "creative", "MODERATE"),
    (["song", "music", "lyrics", "suno"], "songwriting-and-ai-music", "creative", "MODERATE"),
    (["GIF", "gif search", "reaction"], "gif-search", "media", "TRIVIAL"),
    
    # MLOps
    (["serve LLM", "deploy model", "vLLM", "inference server"], "serving-llms-vllm", "mlops", "COMPLEX"),
    (["fine-tune", "LoRA", "train model", "QLoRA"], "axolotl", "mlops", "COMPLEX"),
    (["GGUF", "quantize", "llama.cpp"], "gguf-quantization", "mlops", "MODERATE"),
    (["benchmark", "MMLU", "evaluate LLM"], "evaluating-llms-harness", "mlops", "MODERATE"),
    (["Hugging Face", "hf hub", "upload model"], "huggingface-hub", "mlops", "SIMPLE"),
    (["jailbreak", "red team", "refusal remove"], "godmode", "red-teaming", "MODERATE"),
    
    # GitHub
    (["github", "create repo", "PR", "issue"], "github-repo-management", "github", "SIMPLE"),
    (["batch repo", "add license to all", "bulk github"], "batch-repo-ops", "github", "SIMPLE"),
    (["converge repo", "merge repo"], "repo-convergence", "github", "COMPLEX"),
    (["codebase inspect", "lines of code", "LOC"], "codebase-inspection", "github", "SIMPLE"),
    (["code review", "review diff"], "github-code-review", "github", "MODERATE"),
    
    # Productivity
    (["email", "send email", "inbox", "read mail"], "himalaya", "email", "SIMPLE"),
    (["PDF", "edit PDF", "modify PDF"], "nano-pdf", "productivity", "SIMPLE"),
    (["PPT", "powerpoint", "slides", "deck"], "powerpoint", "productivity", "MODERATE"),
    (["obsidian", "notes", "vault"], "obsidian", "note-taking", "SIMPLE"),
    (["notion", "create page", "notion database"], "notion", "productivity", "SIMPLE"),
    
    # Smart Home / Social / Leisure
    (["smart light", "hue", "philips"], "openhue", "smart-home", "TRIVIAL"),
    (["telegram", "bot config"], "telegram-config", "social", "SIMPLE"),
    (["tweet", "post X", "twitter"], "xitter", "social", "SIMPLE"),
    (["nearby", "restaurant", "find place"], "find-nearby", "leisure", "TRIVIAL"),
    
    # Orchestration
    (["spawn", "council", "deliberate", "multi-agent"], "necroswarm", "agent-orchestration", "COMPLEX"),
    (["MCP", "tool server", "connect MCP", "mcporter"], "native-mcp", "mcp", "SIMPLE"),
    
    # Development Tools
    (["claude code", "claude CLI", "delegate coding"], "claude-code", "autonomous-ai-agents", "MODERATE"),
    (["codex", "openai codex"], "codex", "autonomous-ai-agents", "MODERATE"),
    (["opencode", "open code CLI"], "opencode", "autonomous-ai-agents", "MODERATE"),
    
    # Jupyter / Data
    (["jupyter", "notebook", "data exploration"], "jupyter-live-kernel", "data-science", "SIMPLE"),
]

# NecroSwarm routing thresholds
COMPLEXITY_MODEL_ROUTING = {
    "TRIVIAL": "ministral-3:3b:cloud",
    "SIMPLE": "gemma3:27b:cloud",
    "MODERATE": "minimax-m2.5:cloud",
    "COMPLEX": "kimi-k2.5:cloud",
}


def resolve(query: str, json_output: bool = False) -> dict:
    """Resolve an intent string to matching skills.
    
    Args:
        query: Natural language intent string.
        json_output: If True, return JSON dict. If False, return human-readable.
    
    Returns:
        Dict with matches, each containing skill, category, complexity, suggested model.
    """
    query_lower = query.lower()
    matches = []
    
    for patterns, skill, category, complexity in DISPATCH_TABLE:
        for pattern in patterns:
            if pattern in query_lower:
                # Score by pattern length (longer = more specific)
                score = len(pattern)
                matches.append({
                    "skill": skill,
                    "category": category,
                    "complexity": complexity,
                    "matched_pattern": pattern,
                    "suggested_model": COMPLEXITY_MODEL_ROUTING.get(complexity, "glm-5.1:cloud"),
                    "score": score,
                })
                break  # One match per dispatch entry is enough
    
    # Sort by score (most specific match first)
    matches.sort(key=lambda x: -x["score"])
    
    # Remove duplicate skills (keep highest-scored match)
    seen_skills = set()
    deduped = []
    for m in matches:
        if m["skill"] not in seen_skills:
            seen_skills.add(m["skill"])
            deduped.append(m)
    
    # If no matches, return council deliberation fallback
    if not deduped:
        return {
            "query": query,
            "matches": [],
            "fallback": {
                "method": "necroswarm_council",
                "suggested_model": "kimi-k2.5:cloud",
                "reason": "No dispatch pattern matched — escalate to council deliberation",
            },
        }
    
    result = {
        "query": query,
        "matches": deduped,
        "primary": deduped[0] if deduped else None,
        "council_deliberation": any(m["complexity"] == "COMPLEX" for m in deduped),
    }
    
    return result


def format_human(result: dict) -> str:
    """Format result as human-readable text."""
    lines = []
    lines.append(f"⚫ RESOLVER: \"{result['query']}\"")
    lines.append("")
    
    if not result["matches"]:
        lines.append("No dispatch pattern matched.")
        if "fallback" in result:
            fb = result["fallback"]
            lines.append(f"  ⚠ Fallback: {fb['method']}")
            lines.append(f"  Model: {fb['suggested_model']}")
            lines.append(f"  Reason: {fb['reason']}")
        return "\n".join(lines)
    
    lines.append(f"Primary: {result['primary']['skill']} ({result['primary']['complexity']})")
    lines.append(f"  Pattern: \"{result['primary']['matched_pattern']}\"")
    lines.append(f"  Model: {result['primary']['suggested_model']}")
    
    if result["council_deliberation"]:
        lines.append(f"  ⚠ COMPLEX → NecroSwarm council deliberation recommended")
    
    if len(result["matches"]) > 1:
        lines.append("")
        lines.append("Additional matches:")
        for m in result["matches"][1:]:
            lines.append(f"  • {m['skill']} ({m['complexity']}) — matched \"{m['matched_pattern']}\"")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python resolve.py \"<intent query>\" [--json]", file=sys.stderr)
        print("Example: python resolve.py \"debug the login error\"", file=sys.stderr)
        sys.exit(1)
    
    # Parse args: first non-flag argument is the query
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv
    
    if not args:
        print("Error: no query provided", file=sys.stderr)
        sys.exit(1)
    
    query = " ".join(args)
    result = resolve(query, json_output=json_output)
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))
    
    # Exit 1 if no matches found
    sys.exit(0 if result.get("matches") else 1)


if __name__ == "__main__":
    main()