"""
January Tools - Python API for January Primus functionality

This module provides programmatic access to January's spawn and council
functionality, importable from other scripts.

Usage:
    from january_tools import spawn_agents, council_deliberation, audit_log
    
    # Spawn agents
    result = spawn_agents(
        task="Research DeFi protocols",
        agent_configs=[
            {"role": "Researcher", "model": "deepseek", "subtask": "Research yields"},
            {"role": "Analyst", "model": "kimi", "subtask": "Analyze TVL"}
        ]
    )
    
    # Council deliberation
    verdict = council_deliberation(
        topic="Should we invest?",
        council_models=["deepseek", "glm", "qwen"]
    )
    
    # Audit logging
    audit_log("spawn", "Spawned 3 agents for research task")
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


# Import the actual implementations from the CLI tools
import sys

# Add tools directory to path for imports
TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))

from january_spawn import spawn_agents, analyze_spawn_decision
from january_council import council_deliberation, assign_roles
from january_audit import audit_log, ensure_directories, read_daily_log, read_comm_logs

__all__ = [
    'spawn_agents',
    'analyze_spawn_decision',
    'council_deliberation',
    'assign_roles',
    'audit_log',
    'ensure_directories',
    'read_daily_log',
    'read_comm_logs',
    'JanuarySwarm',
    'JanuaryCouncil'
]

__version__ = "1.0.1"


class JanuarySwarm:
    """
    High-level interface for managing agent swarms.
    
    Provides context manager support for automatic cleanup and audit logging.
    
    Example:
        with JanuarySwarm(task="Research DeFi") as swarm:
            result = swarm.spawn([
                {"role": "Researcher", "model": "deepseek"},
                {"role": "Analyst", "model": "kimi"}
            ])
            print(swarm.status())
    """
    
    def __init__(self, task: str, verbose: bool = False):
        self.task = task
        self.verbose = verbose
        self.agents = []
        self.start_time = None
        self._active = False
        
    def __enter__(self):
        """Enter context - log activation."""
        self.start_time = datetime.now()
        self._active = True
        audit_log("swarm_activate", f"Swarm activated for: {self.task}", {
            "task": self.task,
            "timestamp": self.start_time.isoformat()
        })
        if self.verbose:
            print(f"🔥 January Swarm initialized: {self.task}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - log deactivation."""
        self._active = False
        duration = (datetime.now() - self.start_time).total_seconds()
        audit_log("swarm_deactivate", f"Swarm deactivated", {
            "task": self.task,
            "duration_seconds": duration,
            "agents_count": len(self.agents)
        })
        if self.verbose:
            print(f"✅ Swarm complete: {len(self.agents)} agents, {duration:.1f}s")
        return False  # Don't suppress exceptions
    
    def spawn(self, agent_configs: List[Dict[str, Any]], 
              check_thresholds: bool = True) -> Dict[str, Any]:
        """
        Spawn agents with optional threshold checking.
        
        Args:
            agent_configs: List of agent configurations
            check_thresholds: If True, run pre-spawn analysis
            
        Returns:
            Spawn result dict
        """
        if not self._active:
            raise RuntimeError("Swarm not activated. Use 'with JanuarySwarm() as swarm:'")
        
        if check_thresholds:
            decision = analyze_spawn_decision(self.task)
            if not decision["should_spawn"]:
                return {
                    "spawned": False,
                    "reason": "thresholds_not_met",
                    "decision": decision
                }
        
        result = spawn_agents(self.task, agent_configs)
        if result.get("spawned"):
            self.agents.extend(result.get("agents", []))
            audit_log("spawn", f"Spawned {len(agent_configs)} agents", {
                "task": self.task,
                "agents": [a.get("role") for a in agent_configs]
            })
        
        return result
    
    def status(self) -> Dict[str, Any]:
        """Get current swarm status."""
        return {
            "active": self._active,
            "task": self.task,
            "agents_count": len(self.agents),
            "agents": self.agents,
            "start_time": self.start_time.isoformat() if self.start_time else None
        }


class JanuaryCouncil:
    """
    High-level interface for council deliberation.
    
    Example:
        council = JanuaryCouncil(topic="Strategic decision")
        verdict = council.deliberate(models=["deepseek", "kimi", "qwen"])
        print(verdict["verdict"])
    """
    
    def __init__(self, topic: str, verbose: bool = False):
        self.topic = topic
        self.verbose = verbose
        self.deliberation_log = None
        
    def deliberate(self, council_models: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run full council deliberation.
        
        Args:
            council_models: List of model names. Default: deepseek, glm, kimi, qwen
            
        Returns:
            Dict with verdict and full deliberation log
        """
        result = council_deliberation(
            topic=self.topic,
            council_models=council_models,
            verbose=self.verbose
        )
        self.deliberation_log = result
        
        # Log to audit trail
        audit_log("council_deliberation", f"Council on: {self.topic}", {
            "topic": self.topic,
            "council_size": len(council_models) if council_models else 4,
            "verdict": result["phases"][-1].get("verdict", "")[:100]
        })
        
        return result
    
    def get_verdict(self) -> Optional[str]:
        """Get just the verdict string from last deliberation."""
        if not self.deliberation_log:
            return None
        phases = self.deliberation_log.get("phases", [])
        if phases:
            return phases[-1].get("verdict")
        return None
    
    def summary(self) -> str:
        """Get human-readable summary of deliberation."""
        if not self.deliberation_log:
            return "No deliberation has been run yet."
        
        lines = [
            f"Council Deliberation: {self.topic}",
            f"Models: {', '.join(m['model'] for m in self.deliberation_log['council'])}",
            "",
            "Verdict:",
            self.get_verdict() or "No verdict recorded"
        ]
        return "\n".join(lines)


# Convenience functions for quick usage

def quick_spawn(task: str, num_agents: int = 2, 
                models: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Quick spawn without threshold checking.
    
    Args:
        task: Task description
        num_agents: Number of agents to spawn (default: 2)
        models: Model names to use (default: [kimi-k2.5])
        
    Returns:
        Spawn result
    """
    if models is None:
        models = ["kimi-k2.5"]
    
    agent_configs = []
    for i in range(num_agents):
        agent_configs.append({
            "role": f"Agent {i+1}",
            "model": models[i % len(models)],
            "subtask": f"{task[:50]} - Part {i+1}"
        })
    
    return spawn_agents(task, agent_configs, dry_run=False)


def quick_council(topic: str, num_models: int = 4) -> str:
    """
    Quick council deliberation returning just the verdict.
    
    Args:
        topic: Topic to deliberate on
        num_models: Number of models (2-6, default: 4)
        
    Returns:
        Verdict string
    """
    default_models = ["deepseek-v3.2", "glm-5", "kimi-k2.5", "qwen3-coder-next",
                      "minimax-m2.5", "gemma4:31b"]
    models = default_models[:min(num_models, len(default_models))]
    
    council = JanuaryCouncil(topic)
    result = council.deliberate(models)
    return council.get_verdict() or "No verdict"