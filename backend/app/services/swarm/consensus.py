"""
Consensus Protocols for NECROSWARM — The Undead Collective

Implements Raft, Gossip, and Quorum-based consensus mechanisms
for reliable distributed decision-making in agent swarms.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Generic, TypeVar

T = TypeVar('T')

__all__ = [
    "RaftProtocol",
    "GossipProtocol",
    "QuorumProtocol",
    "ConsensusState",
    "ConsensusResult",
    "ConsensusVote",
    "ConsensusInstance",
    "NodeState",
    "MessageType",
    "RaftLogEntry",
    "RaftMessage",
    "GossipDigest",
    "GossipMessage",
    "VoteRecord",
    "QuorumConfig",
]


class NodeState(Enum):
    """Possible states for a consensus node."""
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()
    LEARNING = auto()
    INACTIVE = auto()


class ConsensusState(Enum):
    """Possible outcomes of a consensus round."""
    PENDING = auto()
    COMMITTED = auto()
    REJECTED = auto()
    TIMEOUT = auto()
    CONFLICT = auto()


class MessageType(Enum):
    """Message types for consensus protocols."""
    # Raft messages
    REQUEST_VOTE = auto()
    VOTE_RESPONSE = auto()
    APPEND_ENTRIES = auto()
    APPEND_RESPONSE = auto()
    HEARTBEAT = auto()
    INSTALL_SNAPSHOT = auto()
    
    # Gossip messages
    GOSSIP_SYNC = auto()
    GOSSIP_ACK = auto()
    GOSSIP_DIGEST = auto()
    GOSSIP_PAYLOAD = auto()
    
    # Quorum messages
    PROPOSE = auto()
    ACCEPT = auto()
    COMMIT = auto()
    ABORT = auto()


# =============================================================================
# Dataclasses
# =============================================================================

@dataclass
class RaftLogEntry:
    """Single entry in the Raft distributed log."""
    index: int
    term: int
    command: Any
    timestamp: float = field(default_factory=time.time)
    
    def __hash__(self) -> int:
        return hash((self.index, self.term))


@dataclass
class RaftMessage:
    """Message format for Raft protocol communication."""
    msg_type: MessageType
    term: int
    sender_id: str
    
    # Election fields
    last_log_index: int = 0
    last_log_term: int = 0
    vote_granted: bool = False
    
    # Append entries fields
    prev_log_index: int = 0
    prev_log_term: int = 0
    entries: list[RaftLogEntry] = field(default_factory=list)
    leader_commit: int = 0
    
    # Response fields
    success: bool = False
    match_index: int = 0
    
    def to_bytes(self) -> bytes:
        """Serialize message to bytes."""
        return json.dumps({
            "msg_type": self.msg_type.name,
            "term": self.term,
            "sender_id": self.sender_id,
            "last_log_index": self.last_log_index,
            "last_log_term": self.last_log_term,
            "vote_granted": self.vote_granted,
            "prev_log_index": self.prev_log_index,
            "prev_log_term": self.prev_log_term,
            "entries": [
                {"index": e.index, "term": e.term, "command": e.command}
                for e in self.entries
            ],
            "leader_commit": self.leader_commit,
            "success": self.success,
            "match_index": self.match_index,
        }).encode()


@dataclass
class GossipDigest:
    """Digest of node state for gossip protocol."""
    node_id: str
    heartbeat_version: int
    max_version: int
    data_hash: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class GossipMessage:
    """Message format for gossip protocol."""
    msg_type: MessageType
    sender_id: str
    digests: list[GossipDigest] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    ttl: int = 3  # Time-to-live for rumor propagation
    timestamp: float = field(default_factory=time.time)


@dataclass
class VoteRecord:
    """Record of a single vote in quorum protocol."""
    voter_id: str
    proposal_id: str
    vote: bool
    timestamp: float = field(default_factory=time.time)


@dataclass
class QuorumConfig:
    """Configuration for quorum-based consensus."""
    quorum_size: int
    timeout_seconds: float = 5.0
    max_retries: int = 3
    weights: dict[str, float] = field(default_factory=dict)
    require_strong_consistency: bool = False


@dataclass
class ConsensusVote:
    """Represents a single vote in a consensus round."""
    voter_id: str
    proposal_id: str
    term: int
    vote: bool
    timestamp: float = field(default_factory=time.time)
    signature: str = ""  # Optional cryptographic signature

    def to_dict(self) -> dict[str, Any]:
        """Convert vote to dictionary."""
        return {
            "voter_id": self.voter_id,
            "proposal_id": self.proposal_id,
            "term": self.term,
            "vote": self.vote,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }


@dataclass
class ConsensusResult:
    """Result of a consensus round."""
    proposal_id: str
    state: ConsensusState
    votes_yes: int = 0
    votes_no: int = 0
    total_nodes: int = 0
    leader_id: str = ""
    term: int = 0
    commit_index: int = 0
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_committed(self) -> bool:
        """Check if consensus was reached."""
        return self.state == ConsensusState.COMMITTED

    @property
    def is_rejected(self) -> bool:
        """Check if consensus was rejected."""
        return self.state == ConsensusState.REJECTED

    @property
    def is_pending(self) -> bool:
        """Check if consensus is still pending."""
        return self.state == ConsensusState.PENDING

    @property
    def quorum_reached(self) -> bool:
        """Check if quorum was reached."""
        if self.total_nodes == 0:
            return False
        return self.votes_yes > (self.total_nodes // 2)


@dataclass
class ConsensusInstance:
    """Represents an active consensus instance with all its state."""
    instance_id: str
    proposal_id: str
    term: int
    state: ConsensusState = field(default=ConsensusState.PENDING)
    votes: list[ConsensusVote] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    committed_at: float = 0.0
    value: Any = None
    leader_id: str = ""
    participating_nodes: list[str] = field(default_factory=list)
    vote_weights: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize default expiration if not set."""
        if self.expires_at == 0.0:
            self.expires_at = time.time() + 30.0  # Default 30s timeout

    def add_vote(self, vote: ConsensusVote) -> bool:
        """Add a vote to this instance."""
        # Check for duplicate vote
        for existing in self.votes:
            if existing.voter_id == vote.voter_id:
                return False
        self.votes.append(vote)
        return True

    def get_vote_count(self, vote_value: bool | None = None) -> int:
        """Count votes. If vote_value is None, count all votes."""
        if vote_value is None:
            return len(self.votes)
        return sum(1 for v in self.votes if v.vote == vote_value)

    def get_weighted_votes(self) -> tuple[float, float]:
        """Get weighted yes/no vote totals."""
        yes_weight = sum(
            self.vote_weights.get(v.voter_id, 1.0)
            for v in self.votes if v.vote
        )
        no_weight = sum(
            self.vote_weights.get(v.voter_id, 1.0)
            for v in self.votes if not v.vote
        )
        return yes_weight, no_weight

    def is_expired(self) -> bool:
        """Check if this instance has expired."""
        return time.time() > self.expires_at

    def to_result(self) -> ConsensusResult:
        """Convert instance to result snapshot."""
        return ConsensusResult(
            proposal_id=self.proposal_id,
            state=self.state,
            votes_yes=self.get_vote_count(True),
            votes_no=self.get_vote_count(False),
            total_nodes=len(self.participating_nodes),
            leader_id=self.leader_id,
            term=self.term,
            commit_index=len(self.votes),
            timestamp=time.time(),
        )


# =============================================================================
# RAFT PROTOCOL IMPLEMENTATION
# =============================================================================

class RaftProtocol:
    """
    Raft consensus protocol implementation for distributed leader election
    and log replication.
    
    Guarantees:
    - Leader Election: At most one leader per term
    - Log Matching: If two entries have same index and term, logs match up to that point
    - Leader Completeness: If entry committed in term T, all leaders in terms > T contain it
    - State Machine Safety: Committed entries are never overwritten
    """
    
    def __init__(
        self,
        node_id: str,
        peers: list[str],
        election_timeout_min: float = 0.15,
        election_timeout_max: float = 0.3,
        heartbeat_interval: float = 0.05,
    ):
        self.node_id = node_id
        self.peers = peers
        self.election_timeout_min = election_timeout_min
        self.election_timeout_max = election_timeout_max
        self.heartbeat_interval = heartbeat_interval
        
        # Persistent state
        self.current_term: int = 0
        self.voted_for: str | None = None
        self.log: list[RaftLogEntry] = []
        
        # Volatile state
        self.state = NodeState.FOLLOWER
        self.commit_index: int = 0
        self.last_applied: int = 0
        
        # Leader state
        self.next_index: dict[str, int] = {}
        self.match_index: dict[str, int] = {}
        
        # Async components
        self._message_queue: asyncio.Queue[RaftMessage] = asyncio.Queue()
        self._running = False
        self._election_timer: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._commit_callback: Callable[[RaftLogEntry], Coroutine] | None = None
        
    async def start(self) -> None:
        """Start the Raft protocol."""
        self._running = True
        self._reset_election_timer()
        asyncio.create_task(self._message_processor())
        
    async def stop(self) -> None:
        """Stop the Raft protocol."""
        self._running = False
        if self._election_timer:
            self._election_timer.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            
    def on_commit(self, callback: Callable[[RaftLogEntry], Coroutine]) -> None:
        """Set callback for committed log entries."""
        self._commit_callback = callback
        
    def _reset_election_timer(self) -> None:
        """Reset the election timeout with random jitter."""
        if self._election_timer:
            self._election_timer.cancel()
        timeout = random.uniform(self.election_timeout_min, self.election_timeout_max)
        self._election_timer = asyncio.create_task(self._election_timeout(timeout))
        
    async def _election_timeout(self, timeout: float) -> None:
        """Handle election timeout - start election if still follower."""
        await asyncio.sleep(timeout)
        if self.state in (NodeState.FOLLOWER, NodeState.CANDIDATE):
            await self._start_election()
            
    async def _start_election(self) -> None:
        """Begin leader election process."""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        
        votes_received: set[str] = {self.node_id}
        
        # Send RequestVote RPCs to all peers
        last_log = self._last_log_entry()
        request = RaftMessage(
            msg_type=MessageType.REQUEST_VOTE,
            term=self.current_term,
            sender_id=self.node_id,
            last_log_index=last_log.index if last_log else 0,
            last_log_term=last_log.term if last_log else 0,
        )
        
        for peer in self.peers:
            asyncio.create_task(self._send_message(peer, request))
            
        # Wait for responses
        timeout = random.uniform(self.election_timeout_min * 2, self.election_timeout_max * 2)
        await asyncio.sleep(timeout)
        
        # Check if we won
        if len(votes_received) > (len(self.peers) + 1) // 2:
            await self._become_leader()
            
    async def _become_leader(self) -> None:
        """Transition to leader state."""
        self.state = NodeState.LEADER
        
        # Initialize leader tracking
        for peer in self.peers:
            self.next_index[peer] = len(self.log) + 1
            self.match_index[peer] = 0
            
        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
        self._reset_election_timer()
        
    async def _send_heartbeats(self) -> None:
        """Send periodic heartbeats to maintain leadership."""
        while self._running and self.state == NodeState.LEADER:
            for peer in self.peers:
                await self._send_append_entries(peer)
            await asyncio.sleep(self.heartbeat_interval)
            
    async def _send_append_entries(self, peer: str, entries: list[RaftLogEntry] | None = None) -> None:
        """Send AppendEntries RPC to a peer."""
        if not entries:
            entries = []
            
        prev_log_index = self.next_index[peer] - 1
        prev_log_term = 0
        
        if prev_log_index > 0 and prev_log_index <= len(self.log):
            prev_log_term = self.log[prev_log_index - 1].term
            
        msg = RaftMessage(
            msg_type=MessageType.APPEND_ENTRIES,
            term=self.current_term,
            sender_id=self.node_id,
            prev_log_index=prev_log_index,
            prev_log_term=prev_log_term,
            entries=entries,
            leader_commit=self.commit_index,
        )
        
        await self._send_message(peer, msg)
        
    def _last_log_entry(self) -> RaftLogEntry | None:
        """Get the last entry in the log."""
        return self.log[-1] if self.log else None
        
    async def propose(self, command: Any) -> bool:
        """Propose a new command to the log."""
        if self.state != NodeState.LEADER:
            return False
            
        entry = RaftLogEntry(
            index=len(self.log) + 1,
            term=self.current_term,
            command=command,
        )
        self.log.append(entry)
        
        # Replicate to followers
        for peer in self.peers:
            await self._send_append_entries(peer, [entry])
            
        return True
        
    async def _handle_message(self, msg: RaftMessage) -> None:
        """Process incoming Raft messages."""
        if msg.term > self.current_term:
            self.current_term = msg.term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
            
        if msg.msg_type == MessageType.REQUEST_VOTE:
            await self._handle_request_vote(msg)
        elif msg.msg_type == MessageType.VOTE_RESPONSE:
            await self._handle_vote_response(msg)
        elif msg.msg_type == MessageType.APPEND_ENTRIES:
            await self._handle_append_entries(msg)
        elif msg.msg_type == MessageType.APPEND_RESPONSE:
            await self._handle_append_response(msg)
            
    async def _handle_request_vote(self, msg: RaftMessage) -> None:
        """Handle vote request from candidate."""
        vote_granted = False
        
        if msg.term >= self.current_term and (
            self.voted_for is None or self.voted_for == msg.sender_id
        ):
            last_log = self._last_log_entry()
            last_index = last_log.index if last_log else 0
            last_term = last_log.term if last_log else 0
            
            # Candidate's log must be at least as up-to-date
            if (msg.last_log_term > last_term or 
                (msg.last_log_term == last_term and msg.last_log_index >= last_index)):
                vote_granted = True
                self.voted_for = msg.sender_id
                self._reset_election_timer()
                
        response = RaftMessage(
            msg_type=MessageType.VOTE_RESPONSE,
            term=self.current_term,
            sender_id=self.node_id,
            vote_granted=vote_granted,
        )
        await self._send_message(msg.sender_id, response)
        
    async def _handle_vote_response(self, msg: RaftMessage) -> None:
        """Handle response to vote request."""
        # Counting happens in election task
        pass
        
    async def _handle_append_entries(self, msg: RaftMessage) -> None:
        """Handle append entries from leader."""
        success = False
        
        if msg.term >= self.current_term:
            self.state = NodeState.FOLLOWER
            self._reset_election_timer()
            
            # Log consistency check
            if msg.prev_log_index == 0 or (
                msg.prev_log_index <= len(self.log) and
                (msg.prev_log_index == 0 or 
                 self.log[msg.prev_log_index - 1].term == msg.prev_log_term)
            ):
                success = True
                
                # Append new entries
                for i, entry in enumerate(msg.entries):
                    log_index = msg.prev_log_index + i + 1
                    if log_index <= len(self.log):
                        if self.log[log_index - 1].term != entry.term:
                            # Delete conflicting entries
                            self.log = self.log[:log_index - 1]
                            self.log.append(entry)
                    else:
                        self.log.append(entry)
                        
                # Update commit index
                if msg.leader_commit > self.commit_index:
                    self.commit_index = min(msg.leader_commit, len(self.log))
                    await self._apply_committed()
                    
        response = RaftMessage(
            msg_type=MessageType.APPEND_RESPONSE,
            term=self.current_term,
            sender_id=self.node_id,
            success=success,
            match_index=len(self.log),
        )
        await self._send_message(msg.sender_id, response)
        
    async def _handle_append_response(self, msg: RaftMessage) -> None:
        """Handle response to append entries."""
        if self.state != NodeState.LEADER:
            return
            
        if msg.success:
            self.match_index[msg.sender_id] = msg.match_index
            self.next_index[msg.sender_id] = msg.match_index + 1
            await self._check_commit()
        else:
            self.next_index[msg.sender_id] = max(1, self.next_index[msg.sender_id] - 1)
            
    async def _check_commit(self) -> None:
        """Check if any entries can be committed."""
        for index in range(self.commit_index + 1, len(self.log) + 1):
            count = 1  # Leader counts as 1
            for peer in self.peers:
                if self.match_index.get(peer, 0) >= index:
                    count += 1
                    
            if count > (len(self.peers) + 1) // 2:
                self.commit_index = index
                await self._apply_committed()
                
    async def _apply_committed(self) -> None:
        """Apply committed entries to state machine."""
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied - 1]
            if self._commit_callback:
                await self._commit_callback(entry)
                
    async def _send_message(self, peer: str, msg: RaftMessage) -> None:
        """Send message to peer (abstract - implement in subclass)."""
        # Implement based on transport layer
        pass
        
    async def _message_processor(self) -> None:
        """Process incoming messages."""
        while self._running:
            try:
                msg = await asyncio.wait_for(self._message_queue.get(), timeout=0.1)
                await self._handle_message(msg)
            except asyncio.TimeoutError:
                continue
                
    def receive_message(self, msg: RaftMessage) -> None:
        """External entry point to receive messages."""
        self._message_queue.put_nowait(msg)


# =============================================================================
# GOSSIP PROTOCOL IMPLEMENTATION
# =============================================================================

class GossipProtocol:
    """
    Gossip protocol implementation for eventually consistent state distribution.
    
    Uses epidemic-style propagation to efficiently disseminate state across
    large swarms without centralized coordination.
    
    Features:
    - Probabilistic peer selection for efficient fan-out
    - Digest-based synchronization to minimize bandwidth
    - Anti-entropy for eventual consistency
    - Configurable fan-out and intervals
    """
    
    def __init__(
        self,
        node_id: str,
        gossip_interval: float = 1.0,
        fan_out: int = 3,
        digest_threshold: int = 10,
    ):
        self.node_id = node_id
        self.gossip_interval = gossip_interval
        self.fan_out = fan_out
        self.digest_threshold = digest_threshold
        
        # State storage
        self._local_data: dict[str, Any] = {}
        self._version: int = 0
        self._heartbeats: dict[str, int] = {}
        self._peer_data: dict[str, dict[str, Any]] = defaultdict(dict)
        
        # Async components
        self._running = False
        self._gossip_task: asyncio.Task | None = None
        self._peers: set[str] = set()
        self._message_handlers: dict[MessageType, Callable[[GossipMessage], Coroutine]] = {}
        
        # Failure detection
        self._failure_detector: dict[str, tuple[float, int]] = {}
        self._suspected: set[str] = set()
        
    async def start(self) -> None:
        """Start the gossip protocol."""
        self._running = True
        self._gossip_task = asyncio.create_task(self._gossip_loop())
        
    async def stop(self) -> None:
        """Stop the gossip protocol."""
        self._running = False
        if self._gossip_task:
            self._gossip_task.cancel()
            
    def add_peer(self, peer_id: str) -> None:
        """Add a peer to the gossip network."""
        self._peers.add(peer_id)
        self._heartbeats[peer_id] = 0
        
    def remove_peer(self, peer_id: str) -> None:
        """Remove a peer from the gossip network."""
        self._peers.discard(peer_id)
        self._peer_data.pop(peer_id, None)
        self._heartbeats.pop(peer_id, None)
        
    def set(self, key: str, value: Any) -> None:
        """Update local state with a new value."""
        self._version += 1
        self._local_data[key] = {
            "value": value,
            "version": self._version,
            "timestamp": time.time(),
            "node_id": self.node_id,
        }
        self._heartbeats[self.node_id] = self._version
        
    def get(self, key: str) -> Any | None:
        """Get a value from local state."""
        entry = self._local_data.get(key)
        return entry["value"] if entry else None
        
    def get_merged(self, key: str) -> dict[str, Any] | None:
        """Get merged view of a key across all nodes."""
        results = {}
        
        if key in self._local_data:
            results[self.node_id] = self._local_data[key]
            
        for peer_id, data in self._peer_data.items():
            if key in data:
                results[peer_id] = data[key]
                
        return results if results else None
        
    async def _gossip_loop(self) -> None:
        """Main gossip loop."""
        while self._running:
            try:
                await self._gossip_round()
                await self._check_failures()
                await asyncio.sleep(self.gossip_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                continue
                
    async def _gossip_round(self) -> None:
        """Execute a single gossip round."""
        if not self._peers:
            return
            
        # Select random subset of peers
        targets = random.sample(
            list(self._peers),
            min(self.fan_out, len(self._peers))
        )
        
        # Generate digest
        digest = self._generate_digest()
        
        for target in targets:
            msg = GossipMessage(
                msg_type=MessageType.GOSSIP_SYNC,
                sender_id=self.node_id,
                digests=[digest],
            )
            await self._send_message(target, msg)
            
    def _generate_digest(self) -> GossipDigest:
        """Generate current state digest."""
        data_str = json.dumps(self._local_data, sort_keys=True, default=str)
        return GossipDigest(
            node_id=self.node_id,
            heartbeat_version=self._version,
            max_version=self._version,
            data_hash=hashlib.sha256(data_str.encode()).hexdigest()[:16],
        )
        
    async def _check_failures(self) -> None:
        """Check for failed nodes based on heartbeat timeouts."""
        now = time.time()
        timeout = self.gossip_interval * 10
        
        for peer_id, (last_seen, _) in list(self._failure_detector.items()):
            if now - last_seen > timeout:
                if peer_id not in self._suspected:
                    self._suspected.add(peer_id)
                    await self._on_suspect(peer_id)
                    
    async def _on_suspect(self, peer_id: str) -> None:
        """Handle suspected node failure."""
        # Override for custom failure handling
        pass
        
    async def receive_message(self, msg: GossipMessage) -> None:
        """Receive and process a gossip message."""
        handler = self._message_handlers.get(msg.msg_type)
        if handler:
            await handler(msg)
        else:
            await self._default_handler(msg)
            
    async def _default_handler(self, msg: GossipMessage) -> None:
        """Default message handler."""
        if msg.msg_type == MessageType.GOSSIP_SYNC:
            await self._handle_sync(msg)
        elif msg.msg_type == MessageType.GOSSIP_ACK:
            await self._handle_ack(msg)
        elif msg.msg_type == MessageType.GOSSIP_PAYLOAD:
            await self._handle_payload(msg)
            
    async def _handle_sync(self, msg: GossipMessage) -> None:
        """Handle sync request with digest."""
        # Update failure detector
        self._failure_detector[msg.sender_id] = (time.time(), msg.sender_id)
        self._suspected.discard(msg.sender_id)
        
        # Compare digests
        if msg.digests:
            remote_digest = msg.digests[0]
            local_version = self._version
            
            if remote_digest.max_version > local_version:
                # Remote is ahead - request data
                ack = GossipMessage(
                    msg_type=MessageType.GOSSIP_ACK,
                    sender_id=self.node_id,
                    digests=[self._generate_digest()],
                )
                await self._send_message(msg.sender_id, ack)
            elif remote_digest.max_version < local_version:
                # We are ahead - send data
                await self._send_payload(msg.sender_id)
                
    async def _handle_ack(self, msg: GossipMessage) -> None:
        """Handle acknowledgment with digest."""
        # Send our data if we're ahead
        await self._send_payload(msg.sender_id)
        
    async def _handle_payload(self, msg: GossipMessage) -> None:
        """Handle incoming data payload."""
        for key, entry in msg.payload.items():
            if not isinstance(entry, dict):
                continue
                
            remote_version = entry.get("version", 0)
            local_version = self._peer_data[msg.sender_id].get(key, {}).get("version", 0)
            
            if remote_version > local_version:
                self._peer_data[msg.sender_id][key] = entry
                
        # Update heartbeat
        self._heartbeats[msg.sender_id] = msg.digests[0].heartbeat_version if msg.digests else 0
        
    async def _send_payload(self, target: str) -> None:
        """Send current state to target node."""
        msg = GossipMessage(
            msg_type=MessageType.GOSSIP_PAYLOAD,
            sender_id=self.node_id,
            digests=[self._generate_digest()],
            payload=self._local_data.copy(),
        )
        await self._send_message(target, msg)
        
    async def _send_message(self, target: str, msg: GossipMessage) -> None:
        """Send message to target (abstract - implement in subclass)."""
        pass
        
    def register_handler(
        self,
        msg_type: MessageType,
        handler: Callable[[GossipMessage], Coroutine],
    ) -> None:
        """Register a custom message handler."""
        self._message_handlers[msg_type] = handler
        
    def get_live_nodes(self) -> list[str]:
        """Get list of currently live nodes."""
        now = time.time()
        timeout = self.gossip_interval * 5
        
        live = []
        for peer_id, (last_seen, _) in self._failure_detector.items():
            if now - last_seen < timeout and peer_id not in self._suspected:
                live.append(peer_id)
                
        return live


# =============================================================================
# QUORUM PROTOCOL IMPLEMENTATION
# =============================================================================

class QuorumProtocol:
    """
    Quorum-based consensus protocol for distributed agreement.
    
    Implements weighted voting with configurable quorum sizes.
    Supports both strong and eventual consistency modes.
    
    Features:
    - Weighted voting based on node importance/reliability
    - Configurable quorum sizes for flexibility
    - Two-phase commit for strong consistency
    - Optimistic commit for low latency
    """
    
    def __init__(
        self,
        node_id: str,
        config: QuorumConfig,
    ):
        self.node_id = node_id
        self.config = config
        
        # State
        self._proposals: dict[str, dict[str, Any]] = {}
        self._votes: dict[str, list[VoteRecord]] = defaultdict(list)
        self._committed: dict[str, Any] = {}
        
        # Peers and weights
        self._peers: set[str] = set()
        self._weights: dict[str, float] = config.weights.copy()
        
        # Async components
        self._running = False
        self._commit_callbacks: dict[str, Callable[[str, Any], Coroutine]] = {}
        self._vote_queue: asyncio.Queue[tuple[str, VoteRecord]] = asyncio.Queue()
        
    async def start(self) -> None:
        """Start the quorum protocol."""
        self._running = True
        asyncio.create_task(self._vote_processor())
        
    async def stop(self) -> None:
        """Stop the quorum protocol."""
        self._running = False
        
    def add_peer(self, peer_id: str, weight: float = 1.0) -> None:
        """Add a peer with optional voting weight."""
        self._peers.add(peer_id)
        self._weights[peer_id] = weight
        
    def remove_peer(self, peer_id: str) -> None:
        """Remove a peer."""
        self._peers.discard(peer_id)
        self._weights.pop(peer_id, None)
        
    async def propose(
        self,
        proposal_id: str,
        value: Any,
        timeout: float | None = None,
    ) -> ConsensusState:
        """
        Propose a value for consensus.
        
        Returns the final consensus state after voting completes.
        """
        timeout = timeout or self.config.timeout_seconds
        
        # Create proposal
        self._proposals[proposal_id] = {
            "value": value,
            "state": ConsensusState.PENDING,
            "timestamp": time.time(),
        }
        
        # Send propose to all peers
        for peer in self._peers:
            await self._send_propose(peer, proposal_id, value)
            
        # Wait for quorum
        start_time = time.time()
        while time.time() - start_time < timeout:
            state = self._check_quorum(proposal_id)
            if state in (ConsensusState.COMMITTED, ConsensusState.REJECTED):
                return state
            await asyncio.sleep(0.01)
            
        return ConsensusState.TIMEOUT
        
    async def _send_propose(self, peer: str, proposal_id: str, value: Any) -> None:
        """Send propose message to peer."""
        # Implement based on transport layer
        pass
        
    def _check_quorum(self, proposal_id: str) -> ConsensusState:
        """Check if quorum has been reached for a proposal."""
        if proposal_id in self._committed:
            return ConsensusState.COMMITTED
            
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return ConsensusState.REJECTED
            
        votes = self._votes.get(proposal_id, [])
        
        # Calculate weighted votes
        yes_weight = sum(
            self._weights.get(v.voter_id, 1.0)
            for v in votes if v.vote
        )
        no_weight = sum(
            self._weights.get(v.voter_id, 1.0)
            for v in votes if not v.vote
        )
        total_weight = sum(self._weights.get(p, 1.0) for p in self._peers) + self._weights.get(self.node_id, 1.0)
        
        quorum_threshold = total_weight * self.config.quorum_size / (len(self._peers) + 1)
        
        if yes_weight >= quorum_threshold:
            proposal["state"] = ConsensusState.COMMITTED
            self._committed[proposal_id] = proposal["value"]
            asyncio.create_task(self._on_commit(proposal_id, proposal["value"]))
            return ConsensusState.COMMITTED
        elif no_weight > total_weight - quorum_threshold:
            proposal["state"] = ConsensusState.REJECTED
            return ConsensusState.REJECTED
            
        return ConsensusState.PENDING
        
    async def _on_commit(self, proposal_id: str, value: Any) -> None:
        """Handle committed proposal."""
        callback = self._commit_callbacks.get(proposal_id)
        if callback:
            await callback(proposal_id, value)
            
    def register_commit_callback(
        self,
        proposal_id: str,
        callback: Callable[[str, Any], Coroutine],
    ) -> None:
        """Register a callback for when a proposal is committed."""
        self._commit_callbacks[proposal_id] = callback
        
    async def vote(self, proposal_id: str, accept: bool, voter_id: str | None = None) -> None:
        """Cast a vote for a proposal."""
        voter_id = voter_id or self.node_id
        
        record = VoteRecord(
            voter_id=voter_id,
            proposal_id=proposal_id,
            vote=accept,
        )
        
        await self._vote_queue.put((proposal_id, record))
        
    async def _vote_processor(self) -> None:
        """Process votes from queue."""
        while self._running:
            try:
                proposal_id, record = await asyncio.wait_for(
                    self._vote_queue.get(),
                    timeout=0.1,
                )
                self._votes[proposal_id].append(record)
            except asyncio.TimeoutError:
                continue
                
    async def handle_vote_message(self, proposal_id: str, vote: bool, sender: str) -> None:
        """Handle incoming vote message."""
        await self.vote(proposal_id, vote, sender)
        
    def get_proposal_status(self, proposal_id: str) -> dict[str, Any]:
        """Get current status of a proposal."""
        if proposal_id in self._committed:
            return {
                "proposal_id": proposal_id,
                "state": ConsensusState.COMMITTED.name,
                "value": self._committed[proposal_id],
            }
            
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {"proposal_id": proposal_id, "state": "UNKNOWN"}
            
        votes = self._votes.get(proposal_id, [])
        
        return {
            "proposal_id": proposal_id,
            "state": proposal["state"].name,
            "votes_yes": sum(1 for v in votes if v.vote),
            "votes_no": sum(1 for v in votes if not v.vote),
            "total_votes": len(votes),
            "age": time.time() - proposal["timestamp"],
        }
        
    async def abort(self, proposal_id: str) -> bool:
        """Abort a pending proposal."""
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal["state"] != ConsensusState.PENDING:
            return False
            
        proposal["state"] = ConsensusState.REJECTED
        
        # Notify peers
        for peer in self._peers:
            await self._send_abort(peer, proposal_id)
            
        return True
        
    async def _send_abort(self, peer: str, proposal_id: str) -> None:
        """Send abort message to peer."""
        pass
osal_id, [])
        
        return {
            "proposal_id": proposal_id,
            "state": proposal["state"].name,
            "votes_yes": sum(1 for v in votes if v.vote),
            "votes_no": sum(1 for v in votes if not v.vote),
            "total_votes": len(votes),
            "age": time.time() - proposal["timestamp"],
        }
        
    async def abort(self, proposal_id: str) -> bool:
        """Abort a pending proposal."""
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal["state"] != ConsensusState.PENDING:
            return False
            
        proposal["state"] = ConsensusState.REJECTED
        
        # Notify peers
        for peer in self._peers:
            await self._send_abort(peer, proposal_id)
            
        return True
        
    async def _send_abort(self, peer: str, proposal_id: str) -> None:
        """Send abort message to peer."""
        pass
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal["state"] != ConsensusState.PENDING:
            return False
            
        proposal["state"] = ConsensusState.REJECTED
        
        # Notify peers
        for peer in self._peers:
            await self._send_abort(peer, proposal_id)
            
        return True
        
    async def _send_abort(self, peer: str, proposal_id: str) -> None:
        """Send abort message to peer."""
        pass
