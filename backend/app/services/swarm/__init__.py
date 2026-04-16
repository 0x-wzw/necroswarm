"""
Swarm Intelligence Module for Light_Agentic_Agent

This module provides swarm-native coordination capabilities including:
- Coordinator: Central orchestration of swarm agents with Docker sandbox support
- Consensus: Raft/gossip-based consensus implementations
- Message Bus: Inter-agent communication layer
- Role Manager: Agent specialization (orchestrator/worker/critic/memory/communicator)
- Swarm Memory: Cross-simulation persistent knowledge base
- Docker Sandbox: Ephemeral containerized agent execution
"""

from __future__ import annotations

from .coordinator import (
    AgentRole,
    AgentSpec,
    SwarmMessage,
    ConsensusVote,
    SwarmState,
    MessageBus,
    RoleManager,
    ConsensusEngine,
    SwarmCoordinator
)

from .consensus import (
    ConsensusState,
    ConsensusInstance,
    RaftProtocol,
    GossipProtocol,
    QuorumProtocol
)

from .message_bus import (
    MessageType,
    Envelope,
    InMemoryMessageBus,
    ChannelMessageBus,
    create_message_bus
)

from .role_manager import RoleTemplate

from .swarm_memory import SwarmMemory

from .docker_sandbox import (
    DockerSandbox,
    SandboxPool,
    SandboxConfig,
    SandboxResult,
    SandboxAgent,
    SandboxState,
    SandboxError,
    SandboxSpawnError,
    SandboxExecutionError
)

__all__ = [
    # Coordinator
    "AgentRole",
    "AgentSpec",
    "SwarmMessage",
    "ConsensusVote",
    "SwarmState",
    "MessageBus",
    "RoleManager",
    "ConsensusEngine",
    "SwarmCoordinator",
    "SwarmMemory",
    # Consensus
    "ConsensusState",
    "ConsensusInstance",
    "RaftProtocol",
    "GossipProtocol",
    "QuorumProtocol",
    # Message Bus
    "MessageType",
    "Envelope",
    "InMemoryMessageBus",
    "ChannelMessageBus",
    "create_message_bus",
    # Role Manager
    "RoleTemplate",
    # Docker Sandbox
    "DockerSandbox",
    "SandboxPool",
    "SandboxConfig",
    "SandboxResult",
    "SandboxAgent",
    "SandboxState",
    "SandboxError",
    "SandboxSpawnError",
    "SandboxExecutionError"
]

__version__ = "1.0.0"
__author__ = "Light_Agentic_Agent Team"
