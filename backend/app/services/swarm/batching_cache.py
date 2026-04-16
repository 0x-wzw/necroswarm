"""
"""Adaptive Batching & Intelligent Caching for NECROSWARM

Maximizes throughput while minimizing costs through:
- Request batching with dynamic sizing
- Semantic caching with vector similarity
- Predictive pre-fetching
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar
from collections import deque
import numpy as np

# For semantic caching
from collections import OrderedDict

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class BatchConfig:
    """Configuration for adaptive batching."""
    max_batch_size: int = 32
    max_wait_ms: int = 50  # Maximum time to wait for batch to fill
    min_batch_size: int = 4  # Minimum size before processing
    adaptive_window: int = 10  # Number of batches to consider for adaptation
    
    # Dynamic sizing thresholds
    latency_threshold_ms: int = 200
    throughput_target: int = 100  # requests/sec


@dataclass 
class CachedResult:
    """Cached result with metadata."""
    result: Any
    timestamp: float
    access_count: int = 1
    last_access: float = field(default_factory=time.time)
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_access = time.time()


class SemanticCache:
    """
    Semantic cache using embedding similarity.
    
    Instead of exact string matching, caches based on semantic similarity.
    This captures: "summarize this text" ≈ "give me a summary of this"
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.92,
        max_size: int = 10000,
        ttl_seconds: int = 3600
    ):
        self.similarity_threshold = similarity_threshold
        self.max_size = max_size
        self.ttl = ttl_seconds
        
        # Use OrderedDict for LRU eviction
        self.cache: OrderedDict[str, CachedResult] = OrderedDict()
        
        # Embedding index (simplified - in production use FAISS/Annoy)
        self.embeddings: Dict[str, List[float]] = {}
        
        # Stats
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text.
        In production: use OpenAI, local model, or pre-computed embeddings.
        For now: simple hash-based encoding as placeholder.
        """
        # Placeholder: use hash-derived vector
        # In production: import openai; return openai.Embedding.create()
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        # Convert to 16-dimensional float vector
        vec = [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
        # Normalize
        norm = sum(x*x for x in vec) ** 0.5
        return [x/norm for x in vec]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot = sum(x*y for x, y in zip(a, b))
        return dot  # Already normalized
    
    def get(self, query: str) -> Optional[Any]:
        """
        Get cached result if semantically similar entry exists.
        
        Returns result if similarity > threshold and not expired.
        """
        query_emb = self._get_embedding(query)
        
        best_match = None
        best_similarity = 0.0
        
        # Find most similar cached entry
        for key, cached_emb in self.embeddings.items():
            if key not in self.cache:
                continue
                
            # Check TTL
            entry = self.cache[key]
            if time.time() - entry.timestamp > self.ttl:
                continue
            
            similarity = self._cosine_similarity(query_emb, cached_emb)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = key
        
        if best_match and best_similarity >= self.similarity_threshold:
            self.hits += 1
            entry = self.cache[best_match]
            entry.touch()
            
            # Move to end (most recently used)
            self.cache.move_to_end(best_match)
            
            logger.debug(f"Semantic cache hit (sim={best_similarity:.3f}): {best_match[:16]}...")
            return entry.result
        
        self.misses += 1
        return None
    
    def set(self, query: str, result: Any) -> None:
        """Cache a result with its embedding."""
        # Evict if at capacity
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        key = hashlib.sha256(query.encode()).hexdigest()
        embedding = self._get_embedding(query)
        
        self.cache[key] = CachedResult(
            result=result,
            timestamp=time.time()
        )
        self.embeddings[key] = embedding
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return
        
        # Get oldest entry
        oldest_key = next(iter(self.cache))
        del self.cache[oldest_key]
        del self.embeddings[oldest_key]
        self.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(hit_rate, 3),
            "size": len(self.cache),
            "max_size": self.max_size,
        }
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        removed = 0
        keys_to_remove = []
        
        for key in list(self.cache.keys()):
            # In production: check if query contains pattern
            # Simplified: remove random sample for testing
            if hash(key) % 10 == 0:  # Pseudo-random
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            del self.embeddings[key]
            removed += 1
        
        return removed


class AdaptiveBatcher:
    """
    Adaptive batching system that optimizes batch size based on load.
    
    Under low load: smaller batches, lower latency
    Under high load: larger batches, higher throughput
    """
    
    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()
        
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
        self._current_batch: List[Tuple[Any, asyncio.Future]] = []
        self._batch_start_time: Optional[float] = None
        
        # Performance tracking
        self.latency_history: deque = deque(maxlen=self.config.adaptive_window)
        self.batch_size_history: deque = deque(maxlen=self.config.adaptive_window)
        self.throughput_history: deque = deque(maxlen=self.config.adaptive_window)
        
        # Adaptive parameters
        self.current_max_batch = self.config.max_batch_size
        
    async def submit(self, request: Any) -> Any:
        """
        Submit a request for batching.
        
        Returns the result when batch is processed.
        """
        future = asyncio.get_event_loop().create_future()
        await self._queue.put((request, future))
        
        # Trigger batch processing if needed
        if not self._processing:
            asyncio.create_task(self._process_batches())
        
        return await future
    
    async def _process_batches(self) -> None:
        """Main batch processing loop."""
        self._processing = True
        
        try:
            while True:
                batch = await self._collect_batch()
                if not batch:
                    break
                
                start_time = time.time()
                results = await self._process_batch(batch)
                latency_ms = (time.time() - start_time) * 1000
                
                # Track metrics
                self.latency_history.append(latency_ms)
                self.batch_size_history.append(len(batch))
                
                # Resolve futures
                for (_, future), result in zip(batch, results):
                    if not future.done():
                        future.set_result(result)
                
                # Adapt batch size
                self._adapt_batch_size()
                
        finally:
            self._processing = False
    
    async def _collect_batch(self) -> List[Tuple[Any, asyncio.Future]]:
        """Collect a batch of requests."""
        batch = []
        deadline = time.time() + (self.config.max_wait_ms / 1000)
        
        while len(batch) < self.current_max_batch:
            timeout = deadline - time.time()
            
            if timeout <= 0:
                break
            
            try:
                request, future = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=max(0, timeout)
                )
                batch.append((request, future))
            except asyncio.TimeoutError:
                break
        
        # Wait for minimum batch size under low load
        if len(batch) < self.config.min_batch_size:
            remaining = self.config.min_batch_size - len(batch)
            extra_timeout = 0.01  # 10ms additional wait
            
            for _ in range(remaining):
                try:
                    request, future = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=extra_timeout
                    )
                    batch.append((request, future))
                except asyncio.TimeoutError:
                    break
        
        return batch
    
    async def _process_batch(
        self,
        batch: List[Tuple[Any, asyncio.Future]]
    ) -> List[Any]:
        """
        Process a batch of requests.
        
        Override this method for specific batch processing logic.
        """
        # Default: process individually
        results = []
        for request, _ in batch:
            result = await self._process_single(request)
            results.append(result)
        return results
    
    async def _process_single(self, request: Any) -> Any:
        """Process a single request. Override in subclass."""
        return request  # Identity by default
    
    def _adapt_batch_size(self) -> None:
        """Adapt batch size based on performance history."""
        if len(self.latency_history) < self.config.adaptive_window:
            return
        
        avg_latency = sum(self.latency_history) / len(self.latency_history)
        avg_batch = sum(self.batch_size_history) / len(self.batch_size_history)
        
        # If latency is high and batches are large, decrease size
        if avg_latency > self.config.latency_threshold_ms and avg_batch > 8:
            self.current_max_batch = max(4, int(self.current_max_batch * 0.8))
            logger.debug(f"Decreased batch size to {self.current_max_batch} "
                        f"(avg latency: {avg_latency:.1f}ms)")
        
        # If latency is low and queue is building, increase size
        elif avg_latency < self.config.latency_threshold_ms * 0.5:
            self.current_max_batch = min(
                self.config.max_batch_size,
                int(self.current_max_batch * 1.2)
            )
            logger.debug(f"Increased batch size to {self.current_max_batch}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics."""
        if not self.latency_history:
            return {"status": "idle"}
        
        return {
            "current_max_batch": self.current_max_batch,
            "avg_latency_ms": round(sum(self.latency_history) / len(self.latency_history), 2),
            "avg_batch_size": round(sum(self.batch_size_history) / len(self.batch_size_history), 2),
            "queue_size": self._queue.qsize(),
        }


class PredictivePrefetcher:
    """
    Predictive prefetching based on common task patterns.
    
    Identifies sequences that commonly occur together and pre-computes.
    """
    
    def __init__(self, lookahead: int = 3):
        self.lookahead = lookahead
        
        # Markov chain for task prediction
        self.transitions: Dict[str, Dict[str, int]] = {}
        self.task_counts: Dict[str, int] = {}
        
        # Prefetch cache
        self.prefetched: Dict[str, Any] = {}
        
    def observe_sequence(self, tasks: List[str]) -> None:
        """Learn from observed task sequences."""
        for i in range(len(tasks) - 1):
            current = tasks[i]
            next_task = tasks[i + 1]
            
            if current not in self.transitions:
                self.transitions[current] = {}
            
            self.transitions[current][next_task] = \
                self.transitions[current].get(next_task, 0) + 1
            
            self.task_counts[current] = self.task_counts.get(current, 0) + 1
    
    def predict_next(self, current_task: str) -> List[str]:
        """Predict likely next tasks."""
        if current_task not in self.transitions:
            return []
        
        # Get top predictions by transition probability
        transitions = self.transitions[current_task]
        total = sum(transitions.values())
        
        probs = [(task, count/total) for task, count in transitions.items()]
        probs.sort(key=lambda x: x[1], reverse=True)
        
        # Return tasks above threshold
        return [task for task, prob in probs[:self.lookahead] if prob > 0.2]
    
    def should_prefetch(self, current_task: str) -> List[str]:
        """Get tasks to prefetch based on current task."""
        predictions = self.predict_next(current_task)
        
        # Filter out already prefetched
        return [p for p in predictions if p not in self.prefetched]
    
    def store_prefetch(self, task: str, result: Any) -> None:
        """Store a prefetched result."""
        self.prefetched[task] = result
    
    def get_prefetch(self, task: str) -> Optional[Any]:
        """Get prefetched result if available."""
        return self.prefetched.pop(task, None)  # Remove after retrieval
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prefetch statistics."""
        return {
            "learned_transitions": len(self.transitions),
            "total_observations": sum(self.task_counts.values()),
            "prefetch_buffer_size": len(self.prefetched),
        }


# Export
__all__ = [
    "SemanticCache",
    "AdaptiveBatcher",
    "PredictivePrefetcher",
    "BatchConfig",
    "CachedResult",
]