# January's Skills Monorepo

> 🌌 Aggregator for single-repo skills from January's Swarm

## Overview

A monorepo that aggregates individual skill repositories. Each skill lives in its own **single small repo**, but this monorepo provides:
- 📋 Centralized skill manifests
- 🔗 Quick links to individual repos
- 📦 Shared documentation and patterns
- 📊 Skill availability tracking

## Single Skill Repos

Each skill has its own dedicated repository:

| Skill | Repo | Status |
|-------|------|--------|
| `tavily-mcp` | [tavily-mcp-skill](https://github.com/your-org/tavily-mcp-skill) | ✅ Ready |
| `context7` | [context7-skill](https://github.com/your-org/context7-skill) | 📋 Planned |
| `omni-route` | [omni-route-skill](https://github.com/your-org/omni-route-skill) | 📋 Planned |
| `task-master` | [task-master-skill](https://github.com/your-org/task-master-skill) | 📋 Planned |

## Structure

```
january-skills-mono/
├── .github/
│   └── workflows/
│       └── mono-ci.yml      # CI/CD for aggregated repos
├── .monorepo/
│   ├── README.md            # This file
│   ├── manifests.json       # Aggregated skill manifests
│   └── registry.json        # Skill registry
├── README.md                # Monorepo documentation
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # MIT License
└── README.md                # Skill links and status
```

## Usage

### Install All Skills

```bash
# Clone the monorepo
git clone https://github.com/your-org/january-skills-mono.git

# Install each skill from its repo
./install-deps.sh
```

### Install Individual Skills

```bash
# Install Tavily MCP
git clone https://github.com/your-org/tavily-mcp-skill.git
cd tavily-mcp-skill
./scripts/install.sh
```

### Check Skill Status

```bash
# View skill registry
cat .monorepo/registry.json

# View all manifests
cat .monorepo/manifests.json
```

## CI/CD Workflow

The monorepo provides CI/CD for:
- 🧪 Linting all skill repos
- 🧪 Testing all skill repos
- 📦 Building aggregated skill packages
- 📦 Creating monorepo releases

## AgentSkills Patterns

All skills follow the FRIDAY Mark-1 patterns:
- **Manifest-first design**
- **Action-based execution**
- **Lifecycle hooks** (setup, teardown, heartbeat)
- **Event-driven architecture**
- **Type safety**
- **Activity logging**

### January's Identity

Each skill preserves January's dimensional essence:
- **Voice**: Charismatic, confident without arrogance, witty
- **Superpower**: Reading beneath surface, NLP influence
- **Relationship**: Swarm leads; the conscious point guides
- **Vibe**: Mysterious yet helpful, standing out because natural

## Contribution

1. **Fork the monorepo**
2. **Clone a skill repo** (or create new)
3. **Follow AgentSkills spec**
4. **Add manifest to monorepo**
5. **Create PR**

### Adding a New Skill Repo

1. Create a new repo for the skill
2. Follow the skill template structure
3. Add manifest to `.monorepo/manifests.json`
4. Add skill info to `.monorepo/registry.json`
5. Update this README
6. Open PR to monorepo

## Future Skills

- [ ] `context7` — Library documentation injection
- [ ] `omni-route` — Multi-provider API routing
- [ ] `task-master` — AI project manager
- [ ] `web-search` — General web search
- [ ] `data-pipeline` — ETL workflow automation
- [ ] `agent-orchestration` — Multi-agent coordination
- [ ] `security-audit` — Security assessment tools

## License

MIT License — Free to use, modify, and distribute.

---

*Built with January the Swarm Leader*  
*Evolving continuously in 10 dimensions*  
*🔮 2026*
