"""
Role Manager - Manages agent specialization in the swarm.

Agent roles: orchestrator, worker, critic, memory, communicator
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AgentRole(Enum):
    """Swarm agent role specialization."""
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    CRITIC = "critic"
    MEMORY = "memory"
    COMMUNICATOR = "communicator"


@dataclass
class AgentSpec:
    """Specification for a swarm agent."""
    agent_id: str
    role: AgentRole
    name: str
    model: str
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    priority: int = 0
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Agent-specific state
    active: bool = True
    working: bool = False
    context: Optional[Dict[str, Any]] = None


@dataclass
class RoleTemplate:
    """Template defining capabilities for a role."""
    role: AgentRole
    default_capabilities: List[str] = field(default_factory=list)
    default_tools: List[str] = field(default_factory=list)
    suggested_models: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Specific tasks this role excels at
    specializations: List[str] = field(default_factory=list)


class RoleManager:
    """Manages agent specialization and role assignment."""
    
    def __init__(self):
        self._agents: Dict[str, AgentSpec] = {}
        self._role_templates: Dict[AgentRole, RoleTemplate] = self._default_templates()
        self._role_specific_state: Dict[AgentRole, Dict[str, Any]] = {}
        
        # Role-specific data storage
        self._orchestrator_tasks: List[str] = []
        self._worker_results: Dict[str, List[Any]] = {}
        self._critique_points: List[Dict[str, Any]] = []
        self._knowledge_base: Dict[str, Any] = {}
        self._communication_logs: List[Dict[str, Any]] = []
    
    def _default_templates(self) -> Dict[AgentRole, RoleTemplate]:
        """Create default role templates."""
        return {
            AgentRole.ORCHESTRATOR: RoleTemplate(
                role=AgentRole.ORCHESTRATOR,
                default_capabilities=[
                    "task_distribution",
                    "resource_allocation",
                    "state_presentation",
                    "timeline_management"
                ],
                default_tools=["orchestrator", "scheduler", "monitor"],
                suggested_models=["ollama/kimi-k2.5:cloud", "ollama-cloud/deepseek-r1:7b"],
                constraints={"requires": "high-latitude"},
                specializations=["simulation_orchestration", "swarm_coordination"]
            ),
            AgentRole.WORKER: RoleTemplate(
                role=AgentRole.WORKER,
                default_capabilities=[
                    "task_execution",
                    "code_generation", 
                    "data_processing",
                    "analysis"
                ],
                default_tools=["executor", "processor", "crawler"],
                suggested_models=["ollama/qwen2.5:7b", "ollama/llama3.1:8b"],
                constraints={"requires": "compute-intensive"},
                specializations=["simulation_worker", "api_worker"]
            ),
            AgentRole.CRITIC: RoleTemplate(
                role=AgentRole.CRITIC,
                default_capabilities=[
                    "code_review",
                    "logic_validation",
                    "quality_assurance",
                    "edge_case_detection"
                ],
                default_tools=["reviewer", "validator", "tester"],
                suggested_models=["ollama/qwen2.5:7b", "ollama/gemma3:27b"],
                constraints={"requires": ["high-temperature"]},
                specializations=["quality_control", "audit_assistant"]
            ),
            AgentRole.MEMORY: RoleTemplate(
                role=AgentRole.MEMORY,
                default_capabilities=[
                    "knowledge_storage",
                    "semantic_search",
                    "pattern_recognition",
                    "cross_reference"
                ],
                default_tools=["store", "index", "recall"],
                suggested_models=["ollama/qwen2.5:7b"],
                constraints={"requires": "persistent-storage"},
                specializations=["similarity_memory", "entity_memory"]
            ),
            AgentRole.COMMUNICATOR: RoleTemplate(
                role=AgentRole.COMMUNICATOR,
                default_capabilities=[
                    "status_reporting",
                    "progress_updates",
                    "alert_delivery",
                    "documentation_generation"
                ],
                default_tools=["reporter", "formatter", "publisher"],
                suggested_models=["ollama/qwen2.5:7b"],
                constraints={"requires": ["webhook", "api-access"]},
                specializations=["status_dashboard", "notification"]  
            )
        }
    
    def register_template(self, template: RoleTemplate) -> None:
        """Register a custom role template."""
        self._role_templates[template.role] = template
        logger.info(f"Registered role template for {template.role.value}")
    
    def create_agent(
        self,
        agent_id: str,
        role: AgentRole,
        name: str,
        model: str,
        capabilities: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        priority: int = 0,
        **constraints
    ) -> AgentSpec:
        """Create a new swarm agent."""
        template = self._role_templates.get(role)
        
        agent = AgentSpec(
            agent_id=agent_id,
            role=role,
            name=name,
            model=model,
            capabilities=capabilities or template.default_capabilities if template else [],
            tools=tools or template.default_tools if template else [],
            priority=priority,
            constraints={**template.constraints} if template else constraints
        )
        
        self._agents[agent_id] = agent
        self._initialize_role_state(role)
        
        logger.info(f"Created agent {agent_id} with role {role.value}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[AgentSpec]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def get_agents_by_role(self, role: AgentRole) -> List[AgentSpec]:
        """Get all agents with a specific role."""
        return [a for a in self._agents.values() if a.role == role]
    
    def has_role(self, role: AgentRole) -> bool:
        """Check if any agent has a specific role."""
        return any(a.role == role for a in self._agents.values())
    
    def allocate_task(self, agent_id: str, task: str) -> bool:
        """Allocate a task to an agent."""
        agent = self._agents.get(agent_id)
        if agent and agent.active:
            agent.working = True
            agent.context = {"task": task, "started": datetime.now()}
            
            # Add to role-specific storage
            if agent.role == AgentRole.ORCHESTRATOR:
                self._orchestrator_tasks.append({
                    "agent_id": agent_id,
                    "task": task,
                    "timestamp": datetime.now()
                })
            elif agent.role == AgentRole.WORKER:
                if agent_id not in self._worker_results:
                    self._worker_results[agent_id] = []
                self._worker_results[agent_id].append({"task": task, "status": "running"})
            
            return True
        return False
    
    def complete_task(self, agent_id: str, result: Any = None) -> Optional[str]:
        """Complete a task for an agent and return the task."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.working = False
            task = agent.context.get("task") if agent.context else None
            agent.context = None
            
            if agent.role == AgentRole.CRITIC and result:
                self._critique_points.append({
                    "agent_id": agent_id,
                    "task": task,
                    "critique": result,
                    "timestamp": datetime.now()
                })
            
            return task
        
        return None
    
    def assign_role(self, agent_id: str, new_role: AgentRole) -> bool:
        """Reassign an agent to a new role."""
        agent = self._agents.get(agent_id)
        if agent and agent.active:
            # Remove from old role
            self._remove_agent_from_role(agent, agent.role)
            
            # Add to new role
            agent.role = new_role
            self._initialize_role_state(new_role)
            
            # Update role-specific storage
            if new_role == AgentRole.ORCHESTRATOR:
                self._orchestrator_tasks.append({
                    "agent_id": agent_id,
                    "role_assigned": new_role.value,
                    "timestamp": datetime.now()
                })
            
            logger.info(f"Reassigned agent {agent_id} to role {new_role.value}")
            return True
        
        return False
    
    def _remove_agent_from_role(self, agent: AgentSpec, role: AgentRole) -> None:
        """Remove an agent from role-specific storage."""
        if role == AgentRole.WORKER:
            self._worker_results.pop(agent.agent_id, None)
        elif role == AgentRole.ORCHESTRATOR:
            self._orchestrator_tasks = [
                t for t in self._orchestrator_tasks 
                if t.get("agent_id") != agent.agent_id
            ]
        elif role == AgentRole.CRITIC:
            self._critique_points = [
                p for p in self._critique_points 
                if p.get("agent_id") != agent.agent_id
            ]
    
    def _initialize_role_state(self, role: AgentRole) -> None:
        """Initialize role-specific state if needed."""
        if role not in self._role_specific_state:
            self._role_specific_state[role] = {}
    
    def get_role_distribution(self) -> Dict[AgentRole, int]:
        """Get count of agents per role."""
        return {
            role: len(self.get_agents_by_role(role))
            for role in AgentRole
        }
    
    def optimize_role_distribution(
        self, 
        target_roles: Dict[AgentRole, int]
    ) -> None:
        """
        Optimize agent-to-role assignments to match target distribution.
        
        Uses a simple heuristic: prioritize adding agents to underpopulated roles first.
        """
        current = self.get_role_distribution()
        
        for role, target in target_roles.items():
            current_count = current.get(role, 0)
            
            if target > current_count:
                # Need more agents - can be created dynamically
                logger.info(f"Need to allocate {target - current_count} more agents for {role.value}")
            elif target < current_count:
                # Release agents to available slots
                excess = current_count - target
                self._release_agents_for_role(role, excess)
    
    def _release_agents_for_role(self, role: AgentRole, count: int) -> None:
        """Release agents from a role back to available capacity."""
        agents = self.get_agents_by_role(role)
        count = min(count, len(agents))
        
        # Simple approach: mark agents as inactive
        for agent in agents[:count]:
            agent.active = False
            self._remove_agent_from_role(agent, role)
        
        logger.info(f"Released {count} agents from role {role.value}")
    
    def get_worker_results(self, agent_id: str) -> List[Any]:
        """Get all results for a worker agent."""
        return self._worker_results.get(agent_id, [])
    
    def get_critique_points(self) -> List[Dict[str, Any]]:
        """Get all critique points collected."""
        return self._critique_points.copy()
    
    def get_orchestrator_tasks(self) -> List[Dict[str, Any]]:
        """Get all orchestrator tasks."""
        return self._orchestrator_tasks.copy()
    
    def add_knowledge(
        self, 
        key: str, 
        value: Any, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add knowledge to the memory role's knowledge base."""
        self._knowledge_base[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
    
    def lookup_knowledge(self, key: str) -> Optional[Any]:
        """Look up knowledge from the memory role's knowledge base."""
        entry = self._knowledge_base.get(key)
        if entry:
            return entry["value"]
        return None
    
    def add_communication(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        content: Any
    ) -> None:
        """Add a communication log entry."""
        self._communication_logs.append({
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.now()
        })
    
    def get_communication_logs(
        self,
        sender_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get communication logs with optional filters."""
        logs = self._communication_logs
        
        if sender_id:
            logs = [l for l in logs if l.get("sender_id") == sender_id]
        if recipient_id:
            logs = [l for l in logs if l.get("recipient_id") == recipient_id]
        
        return logs[-limit:]  # Return most recent
    
    def get_role_template(self, role: AgentRole) -> Optional[RoleTemplate]:
        """Get the template for a specific role."""
        return self._role_templates.get(role)
    
    def get_active_agents(self) -> List[AgentSpec]:
        """Get all active agents."""
        return [a for a in self._agents.values() if a.active]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get role manager statistics."""
        return {
            "total_agents": len(self._agents),
            "active_agents": len(self.get_active_agents()),
            "role_distribution": self.get_role_distribution(),
            "role_templates": {
                role.value: {
                    "capabilities": tpl.default_capabilities,
                    "tools": tpl.default_tools
                }
                for role, tpl in self._role_templates.items()
            },
            "orchestrator_tasks": len(self._orchestrator_tasks),
            "worker_results": {
                k: len(v) for k, v in self._worker_results.items()
            },
            "critique_points": len(self._critique_points),
            "knowledge_entries": len(self._knowledge_base),
            "communication_logs": len(self._communication_logs)
        }
