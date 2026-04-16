"""
OpenClaw Namespace Protocol
Core module for resolving openclaw:// URIs to filesystem paths.
"""

import re
import json
import hashlib
from pathlib import Path
from functools import lru_cache
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse, unquote


# Base path for all resolutions
DEFAULT_BASE_PATH = Path("/home/ubuntu/.openclaw/workspace")

# Namespace handlers registry
NAMESPACE_HANDLERS: Dict[str, callable] = {}


def register_handler(namespace: str):
    """Decorator to register a namespace handler."""
    def decorator(func):
        NAMESPACE_HANDLERS[namespace] = func
        return func
    return decorator


@dataclass
class ParsedURI:
    """Parsed OpenClaw URI components."""
    raw: str
    namespace: str  # memory, logs, comms, skills, etc.
    path_parts: list[str]
    query: Dict[str, str]
    fragment: str
    
    @property
    def resource_type(self) -> str:
        """Get the resource type (first path component)."""
        return self.path_parts[0] if self.path_parts else ""
    
    @property
    def resource_id(self) -> Optional[str]:
        """Get the resource ID (second path component)."""
        return self.path_parts[1] if len(self.path_parts) > 1 else None


class URIParser:
    """Parser for openclaw:// URIs."""
    
    URI_PATTERN = re.compile(r'^openclaw://([^/]+)(/.*)?$')
    
    @classmethod
    def parse(cls, uri: str) -> ParsedURI:
        """
        Parse an openclaw:// URI into components.
        
        Examples:
            openclaw://memory/agents/halloween
            openclaw://logs/agents/halloween/2026-03-22
            openclaw://comms/telegram/370338255
        """
        if not uri.startswith("openclaw://"):
            raise ValueError(f"Invalid OpenClaw URI: {uri}")
        
        # Strip the protocol prefix
        rest = uri[11:]  # len("openclaw://") = 11
        
        # Parse query and fragment
        fragment = ""
        if "#" in rest:
            rest, fragment = rest.split("#", 1)
        
        query_str = ""
        if "?" in rest:
            rest, query_str = rest.split("?", 1)
        
        # Parse query parameters
        query = {}
        if query_str:
            for param in query_str.split("&"):
                if "=" in param:
                    k, v = param.split("=", 1)
                    query[unquote(k)] = unquote(v)
        
        # Extract namespace and path
        if "/" in rest:
            namespace, path = rest.split("/", 1)
        else:
            namespace, path = rest, ""
        
        path_parts = [unquote(p) for p in path.split("/") if p]
        
        return ParsedURI(
            raw=uri,
            namespace=namespace,
            path_parts=path_parts,
            query=query,
            fragment=fragment
        )


class NamespaceResolver:
    """
    Resolver for OpenClaw namespace URIs with caching.
    """
    
    def __init__(self, base_path: Optional[Path] = None, cache_size: int = 128):
        self.base_path = base_path or DEFAULT_BASE_PATH
        self._cache: Dict[str, Path] = {}
        self._cache_size = cache_size
        self._parser = URIParser()
    
    def _cache_key(self, uri: str) -> str:
        """Generate cache key for a URI."""
        return hashlib.sha256(uri.encode()).hexdigest()[:16]
    
    def _get_cached(self, uri: str) -> Optional[Path]:
        """Get cached result if available."""
        key = self._cache_key(uri)
        return self._cache.get(key)
    
    def _set_cached(self, uri: str, path: Path) -> None:
        """Cache a resolved path."""
        key = self._cache_key(uri)
        # Simple LRU: if cache is full, clear half of it
        if len(self._cache) >= self._cache_size:
            keys_to_remove = list(self._cache.keys())[:self._cache_size // 2]
            for k in keys_to_remove:
                del self._cache[k]
        self._cache[key] = path
    
    def invalidate(self, uri: Optional[str] = None) -> None:
        """Invalidate cache for a specific URI or all URIs."""
        if uri is None:
            self._cache.clear()
        else:
            key = self._cache_key(uri)
            self._cache.pop(key, None)
    
    def resolve(self, uri: str) -> Path:
        """
        Resolve an openclaw:// URI to a filesystem path.
        
        Args:
            uri: The OpenClaw URI to resolve
            
        Returns:
            Path: The resolved filesystem path
            
        Raises:
            ValueError: If the URI is invalid or namespace unknown
        """
        # Check cache first
        cached = self._get_cached(uri)
        if cached:
            return cached
        
        # Parse the URI
        parsed = self._parser.parse(uri)
        
        # Get handler for namespace
        handler = NAMESPACE_HANDLERS.get(parsed.namespace)
        if not handler:
            raise ValueError(f"Unknown namespace: {parsed.namespace}")
        
        # Resolve to path
        path = handler(self.base_path, parsed)
        
        # Cache the result
        self._set_cached(uri, path)
        
        return path
    
    def resolve_str(self, uri: str) -> str:
        """Resolve URI and return as string."""
        return str(self.resolve(uri))


# ============================================================================
# Namespace Handlers
# ============================================================================

@register_handler("memory")
def _handle_memory(base_path: Path, parsed: ParsedURI) -> Path:
    """
    Handle memory:// URIs
    
    Format: openclaw://memory/{type}/{name}
    
    Examples:
        openclaw://memory/agents/halloween → {base}/memory/agents/halloween.md
        openclaw://memory/notes/todo → {base}/memory/notes/todo.md
    """
    if not parsed.path_parts:
        return base_path / "memory"
    
    resource_type = parsed.path_parts[0]
    
    if resource_type == "agents":
        if len(parsed.path_parts) >= 2:
            agent_name = parsed.path_parts[1]
            return base_path / "memory" / "agents" / f"{agent_name}.md"
        return base_path / "memory" / "agents"
    
    # Default: memory/{path}.md
    subpath = "/".join(parsed.path_parts)
    return base_path / "memory" / f"{subpath}.md"


@register_handler("logs")
def _handle_logs(base_path: Path, parsed: ParsedURI) -> Path:
    """
    Handle logs:// URIs
    
    Format: openclaw://logs/{type}/{id}/{date}
    
    Examples:
        openclaw://logs/agents/halloween/2026-03-22 → {base}/logs/agents/halloween/2026-03-22.jsonl
        openclaw://logs/system/2026-03-22 → {base}/logs/system/2026-03-22.log
    """
    if not parsed.path_parts:
        return base_path / "logs"
    
    log_type = parsed.path_parts[0]
    
    if log_type == "agents":
        if len(parsed.path_parts) >= 3:
            agent_name = parsed.path_parts[1]
            date = parsed.path_parts[2]
            return base_path / "logs" / "agents" / agent_name / f"{date}.jsonl"
        elif len(parsed.path_parts) >= 2:
            agent_name = parsed.path_parts[1]
            return base_path / "logs" / "agents" / agent_name
        return base_path / "logs" / "agents"
    
    if log_type == "system":
        if len(parsed.path_parts) >= 2:
            date = parsed.path_parts[1]
            return base_path / "logs" / "system" / f"{date}.log"
        return base_path / "logs" / "system"
    
    # Default logs structure
    subpath = "/".join(parsed.path_parts)
    return base_path / "logs" / subpath


@register_handler("comms")
def _handle_comms(base_path: Path, parsed: ParsedURI) -> Path:
    """
    Handle comms:// URIs
    
    Format: openclaw://comms/{channel}/{thread_id}
    
    Examples:
        openclaw://comms/telegram/370338255 → {base}/comms/telegram/370338255.jsonl
        openclaw://comms/discord/general → {base}/comms/discord/general.jsonl
    """
    if not parsed.path_parts:
        return base_path / "comms"
    
    channel = parsed.path_parts[0]
    
    if len(parsed.path_parts) >= 2:
        thread_id = parsed.path_parts[1]
        return base_path / "comms" / channel / f"{thread_id}.jsonl"
    
    return base_path / "comms" / channel


@register_handler("skills")
def _handle_skills(base_path: Path, parsed: ParsedURI) -> Path:
    """
    Handle skills:// URIs
    
    Format: openclaw://skills/{skill_name}
    
    Examples:
        openclaw://skills/github → {base}/skills/github/SKILL.md
        openclaw://skills/weather → {base}/skills/weather/SKILL.md
    """
    if not parsed.path_parts:
        return base_path / "skills"
    
    skill_name = parsed.path_parts[0]
    return base_path / "skills" / skill_name / "SKILL.md"


@register_handler("config")
def _handle_config(base_path: Path, parsed: ParsedURI) -> Path:
    """
    Handle config:// URIs
    
    Format: openclaw://config/{file}
    
    Examples:
        openclaw://config/agents → {base}/AGENTS.md
        openclaw://config/soul → {base}/SOUL.md
    """
    if not parsed.path_parts:
        return base_path
    
    config_map = {
        "agents": "AGENTS.md",
        "soul": "SOUL.md",
        "user": "USER.md",
        "memory": "MEMORY.md",
        "identity": "IDENTITY.md",
    }
    
    config_file = parsed.path_parts[0]
    if config_file in config_map:
        return base_path / config_map[config_file]
    
    # Default: direct filename
    return base_path / f"{config_file}.md"


@register_handler("workspace")
def _handle_workspace(base_path: Path, parsed: ParsedURI) -> Path:
    """
    Handle workspace:// URIs
    
    Format: openclaw://workspace/{agent_name}/{path}
    
    Examples:
        openclaw://workspace/halloween/code → {base}/workspace-halloween/code
        openclaw://workspace/octoberxin/research → {base}/workspace-octoberxin/research
    """
    if not parsed.path_parts:
        return base_path
    
    agent_name = parsed.path_parts[0]
    workspace_name = f"workspace-{agent_name}"
    
    if len(parsed.path_parts) > 1:
        subpath = "/".join(parsed.path_parts[1:])
        return base_path.parent / workspace_name / subpath
    
    return base_path.parent / workspace_name


# ============================================================================
# Convenience Functions
# ============================================================================

def resolve(uri: str, base_path: Optional[Path] = None) -> Path:
    """
    Quick resolve function using default resolver.
    
    Args:
        uri: OpenClaw URI to resolve
        base_path: Optional custom base path
        
    Returns:
        Path: Resolved filesystem path
    """
    resolver = NamespaceResolver(base_path)
    return resolver.resolve(uri)


def resolve_str(uri: str, base_path: Optional[Path] = None) -> str:
    """Quick resolve returning string."""
    return str(resolve(uri, base_path))


# Global resolver instance for convenience
_default_resolver: Optional[NamespaceResolver] = None


def get_resolver() -> NamespaceResolver:
    """Get or create the default resolver instance."""
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = NamespaceResolver()
    return _default_resolver