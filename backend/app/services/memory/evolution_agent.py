"""
Memory Evolution Agent - Self-improving memory system
Core module with access tracking, decay scoring, and relationship inference
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading


@dataclass
class MemoryEntry:
    """Represents a single memory entry with metadata"""
    id: str
    content: str
    timestamp: float
    access_count: int = 0
    last_accessed: float = 0
    importance_score: float = 1.0
    tags: List[str] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)
    version: int = 1
    rewritten_from: Optional[str] = None
    
    def __post_init__(self):
        if self.last_accessed == 0:
            self.last_accessed = self.timestamp


class AccessPatternTracker:
    """Tracks memory access patterns (reads/writes) to understand usage"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.access_log: List[Dict] = []
        self.memory_access_counts: Dict[str, int] = defaultdict(int)
        self.access_sequences: List[List[str]] = []
        self._lock = threading.Lock()
    
    def record_access(self, memory_id: str, operation: str = "read", context: Optional[str] = None):
        """Record a memory access event"""
        entry = {
            "memory_id": memory_id,
            "operation": operation,
            "timestamp": time.time(),
            "context": context
        }
        
        with self._lock:
            self.access_log.append(entry)
            self.memory_access_counts[memory_id] += 1
            
            # Keep log size manageable
            if len(self.access_log) > self.window_size:
                removed = self.access_log.pop(0)
                self.memory_access_counts[removed["memory_id"]] -= 1
    
    def record_sequence(self, memory_ids: List[str]):
        """Record a sequence of related memory accesses"""
        if len(memory_ids) > 1:
            with self._lock:
                self.access_sequences.append(memory_ids)
                if len(self.access_sequences) > self.window_size:
                    self.access_sequences.pop(0)
    
    def get_frequently_accessed(self, threshold: int = 5) -> List[Tuple[str, int]]:
        """Get memories accessed more than threshold times"""
        return [(mid, count) for mid, count in self.memory_access_counts.items() if count >= threshold]
    
    def get_access_patterns(self, memory_id: str) -> Dict:
        """Get access patterns for a specific memory"""
        accesses = [e for e in self.access_log if e["memory_id"] == memory_id]
        
        if not accesses:
            return {"total_accesses": 0, "operations": {}, "contexts": []}
        
        operations = defaultdict(int)
        contexts = []
        
        for access in accesses:
            operations[access["operation"]] += 1
            if access["context"]:
                contexts.append(access["context"])
        
        return {
            "total_accesses": len(accesses),
            "operations": dict(operations),
            "contexts": list(set(contexts))[:10]  # Unique contexts, limited
        }
    
    def get_coaccess_patterns(self) -> Dict[Tuple[str, str], int]:
        """Find memories frequently accessed together"""
        coaccess = defaultdict(int)
        
        for sequence in self.access_sequences:
            for i, mem1 in enumerate(sequence):
                for mem2 in sequence[i+1:]:
                    key = tuple(sorted([mem1, mem2]))
                    coaccess[key] += 1
        
        return dict(coaccess)
    
    def export_stats(self) -> Dict:
        """Export tracking statistics"""
        return {
            "total_tracked_accesses": len(self.access_log),
            "unique_memories_tracked": len(self.memory_access_counts),
            "sequences_tracked": len(self.access_sequences),
            "top_accessed": sorted(
                self.memory_access_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }


class ImportanceDecay:
    """Manages time-based relevance scoring for memories"""
    
    def __init__(
        self,
        half_life_days: float = 30.0,
        access_boost: float = 0.1,
        max_score: float = 2.0,
        min_score: float = 0.1
    ):
        self.half_life = half_life_days * 24 * 3600  # Convert to seconds
        self.access_boost = access_boost
        self.max_score = max_score
        self.min_score = min_score
    
    def calculate_score(self, memory: MemoryEntry, current_time: Optional[float] = None) -> float:
        """Calculate current importance score for a memory"""
        if current_time is None:
            current_time = time.time()
        
        # Time decay factor
        age = current_time - memory.timestamp
        decay_factor = 0.5 ** (age / self.half_life)
        
        # Access boost based on recency and frequency
        recency_boost = self._recency_boost(memory, current_time)
        frequency_boost = min(memory.access_count * self.access_boost, 1.0)
        
        # Base importance with decay and boosts
        score = memory.importance_score * decay_factor * (1 + recency_boost + frequency_boost)
        
        # Clamp to valid range
        return max(self.min_score, min(self.max_score, score))
    
    def _recency_boost(self, memory: MemoryEntry, current_time: float) -> float:
        """Calculate boost from recent access"""
        time_since_access = current_time - memory.last_accessed
        
        # Recent access within last day gives boost
        if time_since_access < 86400:  # 24 hours
            return 0.5 * (1 - time_since_access / 86400)
        return 0.0
    
    def should_archive(self, memory: MemoryEntry, threshold: float = 0.2) -> bool:
        """Determine if memory should be archived due to low relevance"""
        current_score = self.calculate_score(memory)
        return current_score < threshold
    
    def decay_batch(self, memories: List[MemoryEntry]) -> List[Tuple[MemoryEntry, float]]:
        """Calculate scores for a batch of memories"""
        current_time = time.time()
        return [(mem, self.calculate_score(mem, current_time)) for mem in memories]


class RelationshipInference:
    """Infers relationships between memories based on content and access patterns"""
    
    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold
        self._content_index: Dict[str, Set[str]] = defaultdict(set)  # word -> memory_ids
    
    def update_index(self, memory: MemoryEntry):
        """Update the content index for a memory"""
        words = self._extract_keywords(memory.content)
        for word in words:
            self._content_index[word].add(memory.id)
    
    def _extract_keywords(self, content: str) -> Set[str]:
        """Extract keywords from content (simple implementation)"""
        # Simple keyword extraction - can be enhanced with NLP
        words = content.lower().split()
        # Filter common words (stop words)
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "shall", "can", "need", "dare", "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by", "from", "as", "into", "through", "during", "before", "after", "above", "below", "between", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just", "and", "but", "if", "or", "because", "until", "while"}
        return set(w.strip(".,!?;:'\"") for w in words if len(w) > 2 and w not in stop_words)
    
    def find_related(self, memory: MemoryEntry, all_memories: Dict[str, MemoryEntry]) -> List[Tuple[str, float]]:
        """Find memories related to the given one"""
        candidates = self._get_candidate_relations(memory)
        
        relations = []
        for candidate_id in candidates:
            if candidate_id == memory.id:
                continue
            
            if candidate_id in all_memories:
                score = self._calculate_similarity(memory, all_memories[candidate_id])
                if score >= self.similarity_threshold:
                    relations.append((candidate_id, score))
        
        # Sort by similarity score
        relations.sort(key=lambda x: x[1], reverse=True)
        return relations[:10]  # Top 10 relations
    
    def _get_candidate_relations(self, memory: MemoryEntry) -> Set[str]:
        """Get candidate memories that might be related"""
        candidates = set()
        words = self._extract_keywords(memory.content)
        
        for word in words:
            candidates.update(self._content_index.get(word, set()))
        
        return candidates
    
    def _calculate_similarity(self, mem1: MemoryEntry, mem2: MemoryEntry) -> float:
        """Calculate similarity between two memories"""
        # Content similarity using Jaccard
        words1 = self._extract_keywords(mem1.content)
        words2 = self._extract_keywords(mem2.content)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        content_sim = intersection / union if union > 0 else 0.0
        
        # Tag overlap
        tag_overlap = len(set(mem1.tags) & set(mem2.tags))
        tag_sim = tag_overlap / max(len(mem1.tags), len(mem2.tags), 1)
        
        # Time proximity (memories created close in time may be related)
        time_diff = abs(mem1.timestamp - mem2.timestamp)
        time_sim = max(0, 1 - (time_diff / (7 * 24 * 3600)))  # Decay over a week
        
        # Weighted combination
        score = 0.5 * content_sim + 0.3 * tag_sim + 0.2 * time_sim
        return score
    
    def infer_relationships_batch(
        self, 
        memories: Dict[str, MemoryEntry]
    ) -> Dict[str, List[Tuple[str, float]]]:
        """Infer relationships for all memories in batch"""
        results = {}
        
        for mem_id, memory in memories.items():
            results[mem_id] = self.find_related(memory, memories)
        
        return results


class MemoryRewriter:
    """Updates memory entries based on access patterns and new information"""
    
    def __init__(
        self,
        min_access_for_rewrite: int = 5,
        consolidation_threshold: int = 3
    ):
        self.min_access_for_rewrite = min_access_for_rewrite
        self.consolidation_threshold = consolidation_threshold
        self.rewrite_history: List[Dict] = []
    
    def should_rewrite(self, memory: MemoryEntry, access_tracker: AccessPatternTracker) -> bool:
        """Determine if a memory should be rewritten based on access patterns"""
        patterns = access_tracker.get_access_patterns(memory.id)
        
        # Rewrite if accessed frequently with different contexts
        return (
            patterns["total_accesses"] >= self.min_access_for_rewrite and
            len(patterns.get("contexts", [])) >= 2
        )
    
    def suggest_rewrite(self, memory: MemoryEntry, related_memories: List[MemoryEntry]) -> Dict:
        """Suggest how to rewrite a memory based on related information"""
        # Collect common themes from related memories
        all_tags = set(memory.tags)
        for related in related_memories:
            all_tags.update(related.tags)
        
        # Suggest consolidation if there are similar memories
        if len(related_memories) >= self.consolidation_threshold:
            return {
                "action": "consolidate",
                "original_id": memory.id,
                "related_ids": [r.id for r in related_memories],
                "suggested_tags": list(all_tags),
                "reason": f"High co-occurrence with {len(related_memories)} related memories"
            }
        
        # Suggest tag enrichment
        new_tags = all_tags - set(memory.tags)
        if new_tags:
            return {
                "action": "enrich_tags",
                "original_id": memory.id,
                "suggested_tags": list(all_tags),
                "new_tags": list(new_tags),
                "reason": f"Inferred from {len(related_memories)} related memories"
            }
        
        return {"action": "none", "original_id": memory.id}
    
    def apply_rewrite(self, memory: MemoryEntry, rewrite_plan: Dict) -> Optional[MemoryEntry]:
        """Apply a rewrite plan to a memory"""
        if rewrite_plan["action"] == "none":
            return None
        
        # Create new version
        new_memory = MemoryEntry(
            id=memory.id,
            content=memory.content,  # Content preserved, could be enhanced
            timestamp=memory.timestamp,
            access_count=memory.access_count,
            last_accessed=memory.last_accessed,
            importance_score=memory.importance_score * 1.1,  # Slight boost for being rewritten
            tags=rewrite_plan.get("suggested_tags", memory.tags),
            related_memories=memory.related_memories + rewrite_plan.get("related_ids", []),
            version=memory.version + 1,
            rewritten_from=memory.id if memory.rewritten_from is None else memory.rewritten_from
        )
        
        # Log the rewrite
        self.rewrite_history.append({
            "timestamp": time.time(),
            "original_id": memory.id,
            "new_version": new_memory.version,
            "action": rewrite_plan["action"],
            "reason": rewrite_plan.get("reason", "")
        })
        
        return new_memory
    
    def get_rewrite_stats(self) -> Dict:
        """Get statistics about rewrites performed"""
        return {
            "total_rewrites": len(self.rewrite_history),
            "consolidations": len([r for r in self.rewrite_history if r["action"] == "consolidate"]),
            "tag_enrichments": len([r for r in self.rewrite_history if r["action"] == "enrich_tags"]),
            "recent_rewrites": self.rewrite_history[-10:]
        }


class EvolutionAgent:
    """Main orchestrator for memory evolution"""
    
    def __init__(
        self,
        storage_path: str = "memory_store.json",
        half_life_days: float = 30.0,
        similarity_threshold: float = 0.6
    ):
        self.storage_path = storage_path
        self.memories: Dict[str, MemoryEntry] = {}
        
        # Initialize components
        self.access_tracker = AccessPatternTracker()
        self.decay = ImportanceDecay(half_life_days=half_life_days)
        self.relationships = RelationshipInference(similarity_threshold=similarity_threshold)
        self.rewriter = MemoryRewriter()
        
        self._lock = threading.Lock()
        self._load()
    
    def add_memory(self, content: str, tags: Optional[List[str]] = None) -> str:
        """Add a new memory entry"""
        mem_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
        
        memory = MemoryEntry(
            id=mem_id,
            content=content,
            timestamp=time.time(),
            tags=tags or []
        )
        
        with self._lock:
            self.memories[mem_id] = memory
            self.relationships.update_index(memory)
        
        self._save()
        return mem_id
    
    def get_memory(self, memory_id: str, context: Optional[str] = None) -> Optional[MemoryEntry]:
        """Retrieve a memory and track access"""
        with self._lock:
            memory = self.memories.get(memory_id)
        
        if memory:
            self.access_tracker.record_access(memory_id, "read", context)
            memory.access_count += 1
            memory.last_accessed = time.time()
            self._save()
        
        return memory
    
    def query_memories(self, query: str, limit: int = 10) -> List[Tuple[MemoryEntry, float]]:
        """Query memories by relevance to query string"""
        query_words = set(query.lower().split())
        
        results = []
        with self._lock:
            for memory in self.memories.values():
                score = self._calculate_query_score(memory, query_words)
                if score > 0:
                    results.append((memory, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _calculate_query_score(self, memory: MemoryEntry, query_words: Set[str]) -> float:
        """Calculate relevance score for a query"""
        content_words = set(memory.content.lower().split())
        
        # Word overlap
        overlap = len(query_words & content_words)
        if not overlap:
            return 0.0
        
        # TF-IDF-like scoring
        score = overlap / len(query_words)
        
        # Boost by importance and recency
        importance = self.decay.calculate_score(memory)
        score *= importance
        
        return score
    
    def run_evolution_cycle(self) -> Dict:
        """Run one evolution cycle: decay, infer relationships, suggest rewrites"""
        results = {
            "memories_processed": 0,
            "archived": [],
            "relationships_inferred": 0,
            "rewrites_suggested": 0,
            "rewrites_applied": 0
        }
        
        with self._lock:
            memories_list = list(self.memories.values())
        
        # Step 1: Calculate decay scores
        scored_memories = self.decay.decay_batch(memories_list)
        
        # Step 2: Check for archiving
        for memory, score in scored_memories:
            memory.importance_score = score
            if self.decay.should_archive(memory):
                results["archived"].append(memory.id)
        
        results["memories_processed"] = len(memories_list)
        
        # Step 3: Infer relationships
        with self._lock:
            relations = self.relationships.infer_relationships_batch(self.memories)
        
        for mem_id, related in relations.items():
            if related:
                with self._lock:
                    if mem_id in self.memories:
                        self.memories[mem_id].related_memories = [r[0] for r in related]
                results["relationships_inferred"] += len(related)
        
        # Step 4: Suggest and apply rewrites
        for memory in memories_list:
            if self.rewriter.should_rewrite(memory, self.access_tracker):
                with self._lock:
                    related = [
                        self.memories.get(rid) 
                        for rid in memory.related_memories 
                        if rid in self.memories
                    ]
                
                rewrite_plan = self.rewriter.suggest_rewrite(memory, related)
                results["rewrites_suggested"] += 1
                
                if rewrite_plan["action"] != "none":
                    new_memory = self.rewriter.apply_rewrite(memory, rewrite_plan)
                    if new_memory:
                        with self._lock:
                            self.memories[memory.id] = new_memory
                        results["rewrites_applied"] += 1
        
        self._save()
        return results
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics"""
        return {
            "memory_count": len(self.memories),
            "access_tracking": self.access_tracker.export_stats(),
            "decay_stats": {
                "avg_importance": sum(m.importance_score for m in self.memories.values()) / max(len(self.memories), 1)
            },
            "rewrite_stats": self.rewriter.get_rewrite_stats()
        }
    
    def _save(self):
        """Persist memories to storage"""
        data = {
            mem_id: asdict(mem) 
            for mem_id, mem in self.memories.items()
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Load memories from storage"""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for mem_id, mem_data in data.items():
                self.memories[mem_id] = MemoryEntry(**mem_data)
                self.relationships.update_index(self.memories[mem_id])
        
        except (json.JSONDecodeError, IOError):
            pass  # Start fresh if load fails


if __name__ == "__main__":
    # Demo usage
    agent = EvolutionAgent(storage_path="demo_memory.json")
    
    # Add some memories
    mem1 = agent.add_memory("Python is a great programming language for AI", ["python", "ai"])
    mem2 = agent.add_memory("Machine learning requires good data", ["ml", "data"])
    mem3 = agent.add_memory("Python libraries like PyTorch are useful for ML", ["python", "ml"])
    
    # Access memories
    agent.get_memory(mem1, context="checking programming languages")
    agent.get_memory(mem1, context="AI research")
    agent.get_memory(mem3, context="deep learning")
    
    # Run evolution
    results = agent.run_evolution_cycle()
    print(f"Evolution results: {json.dumps(results, indent=2)}")
    
    # Query
    print("\nQuery results for 'python':")
    for mem, score in agent.query_memories("python"):
        print(f"  {mem.content[:50]}... (score: {score:.2f})")
