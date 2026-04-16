#!/usr/bin/env python3
"""
Simple unit tests for namespace.py that don't require pytest.
"""

import sys
from pathlib import Path

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

from namespace import (
    URIParser,
    ParsedURI,
    NamespaceResolver,
    resolve,
    resolve_str,
    NAMESPACE_HANDLERS,
    register_handler,
    DEFAULT_BASE_PATH
)


def test_simple():
    """Run basic tests."""
    errors = []
    
    # Test 1: Parse simple URI
    try:
        parsed = URIParser.parse("openclaw://memory/agents/halloween")
        assert parsed.namespace == "memory"
        assert parsed.path_parts == ["agents", "halloween"]
        print("✓ Test 1: Parse simple URI")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
        errors.append(1)
    
    # Test 2: Resolve memory agent
    try:
        result = resolve_str("openclaw://memory/agents/halloween", base_path=Path("/workspace"))
        assert result == "/workspace/memory/agents/halloween.md"
        print("✓ Test 2: Resolve memory agent")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
        errors.append(2)
    
    # Test 3: Resolve logs with date
    try:
        result = resolve_str("openclaw://logs/agents/halloween/2026-03-22", base_path=Path("/workspace"))
        assert result == "/workspace/logs/agents/halloween/2026-03-22.jsonl"
        print("✓ Test 3: Resolve logs with date")
    except Exception as e:
        print(f"✗ Test 3 failed: {e}")
        errors.append(3)
    
    # Test 4: Resolve comms
    try:
        result = resolve_str("openclaw://comms/telegram/370338255", base_path=Path("/workspace"))
        assert result == "/workspace/comms/telegram/370338255.jsonl"
        print("✓ Test 4: Resolve comms")
    except Exception as e:
        print(f"✗ Test 4 failed: {e}")
        errors.append(4)
    
    # Test 5: Resolve skills
    try:
        result = resolve_str("openclaw://skills/github", base_path=Path("/workspace"))
        assert result == "/workspace/skills/github/SKILL.md"
        print("✓ Test 5: Resolve skills")
    except Exception as e:
        print(f"✗ Test 5 failed: {e}")
        errors.append(5)
    
    # Test 6: Resolve config
    try:
        result = resolve_str("openclaw://config/agents", base_path=Path("/workspace"))
        assert result == "/workspace/AGENTS.md"
        print("✓ Test 6: Resolve config")
    except Exception as e:
        print(f"✗ Test 6 failed: {e}")
        errors.append(6)
    
    # Test 7: Resolve workspace
    try:
        result = resolve_str("openclaw://workspace/halloween/code", base_path=Path("/workspace"))
        assert result == "/workspace-halloween/code"
        print("✓ Test 7: Resolve workspace")
    except Exception as e:
        print(f"✗ Test 7 failed: {e}")
        errors.append(7)
    
    # Test 8: Invalid protocol
    try:
        URIParser.parse("https://example.com")
        print("✗ Test 8 failed: Should have raised ValueError")
        errors.append(8)
    except ValueError:
        print("✓ Test 8: Invalid protocol rejected")
    
    # Test 9: Unknown namespace
    try:
        resolver = NamespaceResolver()
        resolver.resolve("openclaw://unknown/path")
        print("✗ Test 9 failed: Should have raised ValueError")
        errors.append(9)
    except ValueError:
        print("✓ Test 9: Unknown namespace rejected")
    
    # Test 10: Caching
    try:
        resolver = NamespaceResolver(base_path=Path("/workspace"))
        uri = "openclaw://memory/agents/halloween"
        result1 = resolver.resolve(uri)
        result2 = resolver.resolve(uri)
        assert resolver._get_cached(uri) == result1
        print("✓ Test 10: Caching works")
    except Exception as e:
        print(f"✗ Test 10 failed: {e}")
        errors.append(10)
    
    # Test 11: Query parsing
    try:
        parsed = URIParser.parse("openclaw://memory/agents/halloween?format=json&verbose=true")
        assert parsed.query == {"format": "json", "verbose": "true"}
        print("✓ Test 11: Query parsing")
    except Exception as e:
        print(f"✗ Test 11 failed: {e}")
        errors.append(11)
    
    # Test 12: Fragment parsing
    try:
        parsed = URIParser.parse("openclaw://memory/agents/halloween#section1")
        assert parsed.fragment == "section1"
        print("✓ Test 12: Fragment parsing")
    except Exception as e:
        print(f"✗ Test 12 failed: {e}")
        errors.append(12)
    
    print(f"\n{12 - len(errors)}/12 tests passed")
    return len(errors) == 0


if __name__ == "__main__":
    success = test_simple()
    sys.exit(0 if success else 1)
