"""
Docker Sandbox for Ephemeral Agent Execution

Provides isolated containerized execution environments for swarm agents
with automatic lifecycle management, resource constraints, and consensus
integration.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
import uuid

# Docker SDK
import docker
from docker.models.containers import Container
from docker.errors import DockerException, NotFound

logger = logging.getLogger(__name__)


class SandboxState(Enum):
    """Lifecycle states for a sandbox container."""
    PENDING = auto()
    SPAWNING = auto()
    RUNNING = auto()
    EXECUTING = auto()
    COMPLETED = auto()
    FAILED = auto()
    DESTROYING = auto()
    DESTROYED = auto()


class SandboxError(Exception):
    """Base exception for sandbox operations."""
    pass


class SandboxSpawnError(SandboxError):
    """Failed to spawn sandbox container."""
    pass


class SandboxExecutionError(SandboxError):
    """Task execution failed in sandbox."""
    pass


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""
    image: str = "python:3.11-slim"
    memory_limit: str = "512m"  # Docker memory limit (e.g., "512m", "1g", "2g")
    cpu_limit: float = 1.0  # Number of CPUs
    timeout: int = 300  # Seconds
    network_mode: str = "bridge"  # "bridge", "host", "none", or custom network
    auto_remove: bool = True
    read_only_root: bool = False
    no_new_privileges: bool = True
    cap_drop: List[str] = field(default_factory=lambda: ["ALL"])
    
    # Tier-based presets
    T1_PRESET: ClassVar[Dict] = {
        "memory_limit": "2g",
        "cpu_limit": 2.0,
        "timeout": 600,
    }
    T2_PRESET: ClassVar[Dict] = {
        "memory_limit": "1g",
        "cpu_limit": 1.0,
        "timeout": 300,
    }
    T3_PRESET: ClassVar[Dict] = {
        "memory_limit": "512m",
        "cpu_limit": 0.5,
        "timeout": 120,
    }
    
    @classmethod
    def for_tier(cls, tier: str) -> "SandboxConfig":
        """Create config for a specific model tier."""
        config = cls()
        preset = getattr(cls, f"{tier.upper()}_PRESET", None)
        if preset:
            for key, value in preset.items():
                setattr(config, key, value)
        return config


@dataclass
class SandboxResult:
    """Result of sandbox execution."""
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    state: SandboxState
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0 and self.state == SandboxState.COMPLETED


@dataclass
class SandboxAgent:
    """Represents an agent running in a sandbox."""
    sandbox_id: str
    container_id: Optional[str] = None
    swarm_id: Optional[str] = None
    role: Optional[str] = None
    tier: str = "T3"
    state: SandboxState = SandboxState.PENDING
    spawned_at: Optional[float] = None
    completed_at: Optional[float] = None
    task_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "container_id": self.container_id,
            "swarm_id": self.swarm_id,
            "role": self.role,
            "tier": self.tier,
            "state": self.state.name,
            "spawned_at": self.spawned_at,
            "completed_at": self.completed_at,
            "task_id": self.task_id,
        }


class DockerSandbox:
    """
    Manages ephemeral Docker containers for swarm agent execution.
    
    Features:
    - Isolated execution environments per agent
    - Resource constraints (CPU, memory)
    - Network isolation options
    - Automatic lifecycle management
    - Consensus integration support
    """
    
    def __init__(
        self,
        default_config: Optional[SandboxConfig] = None,
        swarm_network: str = "swarm-net",
        keep_alive: bool = False
    ):
        self.client = docker.from_env()
        self.default_config = default_config or SandboxConfig()
        self.swarm_network = swarm_network
        self.keep_alive = keep_alive
        
        # Active sandbox tracking
        self._agents: Dict[str, SandboxAgent] = {}
        self._containers: Dict[str, Container] = {}
        self._lock = asyncio.Lock()
        
        # Ensure swarm network exists
        self._ensure_network()
        
        logger.info(f"DockerSandbox initialized (network: {swarm_network})")
    
    def _ensure_network(self) -> None:
        """Ensure the swarm network exists."""
        try:
            self.client.networks.get(self.swarm_network)
        except NotFound:
            self.client.networks.create(
                self.swarm_network,
                driver="bridge",
                internal=False
            )
            logger.info(f"Created swarm network: {self.swarm_network}")
    
    async def spawn(
        self,
        task: Optional[str] = None,
        role: Optional[str] = None,
        tier: str = "T3",
        swarm_id: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        config: Optional[SandboxConfig] = None,
        volumes: Optional[Dict[str, str]] = None
    ) -> SandboxAgent:
        """
        Spawn a new ephemeral agent in a Docker container.
        
        Args:
            task: Optional command/task to execute
            role: Agent role (orchestrator, worker, critic, etc.)
            tier: Resource tier (T1, T2, T3)
            swarm_id: Swarm membership ID
            env: Environment variables
            config: Override default sandbox config
            volumes: Additional volume mounts {host: container}
        
        Returns:
            SandboxAgent instance tracking the container
        """
        sandbox_id = f"sandbox-{uuid.uuid4().hex[:12]}"
        cfg = config or SandboxConfig.for_tier(tier)
        
        agent = SandboxAgent(
            sandbox_id=sandbox_id,
            swarm_id=swarm_id,
            role=role,
            tier=tier,
            state=SandboxState.SPAWNING,
            spawned_at=time.time()
        )
        
        async with self._lock:
            self._agents[sandbox_id] = agent
        
        try:
            # Prepare environment
            container_env = {
                "SANDBOX_ID": sandbox_id,
                "AGENT_ROLE": role or "worker",
                "AGENT_TIER": tier,
                "SWARM_ID": swarm_id or "",
                "PYTHONUNBUFFERED": "1",
            }
            if env:
                container_env.update(env)
            
            # Prepare volumes
            volume_mounts = {}
            if volumes:
                for host_path, container_path in volumes.items():
                    volume_mounts[host_path] = {
                        "bind": container_path,
                        "mode": "rw"
                    }
            
            # Calculate CPU quota (Docker uses microseconds per 100ms)
            cpu_quota = int(cfg.cpu_limit * 100000) if cfg.cpu_limit else None
            cpu_period = 100000 if cfg.cpu_limit else None
            
            # Create and start container
            container = self.client.containers.run(
                image=cfg.image,
                command=self._build_entrypoint(task),
                environment=container_env,
                network=self.swarm_network,
                mem_limit=cfg.memory_limit,
                cpu_quota=cpu_quota,
                cpu_period=cpu_period,
                volumes=volume_mounts,
                detach=True,
                stdout=True,
                stderr=True,
                auto_remove=cfg.auto_remove and not self.keep_alive,
                security_opt=["no-new-privileges:true"] if cfg.no_new_privileges else [],
                cap_drop=cfg.cap_drop,
                read_only=cfg.read_only_root,
                labels={
                    "swarm.sandbox.id": sandbox_id,
                    "swarm.agent.role": role or "worker",
                    "swarm.agent.tier": tier,
                }
            )
            
            async with self._lock:
                agent.container_id = container.id
                agent.state = SandboxState.RUNNING
                self._containers[sandbox_id] = container
            
            logger.info(f"Spawned sandbox {sandbox_id} (container: {container.id[:12]})")
            return agent
            
        except DockerException as e:
            agent.state = SandboxState.FAILED
            logger.error(f"Failed to spawn sandbox {sandbox_id}: {e}")
            raise SandboxSpawnError(f"Docker error: {e}") from e
    
    def _build_entrypoint(self, task: Optional[str]) -> str:
        """Build container entrypoint command."""
        if task:
            return f"sh -c '{task}'"
        return "sh -c 'sleep 3600'"  # Idle for 1 hour if no task
    
    async def execute(
        self,
        sandbox_id: str,
        command: str,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """
        Execute a command in a running sandbox.
        
        Args:
            sandbox_id: Sandbox agent ID
            command: Shell command to execute
            timeout: Override default timeout
        
        Returns:
            SandboxResult with output and exit code
        """
        agent = self._agents.get(sandbox_id)
        if not agent:
            raise SandboxError(f"Sandbox {sandbox_id} not found")
        
        if not agent.container_id:
            raise SandboxError(f"Sandbox {sandbox_id} has no container")
        
        container = self._containers.get(sandbox_id)
        if not container:
            raise SandboxError(f"Container for {sandbox_id} not found")
        
        start_time = time.time()
        agent.state = SandboxState.EXECUTING
        
        try:
            # Execute command in container
            exec_result = container.exec_run(
                cmd=f"sh -c '{command}'",
                stdout=True,
                stderr=True,
                demux=True
            )
            
            stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode() if exec_result.output[1] else ""
            
            duration_ms = int((time.time() - start_time) * 1000)
            agent.state = SandboxState.COMPLETED
            agent.completed_at = time.time()
            
            result = SandboxResult(
                sandbox_id=sandbox_id,
                exit_code=exec_result.exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                state=SandboxState.COMPLETED
            )
            
            logger.info(f"Executed in {sandbox_id}: exit={exec_result.exit_code}, duration={duration_ms}ms")
            return result
            
        except Exception as e:
            agent.state = SandboxState.FAILED
            raise SandboxExecutionError(f"Execution failed: {e}") from e
    
    async def destroy(self, sandbox_id: str, force: bool = False) -> bool:
        """
        Destroy a sandbox container.
        
        Args:
            sandbox_id: Sandbox agent ID
            force: Force kill if graceful stop fails
        
        Returns:
            True if destroyed successfully
        """
        agent = self._agents.get(sandbox_id)
        if not agent:
            return False
        
        agent.state = SandboxState.DESTROYING
        container = self._containers.get(sandbox_id)
        
        try:
            if container:
                if force:
                    container.kill()
                else:
                    container.stop(timeout=10)
                container.remove(force=True)
                logger.info(f"Destroyed sandbox {sandbox_id}")
        except NotFound:
            logger.warning(f"Container for {sandbox_id} already removed")
        except Exception as e:
            logger.error(f"Error destroying {sandbox_id}: {e}")
            return False
        finally:
            async with self._lock:
                self._agents.pop(sandbox_id, None)
                self._containers.pop(sandbox_id, None)
            agent.state = SandboxState.DESTROYED
        
        return True
    
    async def destroy_all(self) -> int:
        """Destroy all active sandboxes. Returns count destroyed."""
        sandbox_ids = list(self._agents.keys())
        destroyed = 0
        for sid in sandbox_ids:
            if await self.destroy(sid, force=True):
                destroyed += 1
        return destroyed
    
    async def get_logs(
        self,
        sandbox_id: str,
        tail: int = 100,
        since: Optional[float] = None
    ) -> str:
        """Get container logs."""
        container = self._containers.get(sandbox_id)
        if not container:
            return ""
        
        try:
            logs = container.logs(
                stdout=True,
                stderr=True,
                tail=tail,
                since=int(since) if since else None
            )
            return logs.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to get logs for {sandbox_id}: {e}")
            return ""
    
    def list_active(self) -> List[SandboxAgent]:
        """List all active sandbox agents."""
        return list(self._agents.values())
    
    def get_agent(self, sandbox_id: str) -> Optional[SandboxAgent]:
        """Get a specific sandbox agent."""
        return self._agents.get(sandbox_id)
    
    async def health_check(self, sandbox_id: str) -> bool:
        """Check if a sandbox is healthy and running."""
        agent = self._agents.get(sandbox_id)
        if not agent or not agent.container_id:
            return False
        
        container = self._containers.get(sandbox_id)
        if not container:
            return False
        
        try:
            container.reload()
            return container.status == "running"
        except NotFound:
            return False
    
    async def stats(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Get resource usage stats for a sandbox."""
        container = self._containers.get(sandbox_id)
        if not container:
            return None
        
        try:
            stats = container.stats(stream=False)
            return {
                "cpu_usage": stats.get("cpu_stats", {}),
                "memory_usage": stats.get("memory_stats", {}),
                "network": stats.get("networks", {}),
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {sandbox_id}: {e}")
            return None
    
    def __len__(self) -> int:
        return len(self._agents)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        """Cleanup on context exit."""
        asyncio.create_task(self.destroy_all())


class SandboxPool:
    """
    Manages a pool of pre-warmed sandbox containers for faster spawning.
    
    Useful for reducing latency when agents need to be spawned frequently.
    """
    
    def __init__(
        self,
        sandbox: DockerSandbox,
        min_size: int = 2,
        max_size: int = 10,
        tier: str = "T3"
    ):
        self.sandbox = sandbox
        self.min_size = min_size
        self.max_size = max_size
        self.tier = tier
        self._pool: List[SandboxAgent] = []
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Pre-warm the pool with idle containers."""
        for _ in range(self.min_size):
            agent = await self.sandbox.spawn(
                task="sleep 3600",  # Idle task
                tier=self.tier
            )
            async with self._lock:
                self._pool.append(agent)
        logger.info(f"Sandbox pool initialized with {len(self._pool)} containers")
    
    async def acquire(self) -> Optional[SandboxAgent]:
        """Get a sandbox from the pool (or spawn new if empty)."""
        async with self._lock:
            if self._pool:
                return self._pool.pop()
        
        # Pool empty, spawn new
        return await self.sandbox.spawn(tier=self.tier)
    
    async def release(self, agent: SandboxAgent) -> None:
        """Return a sandbox to the pool (or destroy if full)."""
        async with self._lock:
            if len(self._pool) < self.max_size:
                self._pool.append(agent)
                return
        
        # Pool full, destroy
        await self.sandbox.destroy(agent.sandbox_id)
    
    async def shutdown(self) -> None:
        """Destroy all pooled containers."""
        async with self._lock:
            for agent in self._pool:
                await self.sandbox.destroy(agent.sandbox_id)
            self._pool.clear()


# Export public API
__all__ = [
    "DockerSandbox",
    "SandboxPool",
    "SandboxConfig",
    "SandboxResult",
    "SandboxAgent",
    "SandboxState",
    "SandboxError",
    "SandboxSpawnError",
    "SandboxExecutionError",
]