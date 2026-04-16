# OpenClaw Namespace Protocol

A URI-based protocol for resolving paths in the OpenClaw agent filesystem.

## Overview

The OpenClaw namespace protocol provides a standardized way to reference resources across agent workspaces, memory, logs, and skills using URIs. It enables agents to communicate about filesystem locations without hardcoding paths.

## Installation

```bash
# Clone the repository
git clone https://github.com/0x-wzw/openclaw-namespace.git
cd openclaw-namespace

# Install (optional)
pip install -e .

# Or just use directly
python cli.py resolve openclaw://memory/agents/halloween
```

## URI Format

```
openclaw://{namespace}/{path}?{query}#{fragment}
```

### Components

- **Protocol**: `openclaw://` (required)
- **Namespace**: The resource category (e.g., `memory`, `logs`, `skills`)
- **Path**: Resource identifier within the namespace
- **Query**: Optional parameters (e.g., `?format=json`)
- **Fragment**: Optional section reference (e.g., `#section1`)

## Namespaces

### memory://

Access agent memory and notes.

```
openclaw://memory/agents/{agent_name}     → {base}/memory/agents/{agent}.md
openclaw://memory/notes/{note_name}       → {base}/memory/notes/{note}.md
openclaw://memory/{any_path}              → {base}/memory/{path}.md
```

**Examples:**
- `openclaw://memory/agents/halloween` → `memory/agents/halloween.md`
- `openclaw://memory/notes/todo` → `memory/notes/todo.md`

### logs://

Access agent and system logs.

```
openclaw://logs/agents/{agent}/{date}     → {base}/logs/agents/{agent}/{date}.jsonl
openclaw://logs/system/{date}             → {base}/logs/system/{date}.log
openclaw://logs/{path}                    → {base}/logs/{path}
```

**Examples:**
- `openclaw://logs/agents/halloween/2026-03-22` → `logs/agents/halloween/2026-03-22.jsonl`
- `openclaw://logs/system/2026-03-22` → `logs/system/2026-03-22.log`

### comms://

Access communication logs.

```
openclaw://comms/{channel}/{thread_id}    → {base}/comms/{channel}/{thread}.jsonl
```

**Examples:**
- `openclaw://comms/telegram/370338255` → `comms/telegram/370338255.jsonl`
- `openclaw://comms/discord/general` → `comms/discord/general.jsonl`

### skills://

Access skill definitions.

```
openclaw://skills/{skill_name}            → {base}/skills/{skill}/SKILL.md
```

**Examples:**
- `openclaw://skills/github` → `skills/github/SKILL.md`
- `openclaw://skills/weather` → `skills/weather/SKILL.md`

### config://

Access configuration files.

```
openclaw://config/agents                  → {base}/AGENTS.md
openclaw://config/soul                    → {base}/SOUL.md
openclaw://config/user                    → {base}/USER.md
openclaw://config/memory                  → {base}/MEMORY.md
openclaw://config/identity                → {base}/IDENTITY.md
```

### workspace://

Access agent-specific workspaces.

```
openclaw://workspace/{agent}/{path}       → {base}/../workspace-{agent}/{path}
```

**Examples:**
- `openclaw://workspace/halloween/code` → `workspace-halloween/code`
- `openclaw://workspace/octoberxin/research` → `workspace-octoberxin/research`

## CLI Usage

### Resolve a URI

```bash
openclaw-ns resolve openclaw://memory/agents/halloween
# Output: /home/ubuntu/.openclaw/workspace/memory/agents/halloween.md

# With existence check
openclaw-ns resolve openclaw://memory/agents/halloween --check
```

### Parse a URI

```bash
openclaw-ns parse openclaw://memory/agents/halloween
# Output:
# URI: openclaw://memory/agents/halloween
# Namespace: memory
# Path Parts: ['agents', 'halloween']
# Resource Type: agents
# Resource ID: halloween
# Resolves To: /home/ubuntu/.openclaw/workspace/memory/agents/halloween.md
```

### List Namespaces

```bash
openclaw-ns list
# Output:
# Registered Namespaces:
#   comms           - Handle comms:// URIs
#   config          - Handle config:// URIs
#   logs            - Handle logs:// URIs
#   memory          - Handle memory:// URIs
#   skills          - Handle skills:// URIs
#   workspace       - Handle workspace:// URIs
```

### Validate URIs

```bash
# From command line
openclaw-ns validate openclaw://memory/agents/halloween openclaw://skills/github

# From stdin
echo "openclaw://memory/agents/halloween" | openclaw-ns validate
```

### Interactive Mode

```bash
openclaw-ns interactive
# openclaw-ns> openclaw://memory/agents/halloween
# → /home/ubuntu/.openclaw/workspace/memory/agents/halloween.md [exists]
```

## Python API

### Basic Usage

```python
from namespace import resolve, resolve_str, NamespaceResolver

# Quick resolve
path = resolve("openclaw://memory/agents/halloween")
print(path)  # /home/ubuntu/.openclaw/workspace/memory/agents/halloween.md

# As string
path_str = resolve_str("openclaw://memory/agents/halloween")

# With custom base path
path = resolve("openclaw://memory/agents/halloween", base_path=Path("/custom"))
```

### Advanced Usage

```python
from namespace import NamespaceResolver, URIParser

# Create resolver with caching
resolver = NamespaceResolver(cache_size=128)

# Resolve multiple times (cached)
path1 = resolver.resolve("openclaw://memory/agents/halloween")
path2 = resolver.resolve("openclaw://memory/agents/halloween")  # Uses cache

# Parse URIs
parser = URIParser()
parsed = parser.parse("openclaw://memory/agents/halloween?format=json")
print(parsed.namespace)      # "memory"
print(parsed.path_parts)       # ["agents", "halloween"]
print(parsed.query)            # {"format": "json"}
print(parsed.resource_type)    # "agents"
print(parsed.resource_id)      # "halloween"

# Invalidate cache
resolver.invalidate("openclaw://memory/agents/halloween")  # Specific URI
resolver.invalidate()  # All cached entries
```

### Custom Handlers

```python
from namespace import register_handler, NamespaceResolver

@register_handler("custom")
def _handle_custom(base_path, parsed):
    return base_path / "custom" / "/".join(parsed.path_parts)

# Now openclaw://custom/foo/bar resolves to {base}/custom/foo/bar
resolver = NamespaceResolver()
path = resolver.resolve("openclaw://custom/foo/bar")
```

## Architecture

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────────┐
│   openclaw://   │────▶│   Parser    │────▶│   Namespace     │
│     URI         │     │             │     │   Resolver      │
└─────────────────┘     └─────────────┘     └─────────────────┘
                                                     │
                          ┌─────────────────────────┼──────────┐
                          │                         │          │
                          ▼                         ▼          ▼
                    ┌─────────┐              ┌────────┐  ┌───────┐
                    │ memory  │              │ logs   │  │ skills│
                    │ handler │              │ handler│  │handler│
                    └─────────┘              └────────┘  └───────┘
```

## Testing

```bash
# Run all tests
pytest test_namespace.py -v

# Run specific test class
pytest test_namespace.py::TestURIParser -v

# Run with coverage
pytest test_namespace.py --cov=namespace --cov-report=term-missing
```

## Protocol Specification

### URI Grammar

```
openclaw_uri    ::= "openclaw://" namespace ["/" path] ["?" query] ["#" fragment]
namespace       ::= ALPHA *(ALPHA / DIGIT / "-" / "_")
path            ::= segment *("/" segment)
segment         ::= *(pchar)
query           ::= query_param *("&" query_param)
query_param     ::= key ["=" value]
key             ::= *(pchar)
value           ::= *(pchar / "/" / "?")
fragment        ::= *(pchar)
pchar           ::= unreserved / pct-encoded / "-" / "." / "_" / "~"
unreserved      ::= ALPHA / DIGIT / "-" / "." / "_" / "~"
pct-encoded     ::= "%" HEXDIG HEXDIG
```

### Caching Strategy

- LRU cache with configurable size (default: 128 entries)
- Cache key derived from SHA-256 of URI
- Automatic invalidation on demand
- Thread-safe (single instance only)

### Error Handling

| Error | Condition | Response |
|-------|-----------|----------|
| Invalid URI | Missing/invalid protocol | `ValueError` |
| Unknown namespace | No handler registered | `ValueError` |
| Resolution error | Handler returns invalid path | `ValueError` |

## License

MIT - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Changelog

### 1.0.0 (2026-03-22)
- Initial release
- Core namespace handlers: memory, logs, comms, skills, config, workspace
- CLI with resolve, parse, list, validate, interactive commands
- Python API with caching
- Comprehensive test suite