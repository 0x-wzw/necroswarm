---
name: tmux
description: Control tmux sessions for interactive CLIs. Use when you need to send keystrokes, scrape pane output, or manage long-running terminal sessions. Requires tmux installed and an existing session. Part of the OpenClaw skill set for terminal automation.
---

# Tmux Skill

Remote-control tmux sessions — send keystrokes, capture output, manage panes.

## Prerequisites

```bash
# Check tmux is installed
tmux -V

# Start a session if none exists
tmux new -s mysession
```

## OpenClaw Tmux Skill

OpenClaw has a built-in tmux skill at:
```
~/.npm-global/lib/node_modules/openclaw/skills/tmux/SKILL.md
```

Load it with the tmux skill loader for full instructions.

## Quick Commands

```bash
# List sessions
tmux ls

# Send keystrokes to a pane
tmux send-keys -t mysession:0 "echo hello" Enter

# Capture pane output
tmux capture-pane -t mysession:0 -p

# Create window
tmux new-window -t mysession

# Split pane
tmux split-window -t mysession:0 -h
```

## Session Management

```bash
# Detach (keep running)
tmux detach

# Kill session
tmux kill-session -t mysession

# Switch sessions
tmux switch -t mysession
```

## Common Use Cases

- **Long-running processes** — start in tmux, detach, reattach later
- **Bot control** — send commands to running bots
- **Log monitoring** — tail logs in one pane, work in another
- **Parallel tasks** — split windows for side-by-side work

## Notes

- Sessions persist across SSH disconnects
- Panes can be split horizontally/vertically
- Copy mode for scrolling through output
