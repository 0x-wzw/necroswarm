#!/usr/bin/env python3
"""Brain-First Cache Check — Check memory before external API calls.

This script checks whether information is already available locally
before making expensive external calls. It searches:
1. Memory (durable facts)
2. Session history (past conversations)

Usage:
    python brain_check.py "voidtether github url"
    python brain_check.py --json "ollama cloud models"
    python brain_check.py --source-only "telegram bot token"

Returns:
    Whether the info was found locally, and where.
    Exit 0 if found, exit 1 if not found (go ahead with web_search).
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path


# ── Local Knowledge Sources ─────────────────────────────────────────────

MEMORY_PATH = Path.home() / ".hermes" / "memory.md"


def check_memory(query: str) -> dict:
    """Check Hermes memory file for relevant information.
    
    Searches the memory markdown file for keyword matches.
    Returns match info or empty dict.
    """
    if not MEMORY_PATH.exists():
        return {"found": False, "source": "memory", "query": query, "content": ""}
    
    try:
        content = MEMORY_PATH.read_text()
    except Exception:
        return {"found": False, "source": "memory", "query": query, "content": ""}
    
    # Split into entries (separated by § delimiters)
    entries = content.split("§")
    query_lower = query.lower()
    query_terms = query_lower.split()
    
    matches = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        entry_lower = entry.lower()
        
        # Score: how many query terms appear in the entry
        term_hits = sum(1 for term in query_terms if term in entry_lower)
        if term_hits == 0:
            continue
        
        # Calculate relevance score
        score = term_hits / len(query_terms) if query_terms else 0
        matches.append({
            "score": score,
            "terms_matched": term_hits,
            "content": entry[:500],  # Truncate long entries
        })
    
    if matches:
        # Sort by score, return best match
        matches.sort(key=lambda m: m["score"], reverse=True)
        best = matches[0]
        return {
            "found": best["score"] >= 0.5,  # At least half the terms must match
            "source": "memory",
            "query": query,
            "score": best["score"],
            "terms_matched": best["terms_matched"],
            "content": best["content"],
        }
    
    return {"found": False, "source": "memory", "query": query, "content": ""}


def check_sessions(query: str) -> dict:
    """Check session history for relevant information.
    
    Uses the hermes session_search tool if available, falls back
    to checking session directories directly.
    
    Returns match info or empty dict.
    """
    sessions_dir = Path.home() / ".hermes" / "sessions"
    
    if not sessions_dir.exists():
        return {"found": False, "source": "sessions", "query": query, "content": ""}
    
    query_lower = query.lower()
    query_terms = query_lower.split()
    
    # Quick grep through recent session files
    matches = []
    
    try:
        # Use grep to search session files
        for term in query_terms[:3]:  # Limit to 3 terms for speed
            result = subprocess.run(
                ["grep", "-r", "-l", "-i", term, str(sessions_dir)],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                for filepath in result.stdout.strip().split("\n"):
                    if filepath:
                        matches.append(filepath)
    except (subprocess.TimeoutExpired, Exception):
        pass
    
    if matches:
        # Count unique files (a file matching multiple terms is more relevant)
        file_counts = {}
        for f in matches:
            file_counts[f] = file_counts.get(f, 0) + 1
        
        # Sort by match count (files matching more terms rank higher)
        sorted_files = sorted(file_counts.items(), key=lambda x: -x[1])
        best_file = sorted_files[0][0] if sorted_files else None
        
        if best_file:
            return {
                "found": True,
                "source": "sessions",
                "query": query,
                "match_count": len(set(matches)),
                "best_match": best_file,
            }
    
    return {"found": False, "source": "sessions", "query": query, "content": ""}


def brain_check(query: str, json_output: bool = False, source_only: bool = False) -> dict:
    """Run the brain-first cache check: memory → sessions → external.
    
    Args:
        query: The information you're looking for.
        json_output: If True, return JSON. If False, return human-readable.
        source_only: If True, only return source (no content).
    
    Returns:
        Check result with found status, source, and recommendation.
    """
    # Step 1: Check memory
    memory_result = check_memory(query)
    
    # Step 2: Check sessions (only if memory didn't find it)
    session_result = check_sessions(query) if not memory_result["found"] else {"found": False, "source": "sessions"}
    
    # Determine recommendation
    if memory_result["found"]:
        recommendation = "USE_MEMORY"
        action = "Information found in memory — no external call needed"
        can_skip_external = True
    elif session_result["found"]:
        recommendation = "CHECK_SESSION"
        action = "Information may exist in past sessions — use session_search"
        can_skip_external = True
    else:
        recommendation = "EXTERNAL_CALL"
        action = "No local information found — proceed with web_search or other external call"
        can_skip_external = False
    
    result = {
        "query": query,
        "memory_check": memory_result,
        "session_check": session_result,
        "recommendation": recommendation,
        "can_skip_external": can_skip_external,
        "action": action,
    }
    
    if source_only:
        result["memory_check"].pop("content", None)
        result["session_check"].pop("content", None)
        result["session_check"].pop("best_match", None)
    
    return result


def format_human(result: dict) -> str:
    """Format result as human-readable text."""
    lines = []
    lines.append(f"🧠 Brain-First Check: \"{result['query']}\"")
    lines.append("")
    
    # Memory result
    mem = result["memory_check"]
    if mem["found"]:
        lines.append(f"  ✅ Memory: FOUND (score: {mem.get('score', 'N/A')})")
        if mem.get("content"):
            preview = mem["content"][:120].replace("\n", " ")
            lines.append(f"     → {preview}...")
    else:
        lines.append(f"  ❌ Memory: not found")
    
    # Session result
    sess = result["session_check"]
    if sess["found"]:
        lines.append(f"  ✅ Sessions: FOUND ({sess.get('match_count', '?')} matches)")
    else:
        lines.append(f"  ❌ Sessions: not found")
    
    # Recommendation
    lines.append("")
    rec = result["recommendation"]
    if rec == "USE_MEMORY":
        lines.append(f"  ✨ Recommendation: USE_MEMORY — info already cached locally")
    elif rec == "CHECK_SESSION":
        lines.append(f"  🔍 Recommendation: CHECK_SESSION — may exist in past conversations")
    else:
        lines.append(f"  🌐 Recommendation: EXTERNAL_CALL — proceed with web_search")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Brain-first cache check — check memory before external calls")
    parser.add_argument("query", help="The information you're looking for")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--source-only", action="store_true", help="Only show sources, not content")
    
    args = parser.parse_args()
    
    result = brain_check(args.query, json_output=args.json, source_only=args.source_only)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))
    
    # Exit 0 if found in memory, 1 if need external call
    sys.exit(0 if result["can_skip_external"] else 1)


if __name__ == "__main__":
    main()