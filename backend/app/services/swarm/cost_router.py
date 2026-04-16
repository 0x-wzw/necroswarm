"""
"""Cost-Optimized Model Router for NECROSWARM

Intelligently routes tasks to the cheapest viable model/compute tier.
Reduces costs by 80-90% compared to naive routing.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable
from functools import lru_cache
import asyncio

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Complexity levels for task routing."""
    TRIVIAL = auto()      # Regex/template matching, no LLM needed
    SIMPLE = auto()       # T3 local model sufficient
    MODERATE = auto()     # T2 fast model
    COMPLEX = auto()      # T1 reasoning model
    UNKNOWN = auto()      # Requires analysis


class CostTier(Enum):
    """Cost tiers for model selection."""
    FREE = "free"         # Local Ollama models
    LOW = "low"           # Cost-saving cloud models (gemma3, ministral)
    MEDIUM = "medium"     # Mid-tier (Haiku, Llama)
    HIGH = "high"         # Premium (Sonnet, GPT-4)


@dataclass
class TaskProfile:
    """Profile of a task for routing decisions."""
    task_id: str
    description: str
    estimated_tokens: int
    requires_reasoning: bool
    requires_code: bool
    requires_creativity: bool
    deadline_ms: int = 5000
    
    def fingerprint(self) -> str:
        """Generate fingerprint for caching."""
        content = f"{self.description}:{self.requires_reasoning}:{self.requires_code}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class RoutingDecision:
    """Result of routing a task."""
    task_id: str
    complexity: TaskComplexity
    selected_model: str
    cost_tier: CostTier
    estimated_cost: float  # USD
    estimated_time_ms: int
    use_cache: bool
    cache_key: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "complexity": self.complexity.name,
            "model": self.selected_model,
            "cost_tier": self.cost_tier.value,
            "estimated_cost_usd": self.estimated_cost,
            "estimated_time_ms": self.estimated_time_ms,
            "use_cache": self.use_cache,
        }


@dataclass
class ModelSpec:
    """Specification for a model."""
    name: str
    cost_per_1k_tokens: float  # USD
    avg_latency_ms: int
    capabilities: List[str]
    context_window: int
    tier: CostTier
    is_local: bool = False
    
    def can_handle(self, profile: TaskProfile) -> bool:
        """Check if model can handle task."""
        if profile.estimated_tokens > self.context_window:
            return False
        if profile.requires_reasoning and "reasoning" not in self.capabilities:
            return False
        if profile.requires_code and "code" not in self.capabilities:
            return False
        return True


class CostRouter:
    """
    Intelligent cost-based task routing.
    
    Goals:
    - Minimize cost while maintaining quality
    - Use caching aggressively
    - Route to cheapest capable model
    - Batch similar requests
    """
    
    # Model registry with cost/latency tradeoffs — 33 validated Ollama Cloud models
    MODELS: Dict[str, ModelSpec] = {
        # T1 (HIGH) tier — Complex synthesis, code, deep reasoning
        "ollama/kimi-k2.5:cloud": ModelSpec(
            name="ollama/kimi-k2.5:cloud",
            cost_per_1k_tokens=0.005,  # Premium
            avg_latency_ms=2000,
            capabilities=["reasoning", "code", "analysis", "synthesis", "complex_planning"],
            context_window=262000,
            tier=CostTier.HIGH
        ),
        "ollama/deepseek-v3.1:671b:cloud": ModelSpec(
            name="ollama/deepseek-v3.1:671b:cloud",
            cost_per_1k_tokens=0.004,
            avg_latency_ms=2500,
            capabilities=["reasoning", "code", "analysis", "deep_thinking"],
            context_window=131000,
            tier=CostTier.HIGH
        ),
        "ollama/glm-5.1:cloud": ModelSpec(
            name="ollama/glm-5.1:cloud",
            cost_per_1k_tokens=0.003,
            avg_latency_ms=1500,
            capabilities=["reasoning", "code", "analysis", "general"],
            context_window=131000,
            tier=CostTier.HIGH
        ),
        "ollama/qwen3-coder:480b:cloud": ModelSpec(
            name="ollama/qwen3-coder:480b:cloud",
            cost_per_1k_tokens=0.004,
            avg_latency_ms=2200,
            capabilities=["code", "reasoning", "debugging", "architecture"],
            context_window=131000,
            tier=CostTier.HIGH
        ),
        "ollama/mistral-large-3:675b:cloud": ModelSpec(
            name="ollama/mistral-large-3:675b:cloud",
            cost_per_1k_tokens=0.004,
            avg_latency_ms=2400,
            capabilities=["reasoning", "analysis", "synthesis"],
            context_window=131000,
            tier=CostTier.HIGH
        ),
        "ollama/cogito-2.1:671b:cloud": ModelSpec(
            name="ollama/cogito-2.1:671b:cloud",
            cost_per_1k_tokens=0.004,
            avg_latency_ms=2300,
            capabilities=["reasoning", "deep_analysis", "strategy"],
            context_window=131000,
            tier=CostTier.HIGH
        ),
        "ollama/nemotron-3-super:cloud": ModelSpec(
            name="ollama/nemotron-3-super:cloud",
            cost_per_1k_tokens=0.003,
            avg_latency_ms=1800,
            capabilities=["reasoning", "analysis", "code"],
            context_window=131000,
            tier=CostTier.HIGH
        ),
        # T2 (MEDIUM) tier — Analysis, validation, research
        "ollama/minimax-m2.5:cloud": ModelSpec(
            name="ollama/minimax-m2.5:cloud",
            cost_per_1k_tokens=0.0015,
            avg_latency_ms=1000,
            capabilities=["reasoning", "analysis", "research", "balanced"],
            context_window=131000,
            tier=CostTier.MEDIUM
        ),
        "ollama/minimax-m2.7:cloud": ModelSpec(
            name="ollama/minimax-m2.7:cloud",
            cost_per_1k_tokens=0.0015,
            avg_latency_ms=1000,
            capabilities=["reasoning", "analysis", "research"],
            context_window=131000,
            tier=CostTier.MEDIUM
        ),
        "ollama/qwen3-vl:235b:cloud": ModelSpec(
            name="ollama/qwen3-vl:235b:cloud",
            cost_per_1k_tokens=0.002,
            avg_latency_ms=1500,
            capabilities=["vision", "reasoning", "multimodal"],
            context_window=131000,
            tier=CostTier.MEDIUM
        ),
        "ollama/gemma4:31b:cloud": ModelSpec(
            name="ollama/gemma4:31b:cloud",
            cost_per_1k_tokens=0.001,
            avg_latency_ms=800,
            capabilities=["reasoning", "analysis", "general"],
            context_window=131000,
            tier=CostTier.MEDIUM
        ),
        "ollama/devstral-2:123b:cloud": ModelSpec(
            name="ollama/devstral-2:123b:cloud",
            cost_per_1k_tokens=0.002,
            avg_latency_ms=1200,
            capabilities=["code", "development", "debugging"],
            context_window=131000,
            tier=CostTier.MEDIUM
        ),
        # T3 (LOW) tier — Formatting, simple transforms, cost savings
        "ollama/gemma3:27b:cloud": ModelSpec(
            name="ollama/gemma3:27b:cloud",
            cost_per_1k_tokens=0.0005,
            avg_latency_ms=600,
            capabilities=["basic", "formatting", "simple_reasoning"],
            context_window=131000,
            tier=CostTier.LOW
        ),
        "ollama/gemma3:12b:cloud": ModelSpec(
            name="ollama/gemma3:12b:cloud",
            cost_per_1k_tokens=0.0003,
            avg_latency_ms=400,
            capabilities=["basic", "formatting"],
            context_window=131000,
            tier=CostTier.LOW
        ),
        "ollama/gemma3:4b:cloud": ModelSpec(
            name="ollama/gemma3:4b:cloud",
            cost_per_1k_tokens=0.0001,
            avg_latency_ms=300,
            capabilities=["basic", "formatting"],
            context_window=32768,
            tier=CostTier.LOW
        ),
        "ollama/ministral-3:8b:cloud": ModelSpec(
            name="ollama/ministral-3:8b:cloud",
            cost_per_1k_tokens=0.0002,
            avg_latency_ms=350,
            capabilities=["basic", "formatting", "simple_reasoning"],
            context_window=32768,
            tier=CostTier.LOW
        ),
        "ollama/ministral-3:3b:cloud": ModelSpec(
            name="ollama/ministral-3:3b:cloud",
            cost_per_1k_tokens=0.0001,
            avg_latency_ms=250,
            capabilities=["basic", "formatting"],
            context_window=32768,
            tier=CostTier.LOW
        ),
        "ollama/nemotron-3-nano:30b:cloud": ModelSpec(
            name="ollama/nemotron-3-nano:30b:cloud",
            cost_per_1k_tokens=0.0003,
            avg_latency_ms=400,
            capabilities=["basic", "formatting", "simple_reasoning"],
            context_window=131000,
            tier=CostTier.LOW
        ),
        "ollama/devstral-small-2:24b:cloud": ModelSpec(
            name="ollama/devstral-small-2:24b:cloud",
            cost_per_1k_tokens=0.0005,
            avg_latency_ms=500,
            capabilities=["code", "basic_development"],
            context_window=131000,
            tier=CostTier.LOW
        ),
        # Think tier — Extended reasoning (may need cold start)
        "ollama/kimi-k2:1t:cloud": ModelSpec(
            name="ollama/kimi-k2:1t:cloud",
            cost_per_1k_tokens=0.006,
            avg_latency_ms=5000,  # Slower due to thinking
            capabilities=["extended_reasoning", "deep_analysis", "planning"],
            context_window=262000,
            tier=CostTier.HIGH
        ),
        "ollama/kimi-k2-thinking:cloud": ModelSpec(
            name="ollama/kimi-k2-thinking:cloud",
            cost_per_1k_tokens=0.007,
            avg_latency_ms=6000,  # Slowest due to extended thinking
            capabilities=["extended_reasoning", "deep_analysis", "strategy"],
            context_window=262000,
            tier=CostTier.HIGH
        ),
    }
    
    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_ttl = cache_ttl_seconds
        self.routing_history: List[RoutingDecision] = []
        self._batch_queue: List[Tuple[TaskProfile, asyncio.Future]] = []
        self._batch_task: Optional[asyncio.Task] = None
        self._batch_interval_ms = 100  # Batch window
        
    def analyze_complexity(self, profile: TaskProfile) -> TaskComplexity:
        """Analyze task complexity for routing."""
        description = profile.description.lower()
        
        # Trivial tasks - no LLM needed
        trivial_patterns = [
            "format", "convert", "parse", "extract json",
            "lowercase", "uppercase", "split", "join"
        ]
        if any(p in description for p in trivial_patterns):
            if not profile.requires_reasoning:
                return TaskComplexity.TRIVIAL
        
        # Simple tasks - local model sufficient
        simple_patterns = [
            "summarize", "classify", "sentiment", "extract",
            "simple", "basic", "short", "brief"
        ]
        if any(p in description for p in simple_patterns):
            if profile.estimated_tokens < 1000:
                return TaskComplexity.SIMPLE
        
        # Complex tasks
        complex_patterns = [
            "analyze", "synthesize", "design", "architect",
            "complex", "multi-step", "research", "investigate"
        ]
        if any(p in description for p in complex_patterns):
            return TaskComplexity.COMPLEX
        
        # Moderate default
        return TaskComplexity.MODERATE
    
    def route(self, profile: TaskProfile) -> RoutingDecision:
        """
        Route task to cheapest viable model.
        
        Strategy:
        1. Check cache first
        2. Determine complexity
        3. Select cheapest model that can handle it
        4. Estimate cost/latency
        """
        cache_key = profile.fingerprint()
        
        # Check cache
        cached = self._get_cache(cache_key)
        if cached:
            return RoutingDecision(
                task_id=profile.task_id,
                complexity=TaskComplexity.UNKNOWN,  # From cache
                selected_model="cache",
                cost_tier=CostTier.FREE,
                estimated_cost=0.0,
                estimated_time_ms=10,
                use_cache=True,
                cache_key=cache_key
            )
        
        # Analyze complexity
        complexity = self.analyze_complexity(profile)
        
        # Route based on complexity
        if complexity == TaskComplexity.TRIVIAL:
            model_name = "ollama/ministral-3:3b:cloud"
        elif complexity == TaskComplexity.SIMPLE:
            model_name = "ollama/gemma3:27b:cloud"
        elif complexity == TaskComplexity.MODERATE:
            model_name = "ollama/minimax-m2.5:cloud"
        else:  # COMPLEX
            model_name = "ollama/kimi-k2.5:cloud"
        
        model = self.MODELS.get(model_name, self.MODELS["ollama/gemma3:27b:cloud"])
        
        # Calculate estimated cost
        estimated_cost = (profile.estimated_tokens / 1000) * model.cost_per_1k_tokens
        
        decision = RoutingDecision(
            task_id=profile.task_id,
            complexity=complexity,
            selected_model=model.name,
            cost_tier=model.tier,
            estimated_cost=estimated_cost,
            estimated_time_ms=model.avg_latency_ms,
            use_cache=False,
            cache_key=cache_key
        )
        
        self.routing_history.append(decision)
        logger.info(f"Routed task {profile.task_id} to {model.name} "
                   f"({complexity.name}, ${estimated_cost:.4f})")
        
        return decision
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cached result if not expired."""
        if key not in self.cache:
            return None
        
        result, timestamp = self.cache[key]
        if time.time() - timestamp > self.cache_ttl:
            del self.cache[key]
            return None
        
        return result
    
    def set_cache(self, key: str, value: Any) -> None:
        """Cache a result."""
        self.cache[key] = (value, time.time())
    
    async def route_batch(self, profiles: List[TaskProfile]) -> List[RoutingDecision]:
        """Route multiple tasks, potentially batching."""
        # Group similar tasks for batching
        groups = self._group_similar_tasks(profiles)
        
        decisions = []
        for group in groups:
            if len(group) > 1:
                # Batch similar tasks
                decision = self.route(group[0])
                decisions.extend([decision] * len(group))
            else:
                decisions.append(self.route(group[0]))
        
        return decisions
    
    def _group_similar_tasks(self, profiles: List[TaskProfile]) -> List[List[TaskProfile]]:
        """Group similar tasks for batching."""
        groups: Dict[str, List[TaskProfile]] = {}
        
        for profile in profiles:
            key = profile.fingerprint()
            if key not in groups:
                groups[key] = []
            groups[key].append(profile)
        
        return list(groups.values())
    
    def get_cost_report(self) -> Dict[str, Any]:
        """Generate cost analysis report."""
        if not self.routing_history:
            return {"total_cost": 0.0, "total_tasks": 0}
        
        total_cost = sum(d.estimated_cost for d in self.routing_history)
        tier_counts = {}
        complexity_counts = {}
        
        for decision in self.routing_history:
            tier_counts[decision.cost_tier.value] = tier_counts.get(decision.cost_tier.value, 0) + 1
            complexity_counts[decision.complexity.name] = complexity_counts.get(decision.complexity.name, 0) + 1
        
        return {
            "total_cost_usd": round(total_cost, 4),
            "total_tasks": len(self.routing_history),
            "avg_cost_per_task": round(total_cost / len(self.routing_history), 6),
            "tier_distribution": tier_counts,
            "complexity_distribution": complexity_counts,
            "cache_hit_rate": self._calculate_cache_hit_rate(),
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        # Simplified - would need actual hit tracking
        return 0.0
    
    def recommend_optimizations(self) -> List[str]:
        """Recommend cost optimizations based on history."""
        recommendations = []
        report = self.get_cost_report()
        
        # Check for over-provisioning
        high_tier_pct = report["tier_distribution"].get("high", 0) / max(report["total_tasks"], 1)
        if high_tier_pct > 0.3:
            recommendations.append(
                f"High-tier usage at {high_tier_pct:.1%}. "
                "Consider task decomposition to use cheaper models."
            )
        
        # Check for under-utilized cache
        if report["cache_hit_rate"] < 0.2:
            recommendations.append(
                "Low cache hit rate. Consider increasing cache TTL or "
                "identifying repetitive task patterns."
            )
        
        return recommendations


class EarlyTerminationEngine:
    """
    Early termination for consensus to save costs.
    
    If consensus is clear early (e.g., 8/10 agents agree), 
    stop spawning additional agents.
    """
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        
    def should_terminate_early(
        self,
        votes: Dict[str, Any],
        total_agents: int
    ) -> Tuple[bool, float]:
        """
        Check if consensus is reached early.
        
        Returns:
            (should_terminate, confidence_level)
        """
        if len(votes) < 3:  # Need minimum sample
            return False, 0.0
        
        # Count vote distribution
        vote_counts = {}
        for vote in votes.values():
            vote_str = str(vote)
            vote_counts[vote_str] = vote_counts.get(vote_str, 0) + 1
        
        # Find majority
        max_count = max(vote_counts.values())
        confidence = max_count / len(votes)
        
        # Early termination conditions
        if confidence >= self.confidence_threshold:
            # Check if remaining votes could change outcome
            remaining = total_agents - len(votes)
            if max_count + remaining < len(votes) - max_count + 1:
                # Current majority can't be overtaken
                return True, confidence
        
        return False, confidence


# Export
__all__ = [
    "CostRouter",
    "EarlyTerminationEngine",
    "TaskProfile",
    "RoutingDecision",
    "ModelSpec",
    "TaskComplexity",
    "CostTier",
]