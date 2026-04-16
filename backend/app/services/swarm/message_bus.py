"""
Intra-agent communication layer for swarm.

Provides a channel-based message bus using RabbitMQ or in-memory implementation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in the swarm."""
    TASK = "task"
    RESPONSE = "response"
    STATE_SYNC = "state_sync"
    CONSENSUS_VOTE = "consensus_vote"
    CONSULT = "consult"
    ALERT = "alert"
    ANNOUNCEMENT = "announcement"
    ERROR = "error"


@dataclass
class Envelope:
    """Message envelope with metadata."""
    message_id: str
    sender_id: str
    recipient_id: Optional[str]
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0
    ttl: int = 3600


class InMemoryMessageBus(MessageBus):
    """In-memory implementation of the message bus."""
    
    def __init__(self):
        self._inboxes: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._pending: Dict[str, List[Envelope]] = {}
    
    async def start(self) -> None:
        """Start the message bus."""
        self._running = True
        logger.info("In-memory message bus started")
    
    async def stop(self) -> None:
        """Stop the message bus."""
        self._running = False
        for queue in self._inboxes.values():
            queue.put_nowait(None)  # Poison pill
        self._subscribers.clear()
        logger.info("In-memory message bus stopped")
    
    def create_agent(self, agent_id: str) -> None:
        """Create a new agent inbox."""
        if agent_id not in self._inboxes:
            self._inboxes[agent_id] = asyncio.Queue()
            self._subscribers[agent_id] = []
            self._pending[agent_id] = []
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the bus."""
        self._inboxes.pop(agent_id, None)
        self._subscribers.pop(agent_id, None)
        self._pending.pop(agent_id, None)
    
    async def send(self, message: SwarmMessage) -> bool:
        """Send a message to its recipient(s)."""
        # Wrap in envelope
        envelope = Envelope(
            message_id=message.message_id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            message_type=MessageType(message.message_type),
            payload=message.payload
        )
        
        if envelope.recipient_id:
            # Send to specific recipient
            await self._deliver(envelope.recipient_id, envelope)
            message.delivered = True
            return True
        else:
            # Broadcast to subscribers
            count = await self.broadcast(message, scope=self._subscribers.keys())
            message.delivered = True
            return count > 0
    
    async def broadcast(self, message: SwarmMessage, scope: Optional[List[str]] = None) -> int:
        """Broadcast a message to multiple agents."""
        envelope = Envelope(
            message_id=message.message_id,
            sender_id=message.sender_id,
            recipient_id=None,
            message_type=MessageType(message.message_type),
            payload=message.payload
        )
        
        if scope is None:
            scope = list(self._inboxes.keys())
        
        count = 0
        async with self._lock:
            for agent_id in scope:
                await self._deliver(agent_id, envelope)
                count += 1
        
        return count
    
    async def _deliver(self, agent_id: str, envelope: Envelope) -> None:
        """Deliver a message to an agent."""
        if agent_id not in self._inboxes:
            logger.warning(f"Agent {agent_id} not found, dropping message")
            return
        
        # Check TTL
        if (datetime.now() - envelope.timestamp).total_seconds() > envelope.ttl:
            logger.debug(f"Message {envelope.message_id} expired (TTL check)")
            return
        
        # Check for listeners
        listeners = self._subscribers.get(agent_id, [])
        if listeners:
            for callback in listeners:
                try:
                    # Convert to SwarmMessage for callback
                    sw_msg = SwarmMessage(
                        message_id=envelope.message_id,
                        sender_id=envelope.sender_id,
                        recipient_id=envelope.recipient_id,
                        message_type=envelope.message_type.value,
                        payload=envelope.payload,
                        timestamp=envelope.timestamp
                    )
                    await callback(sw_msg)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")
        else:
            # Put in inbox for polling
            await self._inboxes[agent_id].put(envelope)
    
    async def subscribe(self, agent_id: str, callback: Callable[[SwarmMessage], Any]) -> None:
        """Subscribe an agent to receive messages."""
        if agent_id not in self._inboxes:
            self.create_agent(agent_id)
        
        self._subscribers.setdefault(agent_id, []).append(callback)
        logger.debug(f"Agent {agent_id} subscribed")
    
    async def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe an agent from messaging."""
        self._subscribers.pop(agent_id, None)
        logger.debug(f"Agent {agent_id} unsubscribed")
    
    async def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[SwarmMessage]:
        """Receive pending messages for an agent."""
        queue = self._inboxes.get(agent_id)
        if queue is None:
            return None
        
        try:
            # Poll with timeout
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            if message is None:
                return None  # Poison pill
            return message
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> int:
        """Publish to a topic (routing by topic)."""
        message = SwarmMessage(
            message_id=str(uuid.uuid4()),
            sender_id=f"{self.node_id}:pub",
            recipient_id=None,
            message_type="topic",
            payload={
                "topic": topic,
                "payload": payload,
                "priority": priority
            }
        )
        return await self.broadcast(message)
    
    async def subscribe_topic(
        self,
        topic: str,
        callback: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """Subscribe to a topic."""
        async def wrapper(msg: SwarmMessage):
            topic_data = msg.payload.get("topic")
            if topic_data == topic:
                await callback(msg.payload.get("payload", {}))
        
        await self.subscribe(topic, wrapper)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        active_agents = len(self._inboxes)
        subscriptions = sum(len(subs) for subs in self._subscribers.values())
        pending_messages = sum(
            len(queue._queue) if hasattr(queue, '_queue') else 0
            for queue in self._inboxes.values()
        )
        
        return {
            "active_agents": active_agents,
            "subscriptions": subscriptions,
            "pending_messages": pending_messages,
            "running": self._running
        }


class ChannelMessageBus(MessageBus):
    """
    Channel-based message bus using Redis Channels or RabbitMQ.
    
    This implementation uses Redis Pub/Sub for pub/sub messaging
    and Redis Streams for persistent messaging.
    """
    
    def __init__(self, connection_url: Optional[str] = None):
        self.connection_url = connection_url or "redis://localhost:6379/0"
        self._pubsub = None
        self._inboxes: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[asyncio.Task]] = {}
        self._running = False
        self._lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start the message bus."""
        try:
            import redis.asyncio as redis
            
            self._redis = redis.from_url(self.connection_url)
            await self._redis.ping()
            
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe("__swarm__#")
            
            self._running = True
            logger.info(f"Channel message bus started on {self.connection_url}")
            
            # Start background pubsub listener
            asyncio.create_task(self._pubsub_listener())
            
        except ImportError:
            logger.error("redis.asyncio not available, falling back to in-memory")
            self._in_memory = InMemoryMessageBus()
            await self._in_memory.start()
        except Exception as e:
            logger.error(f"Failed to start channel bus: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the message bus."""
        self._running = False
        
        if hasattr(self, '_pubsub') and self._pubsub:
            await self._pubsub.unsubscribe("__swarm__#")
            await self._pubsub.close()
        
        if hasattr(self, '_redis'):
            await self._redis.close()
        
        for task in self._subscribers.values():
            task.cancel()
        
        if hasattr(self, '_in_memory'):
            await self._in_memory.stop()
        
        logger.info("Channel message bus stopped")
    
    async def _pubsub_listener(self) -> None:
        """Listen for Redis pubsub messages."""
        if not self._pubsub:
            return
        
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        envelope = Envelope(**data)
                        
                        # Route to recipient or broadcast to subscribers
                        if envelope.recipient_id:
                            await self._deliver(envelope.recipient_id, envelope)
                        else:
                            # Broadcast to all subscribed agents
                            async with self._lock:
                                for agent_id, tasks in self._subscribers.items():
                                    for task in tasks:
                                        if not task.done():
                                            task.cancel()
                                        self._subscribers[agent_id].remove(task)
                                        asyncio.create_task(self._deliver(agent_id, envelope))
                    
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in pubsub message: {message}")
                    except Exception as e:
                        logger.error(f"Error processing pubsub message: {e}")
        except Exception as e:
            logger.error(f"Pubsub listener error: {e}")
    
    async def _deliver(self, agent_id: str, envelope: Envelope) -> None:
        """Deliver a message to an agent."""
        if agent_id not in self._inboxes:
            self.create_agent(agent_id)
        
        if (
            datetime.now() - envelope.timestamp
        ).total_seconds() > envelope.ttl:
            return
        
        await self._inboxes[agent_id].put(envelope)
    
    def create_agent(self, agent_id: str) -> None:
        """Create a new agent inbox."""
        if agent_id not in self._inboxes:
            self._inboxes[agent_id] = asyncio.Queue()
    
    async def send(self, message: SwarmMessage) -> bool:
        if hasattr(self, '_in_memory'):
            return await self._in_memory.send(message)
        
        envelope = Envelope(
            message_id=message.message_id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            message_type=MessageType(message.message_type),
            payload=message.payload
        )
        
        # Publish to Redis
        try:
            import redis.asyncio as redis
            if hasattr(self, '_redis'):
                data = json.dumps({
                    "message_id": envelope.message_id,
                    "sender_id": envelope.sender_id,
                    "recipient_id": envelope.recipient_id,
                    "message_type": envelope.message_type.value,
                    "payload": envelope.payload,
                    "timestamp": envelope.timestamp.isoformat(),
                    "priority": envelope.priority,
                    "ttl": envelope.ttl
                })
                
                # Determine channel pattern
                if envelope.recipient_id:
                    channel = f"__swarm__:to:{envelope.recipient_id}"
                else:
                    channel = "__swarm__:broadcast"
                
                await self._redis.publish(channel, data)
                message.delivered = True
                return True
        except Exception as e:
            logger.error(f"Error sending via Redis: {e}")
        
        return False
    
    async def broadcast(self, message: SwarmMessage, scope: Optional[List[str]] = None) -> int:
        if hasattr(self, '_in_memory'):
            return await self._in_memory.broadcast(message, scope)
        
        envelope = Envelope(
            message_id=message.message_id,
            sender_id=message.sender_id,
            recipient_id=None,
            message_type=MessageType(message.message_type),
            payload=message.payload
        )
        
        try:
            import redis.asyncio as redis
            if hasattr(self, '_redis'):
                data = json.dumps({
                    "message_id": envelope.message_id,
                    "sender_id": envelope.sender_id,
                    "recipient_id": envelope.recipient_id,
                    "message_type": envelope.message_type.value,
                    "payload": envelope.payload,
                    "timestamp": envelope.timestamp.isoformat(),
                    "priority": envelope.priority,
                    "ttl": envelope.ttl
                })
                
                count = 0
                if scope:
                    for agent_id in scope:
                        channel = f"__swarm__:to:{agent_id}"
                        await self._redis.publish(channel, data)
                        count += 1
                else:
                    await self._redis.publish("__swarm__:broadcast", data)
                    count = 1
                
                message.delivered = True
                return count
        except Exception as e:
            logger.error(f"Error broadcasting via Redis: {e}")
        
        return 0
    
    async def subscribe(self, agent_id: str, callback: Callable[[SwarmMessage], Any]) -> None:
        if hasattr(self, '_in_memory'):
            await self._in_memory.subscribe(agent_id, callback)
            return
        
        async def wrapper(msg: SwarmMessage):
            await callback(msg)
        
        self._subscribers[agent_id] = [asyncio.create_task(wrapper(None))]
    
    async def unsubscribe(self, agent_id: str) -> None:
        if hasattr(self, '_in_memory'):
            await self._in_memory.unsubscribe(agent_id)
            return
        
        for task in self._subscribers.pop(agent_id, []):
            task.cancel()
    
    async def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[SwarmMessage]:
        if hasattr(self, '_in_memory'):
            return await self._in_memory.receive(agent_id, timeout)
        
        queue = self._inboxes.get(agent_id)
        if queue is None:
            return None
        
        try:
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            return message
        except asyncio.TimeoutError:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        if hasattr(self, '_in_memory'):
            return self._in_memory.get_stats()
        
        return {
            "active_agents": len(self._inboxes),
            "subscriptions": len(self._subscribers),
            "pending_messages": sum(
                len(queue._queue) if hasattr(queue, '_queue') else 0
                for queue in self._inboxes.values()
            ),
            "running": self._running
        }


# Factory function for message bus creation
def create_message_bus(
    backend: str = "in-memory",
    connection_url: Optional[str] = None
) -> MessageBus:
    """Create a message bus with the specified backend."""
    if backend == "in-memory":
        bus = InMemoryMessageBus()
    elif backend == "channel":
        bus = ChannelMessageBus(connection_url)
    else:
        raise ValueError(f"Unknown message bus backend: {backend}")
    
    return bus
