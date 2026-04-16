"""
Docker Sandbox Usage Examples

Demonstrates how to use ephemeral containerized agents in the swarm system.
"""

import asyncio
from app.services.swarm import (
    SwarmCoordinator,
    AgentRole,
    AgentSpec,
    InMemoryMessageBus,
    RoleManager,
    ConsensusEngine
)


async def basic_ephemeral_example():
    """Example 1: Basic ephemeral agent execution."""
    
    # Create coordinator with Docker sandbox enabled
    message_bus = InMemoryMessageBus()
    role_manager = RoleManager(AgentSpec(
        agent_id="coordinator-1",
        role=AgentRole.ORCHESTRATOR,
        name="Swarm Coordinator",
        model="gpt-4"
    ))
    consensus = ConsensusEngine(message_bus)
    
    coordinator = SwarmCoordinator(
        swarm_id="demo-swarm-001",
        message_bus=message_bus,
        role_manager=role_manager,
        consensus_engine=consensus,
        enable_docker=True,  # Enable Docker sandbox
        docker_network="swarm-net"
    )
    
    await coordinator.start()
    
    # Spawn ephemeral T3 agent to run a simple task
    result = await coordinator.run_ephemeral_task(
        task="python -c 'print(\"Hello from ephemeral container!\")'",
        role=AgentRole.WORKER,
        tier="T3",
        cleanup=True  # Auto-destroy after completion
    )
    
    if result:
        print(f"Task completed: {result.success}")
        print(f"Output: {result.stdout}")
    
    await coordinator.stop()


async def tiered_execution_example():
    """Example 2: Different resource tiers for different tasks."""
    
    coordinator = SwarmCoordinator(
        swarm_id="tiered-swarm",
        message_bus=InMemoryMessageBus(),
        role_manager=RoleManager(AgentSpec(
            agent_id="coord",
            role=AgentRole.ORCHESTRATOR,
            name="Coordinator",
            model="gpt-4"
        )),
        consensus_engine=ConsensusEngine(InMemoryMessageBus()),
        enable_docker=True
    )
    
    await coordinator.start()
    
    # T3: Fast, lightweight task (web scraping, formatting)
    t3_task = await coordinator.run_ephemeral_task(
        task="python -c 'import json; print(json.dumps({\"status\": \"ok\"}))'",
        tier="T3"
    )
    print(f"T3 task: {t3_task.stdout if t3_task else 'failed'}")
    
    # T2: Medium complexity (data processing)
    t2_task = await coordinator.run_ephemeral_task(
        task="python -c 'import pandas as pd; print(\"Pandas available\")'",
        tier="T2"
    )
    print(f"T2 task: {t2_task.stdout if t2_task else 'failed'}")
    
    # T1: Heavy computation (ML inference, complex analysis)
    t1_task = await coordinator.run_ephemeral_task(
        task="python -c 'import torch; print(f\"PyTorch {torch.__version__}\")'",
        tier="T1"
    )
    print(f"T1 task: {t1_task.stdout if t1_task else 'failed'}")
    
    await coordinator.stop()


async def manual_lifecycle_example():
    """Example 3: Manual lifecycle management for long-running agents."""
    
    coordinator = SwarmCoordinator(
        swarm_id="manual-swarm",
        message_bus=InMemoryMessageBus(),
        role_manager=RoleManager(AgentSpec(
            agent_id="coord",
            role=AgentRole.ORCHESTRATOR,
            name="Coordinator",
            model="gpt-4"
        )),
        consensus_engine=ConsensusEngine(InMemoryMessageBus()),
        enable_docker=True
    )
    
    await coordinator.start()
    
    # Spawn agent manually (no cleanup)
    agent = await coordinator.spawn_ephemeral_agent(
        task="sleep 300",  # Long-running background task
        role=AgentRole.WORKER,
        tier="T2"
    )
    
    if agent:
        print(f"Agent spawned: {agent.sandbox_id}")
        
        # Check health
        healthy = await coordinator.get_sandbox_health(agent.sandbox_id)
        print(f"Agent healthy: {healthy}")
        
        # Execute additional commands
        result = await coordinator.execute_in_sandbox(
            sandbox_id=agent.sandbox_id,
            command="echo 'Running in background'"
        )
        print(f"Command result: {result.stdout if result else 'failed'}")
        
        # Clean up when done
        await asyncio.sleep(1)  # Let task run briefly
        await coordinator.destroy_ephemeral_agent(agent.sandbox_id, force=True)
    
    await coordinator.stop()


async def parallel_ephemeral_example():
    """Example 4: Spawn multiple ephemeral agents in parallel."""
    
    coordinator = SwarmCoordinator(
        swarm_id="parallel-swarm",
        message_bus=InMemoryMessageBus(),
        role_manager=RoleManager(AgentSpec(
            agent_id="coord",
            role=AgentRole.ORCHESTRATOR,
            name="Coordinator",
            model="gpt-4"
        )),
        consensus_engine=ConsensusEngine(InMemoryMessageBus()),
        enable_docker=True
    )
    
    await coordinator.start()
    
    # Spawn 5 parallel T3 agents
    tasks = [
        coordinator.run_ephemeral_task(
            task=f"python -c 'print(\"Worker {i} done\")'",
            tier="T3"
        )
        for i in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        if result:
            print(f"Worker {i}: {result.stdout.strip()}")
    
    # Get stats
    stats = coordinator.get_stats()
    print(f"\nSwarm stats: {stats}")
    
    await coordinator.stop()


if __name__ == "__main__":
    print("=" * 60)
    print("Docker Sandbox Examples")
    print("=" * 60)
    
    # Run examples
    print("\n1. Basic Ephemeral Example:")
    asyncio.run(basic_ephemeral_example())
    
    print("\n2. Tiered Execution Example:")
    asyncio.run(tiered_execution_example())
    
    print("\n3. Manual Lifecycle Example:")
    asyncio.run(manual_lifecycle_example())
    
    print("\n4. Parallel Ephemeral Example:")
    asyncio.run(parallel_ephemeral_example())
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)