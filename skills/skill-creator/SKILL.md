---
name: skill-creator
description: Author new agent skills following the AgentSkills spec. Use when creating a new skill from scratch or when asked to improve, review, audit, tidy up, or clean up an existing skill or SKILL.md file. Also use when editing or restructuring a skill directory. Covers skill structure, SKILL.md format, script conventions, references layout, and publishing.
---

# Skill Creator

Author new skills that follow the AgentSkills spec.

## Skill Structure

```
skill-name/
├── SKILL.md          # Required: name + description + body
├── scripts/          # Optional: helper scripts
│   └── skill-name.sh
├── references/       # Optional: docs, API refs
│   └── api.md
└── _meta.json        # Optional: version, author, tags
```

## SKILL.md Format

Every skill needs a valid SKILL.md with three YAML frontmatter fields + markdown body:

```markdown
---
name: my-skill
description: One-line description of what this skill does. Include when to use it and what tools/APIs it needs.
---

# My Skill

Full description, prerequisites, usage examples.

## Prerequisites

- Tool A
- API key B

## Configuration

```bash
export MY_API_KEY="..."
```

## Usage

```bash
./scripts/my-skill.sh arg1 arg2
```
```

## Rules

1. **name** must be kebab-case, unique, no spaces
2. **description** must be one line, specific, start with verb
3. **body** must have Prerequisites, Configuration, Usage sections
4. Keep SKILL.md under 200 lines
5. No TODOs or stubs — working content only
6. Scripts go in `scripts/` — executable, documented

## Creating a New Skill

```bash
# 1. Create directory
mkdir -p skills/my-new-skill/{scripts,references}

# 2. Write SKILL.md
cat > skills/my-new-skill/SKILL.md << 'EOF'
---
name: my-new-skill
description: ...
---

# My New Skill
...
EOF

# 3. Write helper scripts
cat > skills/my-new-skill/scripts/my-new-skill.sh << 'EOF'
#!/bin/bash
# Does X
...
EOF
chmod +x skills/my-new-skill/scripts/my-new-skill.sh
```

## Publishing

```bash
clawhub publish skills/my-new-skill
```

## Validation

```bash
# Check SKILL.md format
bash scripts/validate.sh

# Ensure no TODOs
grep -r "TODO" skills/*/SKILL.md && echo "Found TODOs!" || echo "Clean"
```

## Common Mistakes

- Description too vague (e.g., "does stuff")
- Missing Prerequisites section
- Scripts not executable
- SKILL.md over 200 lines
- name not kebab-case
- Publishing without testing
