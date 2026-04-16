"""
"""NECROSWARM — Swarm Intelligence Core

This module provides swarm-native coordination capabilities including:
- Coordinator: Central orchestration of swarm agents
- Consensus: Raft/gossip-based consensus implementation
- Message Bus: Inter-agent communication layer
- Role Manager: Agent specialization (orchestrator/worker/critic/memory/communicator)
- Swarm Memory: Cross-simulation persistent knowledge base
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, ClassVar, Dict, List, Optional, Set, TypeVar

from .docker_sandbox import DockerSandbox, SandboxAgent, SandboxConfig, SandboxResult

logger = logging.getLogger(__name__)

# Runtime type
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


@dataclass
class SwarmMessage:
    """Message exchanged between swarm agents."""
    message_id: str
    sender_id: str
    recipient_id: Optional[str]
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int = 3600  # Time to live in seconds
    delivered: bool = False


@dataclass
class ConsensusVote:
    """Vote in a consensus protocol."""
    voter_id: str
    choice: str
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    justification: Optional[str] = None


@dataclass
class SwarmState:
    """Current state of the swarm."""
    swarm_id: str
    agent_count: int = 0
    active_agents: Set[str] = field(default_factory=set)
    message_count: int = 0
    consensus_state: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class MessageBus(ABC):
    """Abstract message bus for inter-agent communication."""
    
    @abstractmethod
    async def send(self, message: SwarmMessage) -> bool:
        """Send a message to its recipient(s)."""
        pass
    
    @abstractmethod
    async def broadcast(self, message: SwarmMessage, scope: Optional[List[str]] = None) -> int:
        """Broadcast a message to multiple agents."""
        pass
    
    @abstractmethod
    async def subscribe(self, agent_id: str, callback: Callable[[SwarmMessage], Any]) -> None:
        """Subscribe an agent to receive messages."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe an agent from messaging."""
        pass
    
    @abstractmethod
    async def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[SwarmMessage]:
        """Receive pending messages for an agent."""
        pass


class RoleManager:
    """Manages agent specialization and role assignment."""
    
    def __init__(self, agent_spec: AgentSpec):
        self.agent_spec = agent_spec
        self.role = agent_spec.role
        self.specializations: Dict[str, List[AgentSpec]] = self._initialize_specializations()
    
    def _initialize_specializations(self) -> Dict[str, List[AgentSpec]]:
        """Initialize specializations for each role."""
        return {
            AgentRole.ORCHESTRATOR: [],
            AgentRole.WORKER: [],
            AgentRole.CRITIC: [],
            AgentRole.MEMORY: [],
            AgentRole.COMMUNICATOR: []
        }
    
    def assign_role(self, agent: AgentSpec) -> None:
        """Assign or reassign an agent to a role."""
        self.specializations[self.role].append(agent)
        self.agent_spec = agent
        logger.info(f"Agent {agent.agent_id} assigned role: {agent.role}")
    
    def get_agents_by_role(self, role: AgentRole) -> List[AgentSpec]:
        """Get all agents with a specific role."""
        return self.specializations[role]
    
    def has_role(self, role: AgentRole) -> bool:
        """Check if any agent has a specific role."""
        return len(self.specializations[role]) > 0
    
    def get_role_distribution(self) -> Dict[AgentRole, int]:
        """Get count of agents per role."""
        return {role: len(agents) for role, agents in self.specializations.items()}
    
    def optimize_role_distribution(self, target_roles: Dict[AgentRole, int]) -> None:
        """Optimize agent-to-role assignments to match target distribution."""
        current = self.get_role_distribution()
        for role, target in target_roles.items():
            current_count = current.get(role, 0)
            if target > current_count:
                logger.info(f"Dynamically allocate {target - current_count} agents for {role}")
            elif target < current_count:
                self.specializations[role] = self.specializations[role][:target]


class ConsensusEngine:
    """Implements consensus protocols for swarm decision-making."""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.quorum_size: int = 1
        self.current_vote: Optional[ConsensusVote] = None
        self.votes: Dict[str, ConsensusVote] = {}
    
    async def submit_vote(self, vote: ConsensusVote) -> bool:
        """Submit a vote to the consensus process."""
        self.votes[vote.voter_id] = vote
        return await self._check_consensus()
    
    async def broadcast_vote(self, vote: ConsensusVote) -> int:
        """Broadcast a vote to the swarm."""
        message = SwarmMessage(
            message_id=str(uuid.uuid4()),
            sender_id=vote.voter_id,
            recipient_id=None,
            message_type="consensus_vote",
            payload={
                "vote": {
                    "choice": vote.choice,
                    "confidence": vote.confidence,
                    "justification": vote.justification
                }
            }
        )
        return await self.message_bus.broadcast(message)
    
    async def _check_consensus(self) -> bool:
        """Check if consensus has been reached."""
        votes = list(self.votes.values())
        if not votes:
            return False
        
        choice_counts: Dict[str, int] = {}
        for vote in votes:
            choice = vote.choice
            choice_counts[choice] = choice_counts.get(choice, 0) + 1
        
        total_votes = len(votes)
        required = max(total_votes // 2 + 1, self.quorum_size)
        
        for choice, count in choice_counts.items():
            if count >= required:
                self.current_vote = ConsensusVote(
                    voter_id="consensus_reached",
                    choice=choice,
                    confidence=1.0,
                    justification="Consensus reached"
                )
                return True
        
        return False
    
    def get_result(self) -> Optional[ConsensusVote]:
        """Get the current consensus result if available."""
        return self.current_vote


class SwarmCoordinator:
    """Central coordinator for swarm orchestration with Docker sandbox support."""
    
    # Resource allocation per tier
    TIER_RESOURCES: ClassVar[Dict[str, Dict[str, Any]]] = {
        "T1": {"memory_limit": "2g", "cpu_limit": 2.0, "timeout": 600, "image": "python:3.11"},
        "T2": {"memory_limit": "1g", "cpu_limit": 1.0, "timeout": 300, "image": "python:3.11-slim"},
        "T3": {"memory_limit": "512m", "cpu_limit": 0.5, "timeout": 120, "image": "python:3.11-alpine"},
    }
    
    def __init__(
        self,
        swarm_id: str,
        message_bus: MessageBus,
        role_manager: RoleManager,
        consensus_engine: ConsensusEngine,
        swarm_memory: Optional["SwarmMemory"] = None,
        enable_docker: bool = False,
        docker_network: str = "swarm-net"
    ):
        self.swarm_id = swarm_id
        self.message_bus = message_bus
        self.role_manager = role_manager
        self.consensus_engine = consensus_engine
        self.swarm_memory = swarm_memory
        self.agents: Dict[str, AgentSpec] = {}
        self.state = SwarmState(swarm_id=swarm_id)
        self.running = False
        self._tasks: Set[asyncio.Task] = set()
        
        # Docker sandbox integration
        self.enable_docker = enable_docker
        self.docker_sandbox: Optional[DockerSandbox] = None
        self._sandbox_agents: Dict[str, SandboxAgent] = {}
        
        if enable_docker:
            try:
                self.docker_sandbox = DockerSandbox(
                    swarm_network=docker_network,
                    keep_alive=False  # Ephemeral by default
                )
                logger.info(f"Docker sandbox enabled for swarm {swarm_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize Docker sandbox: {e}")
                self.enable_docker = False
    
    async def add_agent(self, agent_spec: AgentSpec) -> bool:
        """Add an agent to the swarm."""
        if agent_spec.agent_id in self.agents:
            logger.warning(f"Agent {agent_spec.agent_id} already in swarm")
            return False
        
        self.agents[agent_spec.agent_id] = agent_spec
        self.state.active_agents.add(agent_spec.agent_id)
        agent_spec.role = self._assign_role(agent_spec)
        self.role_manager.assign_role(agent_spec)
        self.state.agent_count += 1
        self.state.updated_at = datetime.now()
        
        logger.info(f"Added agent {agent_spec.agent_id} ({agent_spec.role}) to swarm {self.swarm_id}")
        return True
    
    def _assign_role(self, agent_spec: AgentSpec) -> AgentRole:
        """Dynamically assign a role based on availability and priority."""
        roles = list(AgentRole)
        roles.sort(key=lambda r: self.role_manager.get_agents_by_role(r).__len__())
        
        for role in roles:
            if not self.role_manager.has_role(role):
                return role
        
        return roles[0]
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the swarm."""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents.pop(agent_id)
        self.state.active_agents.discard(agent_id)
        self.role_manager.specializations[agent.role].remove(agent)
        self.state.agent_count -= 1
        self.state.updated_at = datetime.now()
        
        logger.info(f"Removed agent {agent_id} from swarm {self.swarm_id}")
        return True
    
    async def start(self) -> None:
        """Start the swarm coordinator."""
        self.running = True
        logger.info(f"Started swarm coordinator for swarm {self.swarm_id}")
        
        await self.message_bus.subscribe(
            self.swarm_id, 
            self._handle_message
        )
        
        self._tasks.add(asyncio.create_task(self._message_loop()))
    
    async def stop(self) -> None:
        """Stop the swarm coordinator."""
        self.running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.message_bus.unsubscribe(self.swarm_id)
        
        logger.info(f"Stopped swarm coordinator for swarm {self.swarm_id}")
    
    async def _message_loop(self) -> None:
        """Main message processing loop."""
        while self.running:
            try:
                raw = await self.message_bus.receive(self.swarm_id, timeout=1.0)
                if raw:
                    await self._handle_message(raw)
                    self.state.message_count += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
    
    async def _handle_message(self, message: SwarmMessage) -> None:
        """Handle incoming swarm messages."""
        logger.debug(f"Received message {message.message_id}: {message.message_type}")
        
        if message.message_type == "consensus_vote":
            payload = message.payload.get("vote", {})
            vote = ConsensusVote(
                voter_id=message.sender_id,
                choice=payload.get("choice", "unknown"),
                confidence=payload.get("confidence", 0.5),
                justification=payload.get("justification")
            )
            await self.consensus_engine.submit_vote(vote)
            
            if self.consensus_engine.get_result():
                await self._execute_consensus(self.consensus_engine.get_result())
        
        elif message.message_type == "task_request":
            await self._handle_task_request(message)
        
        elif message.message_type == "state_sync":
            await self._handle_state_sync(message)
    
    async def _execute_consensus(self, result: ConsensusVote) -> None:
        """Execute actions based on consensus result."""
        logger.info(f"Executing consensus: {result.choice}")
        
        if self.swarm_memory:
            await self.swarm_memory.store_consensus(
                swarm_id=self.swarm_id,
                consensus=result.choice,
                votes=list(self.consensus_engine.votes.values())
            )
        
        broadcast_message = SwarmMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.swarm_id,
            recipient_id=None,
            message_type="consensus_executed",
            payload={"choice": result.choice, "timestamp": datetime.now().isoformat()}
        )
        await self.message_bus.broadcast(broadcast_message)
    
    async def _handle_task_request(self, message: SwarmMessage) -> None:
        """Handle task requests from other swarm members."""
        payload = message.payload
        task = payload.get("task")
        recipient = payload.get("recipient")
        
        if recipient and recipient != self.swarm_id:
            relay_message = SwarmMessage(
                message_id=str(uuid.uuid4()),
                sender_id=self.swarm_id,
                recipient_id=recipient,
                message_type="task_request",
                payload=task
            )
            await self.message_bus.send(relay_message)
        else:
            logger.info(f"Executing task request: {task}")
    
    async def _handle_state_sync(self, message: SwarmMessage) -> None:
        """Handle state synchronization messages."""
        payload = message.payload
        state_data = payload.get("state")
        if state_data:
            logger.debug(f"Syncing state from {message.sender_id}")
    
    async def broadcast(self, message_type: str, payload: Dict[str, Any]) -> int:
        """Broadcast a message to all swarm agents."""
        message = SwarmMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.swarm_id,
            recipient_id=None,
            message_type=message_type,
            payload=payload
        )
        return await self.message_bus.broadcast(message, list(self.agents.keys()))
    
    async def execute_with_roles(
        self,
        roles: List[AgentRole],
        task: Callable[[AgentSpec], Any]
    ) -> List[Any]:
        """Execute a task using agents with specific roles."""
        results = []
        for role in roles:
            agents = self.role_manager.get_agents_by_role(role)
            for agent in agents:
                try:
                    result = await task(agent)
                    results.append((agent.agent_id, result))
                except Exception as e:
                    logger.error(f"Error executing task for {agent.agent_id}: {e}")
        return results
    
    def get_swarm_state(self) -> SwarmState:
        """Get the current swarm state."""
        self.state.agent_count = len(self.agents)
        self.state.message_count = self.state.message_count
        self.state.updated_at = datetime.now()
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """Get swarm statistics."""
        state = self.get_swarm_state()
        stats = {
            "swarm_id": self.swarm_id,
            "agent_count": state.agent_count,
            "active_agents": list(state.active_agents),
            "role_distribution": self.role_manager.get_role_distribution(),
            "message_count": state.message_count,
            "consensus_state": {
                "has_result": self.consensus_engine.get_result() is not None,
                "current_result": self.consensus_engine.get_result()
            }
        }
        if self.enable_docker:
            stats["sandbox_agents"] = len(self._sandbox_agents)
            stats["docker_sandbox_active"] = len(self.docker_sandbox) if self.docker_sandbox else 0
        return stats
    
    # =============================================================================
    # Docker Sandbox Integration
    # =============================================================================
    
    async def spawn_ephemeral_agent(
        self,
        task: str,
        role: AgentRole = AgentRole.WORKER,
        tier: str = "T3",
        env: Optional[Dict[str, str]] = None
    ) -> Optional[SandboxAgent]:
        """
        Spawn an ephemeral agent in a Docker container.
        
        Args:
            task: Command to execute in the container
            role: Agent role specialization
            tier: Resource tier (T1, T2, T3)
            env: Additional environment variables
        
        Returns:
            SandboxAgent if spawned successfully, None otherwise
        """
        if not self.enable_docker or not self.docker_sandbox:
            logger.warning("Docker sandbox not enabled. Cannot spawn ephemeral agent.")
            return None
        
        # Get resource config for tier
        tier_config = self.TIER_RESOURCES.get(tier, self.TIER_RESOURCES["T3"])
        config = SandboxConfig(
            image=tier_config["image"],
            memory_limit=tier_config["memory_limit"],
            cpu_limit=tier_config["cpu_limit"],
            timeout=tier_config["timeout"],
            network_mode=self.docker_sandbox.swarm_network,
            auto_remove=True
        )
        
        # Prepare agent environment
        agent_env = {
            "SWARM_ID": self.swarm_id,
            "AGENT_ROLE": role.value,
            "AGENT_TIER": tier,
        }
        if env:
            agent_env.update(env)
        
        try:
            sandbox_agent = await self.docker_sandbox.spawn(
                task=task,
                role=role.value,
                tier=tier,
                swarm_id=self.swarm_id,
                env=agent_env,
                config=config
            )
            
            self._sandbox_agents[sandbox_agent.sandbox_id] = sandbox_agent
            
            logger.info(
                f"Spawned ephemeral agent {sandbox_agent.sandbox_id} "
                f"(role={role.value}, tier={tier})"
            )
            return sandbox_agent
            
        except Exception as e:
            logger.error(f"Failed to spawn ephemeral agent: {e}")
            return None
    
    async def execute_in_sandbox(
        self,
        sandbox_id: str,
        command: str,
        timeout: Optional[int] = None
    ) -> Optional[SandboxResult]:
        """
        Execute a command in a running sandbox.
        
        Args:
            sandbox_id: ID of the sandbox agent
            command: Command to execute
            timeout: Optional timeout override
        
        Returns:
            SandboxResult with output and exit code
        """
        if not self.enable_docker or not self.docker_sandbox:
            logger.warning("Docker sandbox not enabled.")
            return None
        
        if sandbox_id not in self._sandbox_agents:
            logger.warning(f"Sandbox {sandbox_id} not found.")
            return None
        
        try:
            result = await self.docker_sandbox.execute(
                sandbox_id=sandbox_id,
                command=command,
                timeout=timeout
            )
            
            # Store result in swarm memory if available
            if self.swarm_memory and result.success:
                await self.swarm_memory.store_consensus(
                    swarm_id=self.swarm_id,
                    consensus=f"sandbox_exec:{sandbox_id}",
                    votes=[]
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Sandbox execution failed for {sandbox_id}: {e}")
            return None
    
    async def destroy_ephemeral_agent(
        self,
        sandbox_id: str,
        force: bool = False
    ) -> bool:
        """
        Destroy an ephemeral sandbox agent.
        
        Args:
            sandbox_id: ID of the sandbox to destroy
            force: Force kill if graceful stop fails
        
        Returns:
            True if destroyed successfully
        """
        if not self.enable_docker or not self.docker_sandbox:
            return False
        
        if sandbox_id not in self._sandbox_agents:
            return False
        
        try:
            destroyed = await self.docker_sandbox.destroy(sandbox_id, force=force)
            if destroyed:
                self._sandbox_agents.pop(sandbox_id, None)
                logger.info(f"Destroyed ephemeral agent {sandbox_id}")
            return destroyed
            
        except Exception as e:
            logger.error(f"Failed to destroy ephemeral agent {sandbox_id}: {e}")
            return False
    
    async def cleanup_sandboxes(self) -> int:
        """Destroy all ephemeral sandbox agents."""
        if not self.enable_docker or not self.docker_sandbox:
            return 0
        
        count = await self.docker_sandbox.destroy_all()
        self._sandbox_agents.clear()
        logger.info(f"Cleaned up {count} ephemeral agents")
        return count
    
    async def get_sandbox_health(self, sandbox_id: str) -> bool:
        """Check if a sandbox agent is healthy."""
        if not self.enable_docker or not self.docker_sandbox:
            return False
        return await self.docker_sandbox.health_check(sandbox_id)
    
    async def run_ephemeral_task(
        self,
        task: str,
        role: AgentRole = AgentRole.WORKER,
        tier: str = "T3",
        cleanup: bool = True
    ) -> Optional[SandboxResult]:
        """
        One-shot: Spawn agent, run task, optionally cleanup.
        
        This is the main convenience method for ephemeral execution.
        
        Args:
            task: Command to execute
            role: Agent role
            tier: Resource tier
            cleanup: Destroy agent after completion
        
        Returns:
            SandboxResult if successful
        """
        agent = await self.spawn_ephemeral_agent(task, role, tier)
        if not agent:
            return None
        
        # Wait for completion (simple sleep-based polling)
        await asyncio.sleep(0.5)
        
        # Get logs/result
        if self.docker_sandbox:
            logs = await self.docker_sandbox.get_logs(agent.sandbox_id)
            
            result = SandboxResult(
                sandbox_id=agent.sandbox_id,
                exit_code=0 if agent.state.name != "FAILED" else 1,
                stdout=logs,
                stderr="",
                duration_ms=0,
                state=agent.state
            )
            
            if cleanup:
                await self.destroy_ephemeral_agent(agent.sandbox_id)
            
            return result
        
        return None
