#!/usr/bin/env python3
"""10-D Council Cost Tracker - Tracks per-validation costs and savings vs single-model."""

import json
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


class ValidationTier(Enum):
    """Validation tiers for cost tracking."""
    FAST_PATH = "fast_path"
    CONFIDENCE_TIERING = "confidence"
    FULL_COUNCIL = "full_council"
    ESCALATED = "escalated"


@dataclass
class ModelCostConfig:
    """Cost configuration for different model tiers."""
    T1_COST_PER_1K_TOKENS: float = 0.015
    T2_COST_PER_1K_TOKENS: float = 0.005
    T3_COST_PER_1K_TOKENS: float = 0.001

    AVG_TOKENS_PER_CALL: int = 2000

    def get_cost_per_call(self, tier: str) -> float:
        """Calculate cost per model call."""
        tokens = self.AVG_TOKENS_PER_CALL
        if tier == "T1":
            return (tokens / 1000) * self.T1_COST_PER_1K_TOKENS
        elif tier == "T2":
            return (tokens / 1000) * self.T2_COST_PER_1K_TOKENS
        elif tier == "T3":
            return (tokens / 1000) * self.T3_COST_PER_1K_TOKENS
        return 0.0


@dataclass
class ValidationRecord:
    """Record of a single validation session."""
    claim_id: str
    stakes_level: str
    tier: ValidationTier
    timestamp_start: float
    timestamp_end: Optional[float] = None
    model_calls: List[Dict[str, Any]] = field(default_factory=list)
    final_confidence: float = 0.0
    verdict: Optional[str] = None
    cost_saved_vs_full_council: float = 0.0

    @property
    def duration_seconds(self) -> float:
        """Get validation duration."""
        if self.timestamp_end:
            return self.timestamp_end - self.timestamp_start
        return time.time() - self.timestamp_start

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['duration_seconds'] = self.duration_seconds
        result['tier'] = self.tier.value
        return result


class CostTracker:
    """Tracks costs and savings for 10-D Council validations."""

    _instance: Optional["CostTracker"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, cost_config: Optional[ModelCostConfig] = None):
        if self._initialized:
            return
        self._initialized = True
        self.cost_config = cost_config or ModelCostConfig()
        self.active_validations: Dict[str, ValidationRecord] = {}
        self.completed_validations: List[ValidationRecord] = []
        self.full_council_tiers = ["T1", "T1", "T2", "T2", "T3", "T3"]

    def start_validation(self, claim_id: str, stakes_level: str = "medium") -> ValidationRecord:
        """Start tracking a new validation."""
        record = ValidationRecord(
            claim_id=claim_id,
            stakes_level=stakes_level,
            tier=ValidationTier.FULL_COUNCIL,
            timestamp_start=time.time()
        )
        self.active_validations[claim_id] = record
        return record

    def record_model_call(self, claim_id: str, model_name: str, tier: str,
                          tokens_in: int = 1000, tokens_out: int = 1000) -> None:
        """Record a model API call for a validation."""
        if claim_id not in self.active_validations:
            self.start_validation(claim_id)

        cost = self._calculate_call_cost(tier, tokens_in, tokens_out)

        self.active_validations[claim_id].model_calls.append({
            "model": model_name,
            "tier": tier,
            "timestamp": time.time(),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost
        })

    def _calculate_call_cost(self, tier: str, tokens_in: int, tokens_out: int) -> float:
        """Calculate cost for a model call."""
        base_cost = self.cost_config.get_cost_per_call(tier)
        token_ratio = (tokens_in + tokens_out) / (2 * self.cost_config.AVG_TOKENS_PER_CALL)
        return base_cost * max(0.5, token_ratio)

    def complete_validation(self, claim_id: str, tier: ValidationTier,
                          confidence: float, verdict: Optional[str] = None) -> ValidationRecord:
        """Complete a validation and calculate savings."""
        if claim_id not in self.active_validations:
            raise ValueError(f"No active validation found for {claim_id}")

        record = self.active_validations[claim_id]
        record.tier = tier
        record.final_confidence = confidence
        record.verdict = verdict
        record.timestamp_end = time.time()
        record.cost_saved_vs_full_council = self._calculate_savings(record)

        self.completed_validations.append(record)
        del self.active_validations[claim_id]

        return record

    def _calculate_savings(self, record: ValidationRecord) -> float:
        """Calculate cost saved vs running full council."""
        actual_cost = sum(call["cost_usd"] for call in record.model_calls)
        full_council_cost = self._get_full_council_cost(record.stakes_level)
        return max(0, full_council_cost - actual_cost)

    def _get_full_council_cost(self, stakes_level: str) -> float:
        """Get baseline cost for full council based on stakes."""
        if stakes_level == "low":
            tiers = ["T2", "T3"]
        elif stakes_level == "medium":
            tiers = ["T1", "T2", "T3"]
        else:
            tiers = self.full_council_tiers

        return sum(self.cost_config.get_cost_per_call(t) for t in tiers)

    def get_dashboard(self) -> "CostDashboard":
        """Get dashboard with aggregated statistics."""
        return CostDashboard(self.completed_validations, self.active_validations, self.cost_config)

    def get_fast_path_stats(self) -> Dict[str, Any]:
        """Get statistics specific to fast-path validations."""
        fast_path = [r for r in self.completed_validations
                     if r.tier == ValidationTier.FAST_PATH]
        confidence_skipped = [r for r in self.completed_validations
                              if r.tier == ValidationTier.CONFIDENCE_TIERING]
        full_council = [r for r in self.completed_validations
                       if r.tier == ValidationTier.FULL_COUNCIL]

        total_actual_cost = sum(
            sum(c["cost_usd"] for c in r.model_calls) for r in self.completed_validations
        )
        full_council_baseline = sum(
            self._get_full_council_cost(r.stakes_level) for r in self.completed_validations
        )

        return {
            "fast_path_validations": len(fast_path),
            "confidence_tiering_skipped": len(confidence_skipped),
            "full_council_validations": len(full_council),
            "total_validations": len(self.completed_validations),
            "total_cost_usd": round(total_actual_cost, 4),
            "estimated_full_council_cost_usd": round(full_council_baseline, 4),
            "total_savings_usd": round(full_council_baseline - total_actual_cost, 4),
            "savings_percentage": round(((full_council_baseline - total_actual_cost) / full_council_baseline * 100), 1)
                                   if full_council_baseline > 0 else 0,
        }


class CostDashboard:
    """Dashboard for visualizing cost metrics."""

    def __init__(self, completed: List[ValidationRecord],
                 active: Dict[str, ValidationRecord],
                 cost_config: ModelCostConfig):
        self.completed = completed
        self.active = active
        self.cost_config = cost_config

    def get_summary(self) -> Dict[str, Any]:
        """Get high-level summary metrics."""
        total = len(self.completed)
        if total == 0:
            return {"message": "No validations completed yet"}

        by_tier = {
            "fast_path": len([r for r in self.completed if r.tier == ValidationTier.FAST_PATH]),
            "confidence_tiering": len([r for r in self.completed if r.tier == ValidationTier.CONFIDENCE_TIERING]),
            "full_council": len([r for r in self.completed if r.tier == ValidationTier.FULL_COUNCIL]),
            "escalated": len([r for r in self.completed if r.tier == ValidationTier.ESCALATED])
        }

        total_savings = sum(r.cost_saved_vs_full_council for r in self.completed)
        actual_costs = [sum(c["cost_usd"] for c in r.model_calls) for r in self.completed]

        avg_confidence = sum(r.final_confidence for r in self.completed) / total
        avg_duration = sum(r.duration_seconds for r in self.completed) / total

        return {
            "total_validations": total,
            "active_validations": len(self.active),
            "by_tier": by_tier,
            "tier_distribution": {k: round(v/total*100, 1) for k, v in by_tier.items()},
            "total_cost_usd": round(sum(actual_costs), 4),
            "total_savings_usd": round(total_savings, 4),
            "savings_percentage": round(total_savings / (sum(actual_costs) + total_savings) * 100, 1)
                                   if (sum(actual_costs) + total_savings) > 0 else 0,
            "average_confidence": round(avg_confidence, 3),
            "average_duration_seconds": round(avg_duration, 2),
            "estimated_cost_per_model_tier": {
                "T1": round(self.cost_config.get_cost_per_call("T1"), 4),
                "T2": round(self.cost_config.get_cost_per_call("T2"), 4),
                "T3": round(self.cost_config.get_cost_per_call("T3"), 4)
            }
        }

    def print_console(self) -> None:
        """Print dashboard to console."""
        print("\n" + "="*60)
        print("10-D COUNCIL COST DASHBOARD")
        print("="*60)

        summary = self.get_summary()

        print(f"\nSummary:")
        print(f"  Total Validations: {summary.get('total_validations', 0)}")
        print(f"  Active: {summary.get('active_validations', 0)}")

        if 'by_tier' in summary:
            print(f"\nTier Distribution:")
            for tier, count in summary['by_tier'].items():
                pct = summary['tier_distribution'].get(tier, 0)
                print(f"  {tier}: {count} ({pct}%)")

        if 'total_cost_usd' in summary:
            print(f"\nCost Analysis:")
            print(f"  Total Cost: ${summary['total_cost_usd']}")
            print(f"  Total Savings: ${summary['total_savings_usd']}")
            print(f"  Savings: {summary['savings_percentage']}%")

        print("\n" + "="*60)


if __name__ == "__main__":
    tracker = CostTracker()

    # Demo
    for i in range(3):
        claim_id = f"demo_{i}"
        tracker.start_validation(claim_id, stakes_level="medium")
        tracker.record_model_call(claim_id, "qwen", "T3", 800, 600)
        tracker.complete_validation(claim_id, ValidationTier.FAST_PATH, 0.85, "CONFIRMED")

    tracker.get_dashboard().print_console()
    print(json.dumps(tracker.get_fast_path_stats(), indent=2))
