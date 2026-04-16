"""
Swarm Memory - Cross-simulation persistent knowledge base.

Provides persistent storage for swarm consensus, simulation statements, and agent knowledge.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ConsensusRecord:
    """A consensus record stored in swarm memory."""
    swarm_id: str
    consensus_value: str
    votes: List[Dict[str, Any]]
    timestamp: datetime
    outcome: str = "success"


@dataclass
class SimulationStatement:
    """A statement about a simulation stored in swarm memory."""
    simulation_id: str
    swarm_id: str
    statement: str
    likelihood: float
    confidence: float
    timestamp: datetime
    author_id: Optional[str] = None


@dataclass
class AgentKnowledge:
    """Knowledge entry for an agent."""
    agent_id: str
    keyspace: str  # Knowledge domain (e.g., "simulation_stored", "consensus")
    key: str
    value: Any
    last_updated: datetime
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class SwarmMemory:
    """
    Persistent knowledge base for swarm operations.
    
    Features:
    - Persistent storage via JSON file
    - Time-series data for consensus and statements
    - Agent-specific knowledge isolation
    - Query capabilities
    """
    
    def __init__(
        self, 
        storage_path: str = "swarm_memory.json",
        max_records: int = 10000,
        enable_persistence: bool = True
    ):
        self.storage_path = storage_path
        self.max_records = max_records
        self.enable_persistence = enable_persistence
        
        # In-memory storage
        self._consensus_records: List[ConsensusRecord] = []
        self._simulation_statements: List[SimulationStatement] = []
        self._agent_knowledge: Dict[str, AgentKnowledge] = {}
        self._swarm_states: Dict[str, Dict[str, Any]] = {}
        
        # Knowledge version tracking
        self._knowledge_versions: Dict[str, int] = {}
        
        # Lock for thread-safe access
        self._lock = asyncio.Lock()
        
        # Load existing data
        if enable_persistence:
            self._load()
    
    def _load(self) -> None:
        """Load swarm memory from storage."""
        if not os.path.exists(self.storage_path):
            logger.info(f"Creating new swarm memory: {self.storage_path}")
            self._initialize()
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self._consensus_records = [
                ConsensusRecord(**r) 
                for r in data.get("consensus_records", [])
            ]
            self._simulation_statements = [
                SimulationStatement(**s)
                for s in data.get("simulation_statements", [])
            ]
            
            self._agent_knowledge = {}
            for key, value in data.get("agent_knowledge", {}).items():
                self._agent_knowledge[key] = AgentKnowledge(**value)
            
            self._swarm_states = data.get("swarm_states", {})
            self._knowledge_versions = data.get("knowledge_versions", {})
            
            logger.info(f"Loaded swarm memory from {self.storage_path}")
            logger.info(f"Records: {len(self._consensus_records)} consensus, "
                       f"{len(self._simulation_statements)} statements, "
                       f"{len(self._agent_knowledge)} knowledge entries")
            
        except Exception as e:
            logger.error(f"Error loading swarm memory: {e}")
            self._initialize()
    
    def _initialize(self) -> None:
        """Initialize new swarm memory."""
        self._consensus_records = []
        self._simulation_statements = []
        self._agent_knowledge = {}
        self._swarm_states = {}
        self._knowledge_versions = {}
        
        self._save()
        logger.info("Initialized new swarm memory")
    
    def _save(self) -> None:
        """Save swarm memory to storage."""
        if not self.enable_persistence:
            return
        
        try:
            data = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "consensus_records": [
                    {
                        "swarm_id": r.swarm_id,
                        "consensus_value": r.consensus_value,
                        "votes": r.votes,
                        "timestamp": r.timestamp.isoformat(),
                        "outcome": r.outcome
                    }
                    for r in self._consensus_records
                ],
                "simulation_statements": [
                    {
                        "simulation_id": s.simulation_id,
                        "swarm_id": s.swarm_id,
                        "statement": s.statement,
                        "likelihood": s.likelihood,
                        "confidence": s.confidence,
                        "timestamp": s.timestamp.isoformat(),
                        "author_id": s.author_id
                    }
                    for s in self._simulation_statements
                ],
                "agent_knowledge": {
                    key: {
                        "agent_id": k.agent_id,
                        "keyspace": k.keyspace,
                        "key": k.key,
                        "value": k.value,
                        "last_updated": k.last_updated.isoformat(),
                        "version": k.version,
                        "metadata": k.metadata
                    }
                    for key, k in self._agent_knowledge.items()
                },
                "swarm_states": self._swarm_states,
                "knowledge_versions": self._knowledge_versions,
                "updated_at": datetime.now().isoformat()
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved swarm memory to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Error saving swarm memory: {e}")
    
    async def store_consensus(
        self,
        swarm_id: str,
        consensus_value: str,
        votes: List[Dict[str, Any]]
    ) -> None:
        """Store a consensus record."""
        record = ConsensusRecord(
            swarm_id=swarm_id,
            consensus_value=consensus_value,
            votes=votes,
            timestamp=datetime.now(),
            outcome="success"
        )
        
        async with self._lock:
            self._consensus_records.append(record)
            
            # Truncate if exceeds max
            if len(self._consensus_records) > self.max_records:
                self._consensus_records = self._consensus_records[-self.max_records:]
            
            self._save()
        
        logger.info(f"Stored consensus for swarm {swarm_id}: {consensus_value}")
    
    def get_consensus_records(
        self,
        swarm_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ConsensusRecord]:
        """Get consensus records, optionally filtered by swarm."""
        records = self._consensus_records
        
        if swarm_id:
            records = [r for r in records if r.swarm_id == swarm_id]
        
        # Sort by timestamp descending
        records.sort(key=lambda r: r.timestamp, reverse=True)
        
        return records[:limit]
    
    async def store_simulation_statement(
        self,
        simulation_id: str,
        swarm_id: str,
        statement: str,
        likelihood: float = 0.5,
        confidence: float = 0.5,
        author_id: Optional[str] = None
    ) -> None:
        """Store a simulation statement."""
        stmt = SimulationStatement(
            simulation_id=simulation_id,
            swarm_id=swarm_id,
            statement=statement,
            likelihood=likelihood,
            confidence=confidence,
            timestamp=datetime.now(),
            author_id=author_id
        )
        
        async with self._lock:
            self._simulation_statements.append(stmt)
            
            if len(self._simulation_statements) > self.max_records:
                self._simulation_statements = self._simulation_statements[-self.max_records:]
            
            self._save()
        
        logger.debug(f"Stored simulation statement for {simulation_id}")
    
    def get_simulation_statements(
        self,
        simulation_id: Optional[str] = None,
        swarm_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SimulationStatement]:
        """Get simulation statements, optionally filtered."""
        statements = self._simulation_statements
        
        if simulation_id:
            statements = [s for s in statements if s.simulation_id == simulation_id]
        if swarm_id:
            statements = [s for s in statements if s.swarm_id == swarm_id]
        
        statements.sort(key=lambda s: s.timestamp, reverse=True)
        
        return statements[:limit]
    
    def get_similar_statements(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[SimulationStatement]:
        """
        Find similar simulation statements using simple substring matching.
        
        In a production system, this would use semantic search.
        """
        from difflib import SequenceMatcher
        
        statements = self._simulation_statements
        results = []
        
        for stmt in statements:
            similarity = SequenceMatcher(
                None, 
                query.lower(), 
                stmt.statement.lower()
            ).ratio()
            
            if similarity >= similarity_threshold:
                results.append((stmt, similarity))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [s for s, _ in results[:limit]]
    
    async def store_agent_knowledge(
        self,
        agent_id: str,
        keyspace: str,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store knowledge for an agent."""
        agent_key = f"{agent_id}:{keyspace}:{key}"
        
        # Increment version if exists
        new_version = self._knowledge_versions.get(agent_key, 0) + 1
        
        entry = AgentKnowledge(
            agent_id=agent_id,
            keyspace=keyspace,
            key=key,
            value=value,
            last_updated=datetime.now(),
            version=new_version,
            metadata=metadata or {}
        )
        
        async with self._lock:
            self._agent_knowledge[agent_key] = entry
            self._knowledge_versions[agent_key] = new_version
            
            self._save()
        
        return new_version
    
    def get_agent_knowledge(
        self,
        agent_id: str,
        keyspace: Optional[str] = None,
        key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get knowledge for an agent."""
        results = {}
        
        prefix = f"{agent_id}:"
        
        for agent_key, entry in self._agent_knowledge.items():
            if agent_key.startswith(prefix):
                if keyspace and entry.keyspace != keyspace:
                    continue
                if key and entry.key != key:
                    continue
                
                key_name = f"{entry.keyspace}:{entry.key}"
                results[key_name] = {
                    "value": entry.value,
                    "version": entry.version,
                    "last_updated": entry.last_updated.isoformat(),
                    "metadata": entry.metadata
                }
        
        return results
    
    def get_knowledge_by_keyspace(
        self,
        agent_id: Optional[str] = None,
        keyspace: str = "simulation_stored"
    ) -> Dict[str, Any]:
        """Get all knowledge in a specific keyspace."""
        results = {}
        
        prefix = f"{agent_id}:" if agent_id else ""
        
        for agent_key, entry in self._agent_knowledge.items():
            if agent_key.startswith(prefix) and entry.keyspace == keyspace:
                key_name = f"{entry.keyspace}:{entry.key}"
                results[key_name] = {
                    "value": entry.value,
                    "version": entry.version,
                    "last_updated": entry.last_updated.isoformat(),
                    "metadata": entry.metadata
                }
        
        return results
    
    async def update_agent_knowledge(
        self,
        agent_id: str,
        keyspace: str,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Update existing agent knowledge."""
        agent_key = f"{agent_id}:{keyspace}:{key}"
        
        if agent_key not in self._agent_knowledge:
            raise KeyError(f"Knowledge not found: {agent_key}")
        
        current = self._agent_knowledge[agent_key]
        new_version = current.version + 1
        
        entry = AgentKnowledge(
            agent_id=agent_id,
            keyspace=keyspace,
            key=key,
            value=value,
            last_updated=datetime.now(),
            version=new_version,
            metadata={**current.metadata, **(metadata or {})}
        )
        
        async with self._lock:
            self._agent_knowledge[agent_key] = entry
            self._knowledge_versions[agent_key] = new_version
            
            self._save()
        
        return new_version
    
    def delete_agent_knowledge(
        self,
        agent_id: str,
        keyspace: Optional[str] = None,
        key: Optional[str] = None
    ) -> bool:
        """Delete agent knowledge."""
        prefix = f"{agent_id}:"
        
        keys_to_delete = []
        for agent_key in self._agent_knowledge.keys():
            if agent_key.startswith(prefix):
                entry = self._agent_knowledge[agent_key]
                if keyspace and entry.keyspace != keyspace:
                    continue
                if key and entry.key != key:
                    continue
                keys_to_delete.append(agent_key)
        
        if not keys_to_delete:
            return False
        
        async with self._lock:
            for agent_key in keys_to_delete:
                del self._agent_knowledge[agent_key]
                del self._knowledge_versions[agent_key]
            
            self._save()
        
        logger.info(f"Deleted {len(keys_to_delete)} knowledge entries for agent {agent_id}")
        return True
    
    async def store_swarm_state(
        self,
        swarm_id: str,
        state: Dict[str, Any]
    ) -> None:
        """Store swarm state."""
        async with self._lock:
            self._swarm_states[swarm_id] = {
                **state,
                "last_updated": datetime.now().isoformat()
            }
            
            self._save()
    
    def get_swarm_state(self, swarm_id: str) -> Optional[Dict[str, Any]]:
        """Get swarm state."""
        return self._swarm_states.get(swarm_id)
    
    def get_all_swarm_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all swarm states."""
        return self._swarm_states.copy()
    
    def clear(self) -> None:
        """Clear all data from swarm memory."""
        async with self._lock:
            self._consensus_records = []
            self._simulation_statements = []
            self._agent_knowledge = {}
            self._swarm_states = {}
            self._knowledge_versions = {}
            
            self._save()
        
        logger.info("Cleared swarm memory")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get swarm memory statistics."""
        return {
            "total_consensus_records": len(self._consensus_records),
            "total_simulation_statements": len(self._simulation_statements),
            "total_agent_knowledge_entries": len(self._agent_knowledge),
            "total_swarm_states": len(self._swarm_states),
            "max_records": self.max_records,
            "enable_persistence": self.enable_persistence,
            "storage_path": self.storage_path,
            "knowledge_versions_count": len(self._knowledge_versions)
        }
    
    def get_consensus_summary(
        self,
        swarm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of consensus records."""
        records = self.get_consensus_records(swarm_id=swarm_id)
        
        # Count consensus values
        consensus_counts: Dict[str, int] = {}
        total_votes = 0
        
        for record in records:
            consensus_counts[record.consensus_value] = (
                consensus_counts.get(record.consensus_value, 0) + 1
            )
            total_votes += len(record.votes)
        
        return {
            "total_records": len(records),
            "total_votes": total_votes,
            "consensus_distribution": consensus_counts,
            "most_common": (
                max(consensus_counts.items(), key=lambda x: x[1]) 
                if consensus_counts else None
            )
        }
    
    def get_statement_summary(
        self,
        swarm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of simulation statements."""
        statements = self.get_simulation_statements(swarm_id=swarm_id)
        
        # Count by likelihood and confidence
        likelihood_counts: Dict[str, int] = {}
        confidence_summary = {
            "total": len(statements),
            "avg_confidence": 0.0,
            "high_confidence_count": 0,
            "low_confidence_count": 0
        }
        
        total_confidence = 0
        for stmt in statements:
            likelihood_counts[stmt.likelihood] = (
                likelihood_counts.get(stmt.likelihood, 0) + 1
            )
            total_confidence += stmt.confidence
            
            confidence_summary["high_confidence_count"] += 1 if stmt.confidence > 0.7 else 0
            confidence_summary["low_confidence_count"] += 1 if stmt.confidence < 0.3 else 0
        
        confidence_summary["avg_confidence"] = (
            total_confidence / len(statements) if statements else 0.0
        )
        
        return {
            "total_statements": len(statements),
            "likelihood_distribution": likelihood_counts,
            "confidence_summary": confidence_summary
        }
