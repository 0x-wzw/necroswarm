"""
Unit tests for the OpenClaw namespace protocol.
"""

import pytest
from pathlib import Path
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


class TestURIParser:
    """Tests for the URI parser."""
    
    def test_parse_simple_uri(self):
        """Parse a simple URI."""
        uri = "openclaw://memory/agents/halloween"
        parsed = URIParser.parse(uri)
        
        assert parsed.raw == uri
        assert parsed.namespace == "memory"
        assert parsed.path_parts == ["agents", "halloween"]
        assert parsed.resource_type == "agents"
        assert parsed.resource_id == "halloween"
    
    def test_parse_with_query(self):
        """Parse URI with query parameters."""
        uri = "openclaw://memory/agents/halloween?format=json&verbose=true"
        parsed = URIParser.parse(uri)
        
        assert parsed.namespace == "memory"
        assert parsed.path_parts == ["agents", "halloween"]
        assert parsed.query == {"format": "json", "verbose": "true"}
    
    def test_parse_with_fragment(self):
        """Parse URI with fragment."""
        uri = "openclaw://memory/agents/halloween#section1"
        parsed = URIParser.parse(uri)
        
        assert parsed.namespace == "memory"
        assert parsed.fragment == "section1"
    
    def test_parse_with_query_and_fragment(self):
        """Parse URI with both query and fragment."""
        uri = "openclaw://memory/agents/halloween?format=json#section1"
        parsed = URIParser.parse(uri)
        
        assert parsed.namespace == "memory"
        assert parsed.query == {"format": "json"}
        assert parsed.fragment == "section1"
    
    def test_parse_url_encoded(self):
        """Parse URI with URL-encoded characters."""
        uri = "openclaw://memory/notes/hello%20world"
        parsed = URIParser.parse(uri)
        
        assert parsed.path_parts == ["notes", "hello world"]
    
    def test_parse_empty_path(self):
        """Parse URI with empty path."""
        uri = "openclaw://memory"
        parsed = URIParser.parse(uri)
        
        assert parsed.namespace == "memory"
        assert parsed.path_parts == []
        assert parsed.resource_type == ""
    
    def test_parse_invalid_protocol(self):
        """Reject invalid protocol."""
        with pytest.raises(ValueError, match="Invalid OpenClaw URI"):
            URIParser.parse("https://example.com")
        
        with pytest.raises(ValueError, match="Invalid OpenClaw URI"):
            URIParser.parse("/some/path")
    
    def test_parse_single_path_component(self):
        """Parse URI with single path component."""
        uri = "openclaw://skills/github"
        parsed = URIParser.parse(uri)
        
        assert parsed.namespace == "skills"
        assert parsed.path_parts == ["github"]
        assert parsed.resource_type == "github"
        assert parsed.resource_id is None


class TestNamespaceHandlers:
    """Tests for namespace handlers."""
    
    def test_memory_handler_agents(self):
        """Test memory handler for agents."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://memory/agents/halloween",
            namespace="memory",
            path_parts=["agents", "halloween"],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["memory"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace/memory/agents/halloween.md")
    
    def test_memory_handler_notes(self):
        """Test memory handler for notes."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://memory/notes/todo",
            namespace="memory",
            path_parts=["notes", "todo"],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["memory"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace/memory/notes/todo.md")
    
    def test_memory_handler_empty(self):
        """Test memory handler with empty path."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://memory",
            namespace="memory",
            path_parts=[],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["memory"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace/memory")
    
    def test_logs_handler_agent_with_date(self):
        """Test logs handler with agent and date."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://logs/agents/halloween/2026-03-22",
            namespace="logs",
            path_parts=["agents", "halloween", "2026-03-22"],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["logs"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace/logs/agents/halloween/2026-03-22.jsonl")
    
    def test_logs_handler_system(self):
        """Test logs handler for system logs."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://logs/system/2026-03-22",
            namespace="logs",
            path_parts=["system", "2026-03-22"],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["logs"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace/logs/system/2026-03-22.log")
    
    def test_comms_handler(self):
        """Test comms handler."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://comms/telegram/370338255",
            namespace="comms",
            path_parts=["telegram", "370338255"],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["comms"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace/comms/telegram/370338255.jsonl")
    
    def test_skills_handler(self):
        """Test skills handler."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://skills/github",
            namespace="skills",
            path_parts=["github"],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["skills"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace/skills/github/SKILL.md")
    
    def test_config_handler(self):
        """Test config handler."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://config/agents",
            namespace="config",
            path_parts=["agents"],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["config"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace/AGENTS.md")
    
    def test_workspace_handler(self):
        """Test workspace handler."""
        base = Path("/workspace")
        parsed = ParsedURI(
            raw="openclaw://workspace/halloween/code",
            namespace="workspace",
            path_parts=["halloween", "code"],
            query={},
            fragment=""
        )
        
        handler = NAMESPACE_HANDLERS["workspace"]
        result = handler(base, parsed)
        
        assert result == Path("/workspace-halloween/code")
    
    def test_register_handler(self):
        """Test handler registration."""
        @register_handler("test")
        def _test_handler(base_path, parsed):
            return base_path / "test"
        
        assert "test" in NAMESPACE_HANDLERS


class TestNamespaceResolver:
    """Tests for the namespace resolver."""
    
    def test_resolver_init_default(self):
        """Test resolver with default base path."""
        resolver = NamespaceResolver()
        assert resolver.base_path == DEFAULT_BASE_PATH
    
    def test_resolver_init_custom(self):
        """Test resolver with custom base path."""
        custom_path = Path("/custom/path")
        resolver = NamespaceResolver(base_path=custom_path)
        assert resolver.base_path == custom_path
    
    def test_resolve_memory_agent(self):
        """Resolve memory agent URI."""
        resolver = NamespaceResolver(base_path=Path("/workspace"))
        result = resolver.resolve("openclaw://memory/agents/halloween")
        
        assert result == Path("/workspace/memory/agents/halloween.md")
    
    def test_resolve_unknown_namespace(self):
        """Reject unknown namespace."""
        resolver = NamespaceResolver()
        
        with pytest.raises(ValueError, match="Unknown namespace"):
            resolver.resolve("openclaw://unknown/path")
    
    def test_caching(self):
        """Test that caching works."""
        resolver = NamespaceResolver(base_path=Path("/workspace"))
        uri = "openclaw://memory/agents/halloween"
        
        # First call
        result1 = resolver.resolve(uri)
        
        # Should be cached
        assert resolver._get_cached(uri) == result1
        
        # Second call should use cache
        result2 = resolver.resolve(uri)
        assert result1 == result2
    
    def test_invalidate_cache(self):
        """Test cache invalidation."""
        resolver = NamespaceResolver(base_path=Path("/workspace"))
        uri = "openclaw://memory/agents/halloween"
        
        resolver.resolve(uri)
        assert resolver._get_cached(uri) is not None
        
        resolver.invalidate(uri)
        assert resolver._get_cached(uri) is None
    
    def test_invalidate_all(self):
        """Test clearing all cache."""
        resolver = NamespaceResolver(base_path=Path("/workspace"))
        
        resolver.resolve("openclaw://memory/agents/halloween")
        resolver.resolve("openclaw://memory/agents/octoberxin")
        
        resolver.invalidate()
        
        assert len(resolver._cache) == 0
    
    def test_resolve_str(self):
        """Test resolve returning string."""
        resolver = NamespaceResolver(base_path=Path("/workspace"))
        result = resolver.resolve_str("openclaw://memory/agents/halloween")
        
        assert result == "/workspace/memory/agents/halloween.md"
        assert isinstance(result, str)


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_resolve_function(self):
        """Test global resolve function."""
        result = resolve("openclaw://memory/agents/halloween", base_path=Path("/workspace"))
        
        assert result == Path("/workspace/memory/agents/halloween.md")
    
    def test_resolve_str_function(self):
        """Test global resolve_str function."""
        result = resolve_str("openclaw://memory/agents/halloween", base_path=Path("/workspace"))
        
        assert result == "/workspace/memory/agents/halloween.md"
        assert isinstance(result, str)


class TestRealWorldExamples:
    """Tests based on real OpenClaw usage patterns."""
    
    def test_halloween_memory(self):
        """Test accessing Halloween's memory."""
        resolver = NamespaceResolver()
        result = resolver.resolve_str("openclaw://memory/agents/halloween")
        
        assert result.endswith("memory/agents/halloween.md")
    
    def test_agent_logs(self):
        """Test accessing agent logs."""
        resolver = NamespaceResolver()
        result = resolver.resolve_str("openclaw://logs/agents/halloween/2026-03-22")
        
        assert result.endswith("logs/agents/halloween/2026-03-22.jsonl")
    
    def test_telegram_comms(self):
        """Test accessing Telegram communications."""
        resolver = NamespaceResolver()
        result = resolver.resolve_str("openclaw://comms/telegram/370338255")
        
        assert result.endswith("comms/telegram/370338255.jsonl")
    
    def test_github_skill(self):
        """Test accessing GitHub skill."""
        resolver = NamespaceResolver()
        result = resolver.resolve_str("openclaw://skills/github")
        
        assert result.endswith("skills/github/SKILL.md")
    
    def test_agents_config(self):
        """Test accessing AGENTS.md config."""
        resolver = NamespaceResolver()
        result = resolver.resolve_str("openclaw://config/agents")
        
        assert result.endswith("AGENTS.md")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])