#!/usr/bin/env python3
"""
10-D Council Consensus Engine
Implements various consensus algorithms for multi-model decision making.
"""

from typing import Dict, List, Any, Optional
from enum import Enum

class ConsensusMethod(Enum):
    WEIGHTED_MAJORITY = "weighted_majority"
    UNANIMOUS = "unanimous"
    SUPERMAJORITY = "supermajority"
    BORDA_COUNT = "borda_count"
    DELPHI_METHOD = "delphi_method"

class ConsensusEngine:
    """Implements consensus algorithms for the 10-D Council."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.method = ConsensusMethod(config.get("consensus_method", "weighted_majority"))
    
    def calculate_weights(self, members: List[Dict], 
                         confidence_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate weighted vote power for each member."""
        weights = {}
        
        for member in members:
            base_power = member.get("vote_power", 1)
            confidence = confidence_scores.get(member["id"], 0.5)
            tier_weight = member.get("weight", 0.5)
            
            weights[member["id"]] = base_power * confidence * tier_weight
        
        return weights
    
    def weighted_majority(self, proposals: List[str],
                         votes: Dict[str, str],
                         weights: Dict[str, float],
                         threshold: float = 0.6) -> Dict:
        """Weighted majority vote with confidence threshold."""
        vote_counts = {p: 0.0 for p in proposals}
        total_power = sum(weights.values())
        
        for member_id, proposal in votes.items():
            if proposal in vote_counts:
                vote_counts[proposal] += weights.get(member_id, 0)
        
        for proposal in vote_counts:
            vote_counts[proposal] = (vote_counts[proposal] / total_power 
                                   if total_power > 0 else 0)
        
        if not vote_counts:
            return {
                "winner": None,
                "confidence": 0.0,
                "vote_distribution": {},
                "has_consensus": False,
                "method": "weighted_majority"
            }
        
        sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
        winner = sorted_votes[0][0]
        winner_confidence = sorted_votes[0][1]
        
        return {
            "winner": winner if winner_confidence >= threshold else None,
            "leading_proposal": winner,
            "confidence": winner_confidence,
            "vote_distribution": vote_counts,
            "has_consensus": winner_confidence >= threshold,
            "unanimous": winner_confidence >= 0.95,
            "supermajority": winner_confidence >= 0.75,
            "method": "weighted_majority",
            "threshold": threshold
        }
    
    def borda_count(self, rankings: Dict[str, List[str]], 
                    weights: Dict[str, float]) -> Dict:
        """Borda count for ranked preferences."""
        scores = {}
        
        for member_id, ranking in rankings.items():
            weight = weights.get(member_id, 1)
            n = len(ranking)
            
            for i, proposal in enumerate(ranking):
                points = (n - i) * weight
                scores[proposal] = scores.get(proposal, 0) + points
        
        if not scores:
            return {"winner": None, "scores": {}}
        
        winner = max(scores, key=scores.get)
        total_score = sum(scores.values())
        
        return {
            "winner": winner,
            "scores": scores,
            "confidence": scores[winner] / total_score if total_score > 0 else 0,
            "method": "borda_count"
        }
    
    def delphi_method(self, estimates: Dict[str, List[float]]) -> Dict:
        """Delphi method for numerical estimation consensus."""
        import statistics
        
        all_estimates = []
        for member_estimates in estimates.values():
            all_estimates.extend(member_estimates)
        
        if not all_estimates:
            return {"consensus": None, "confidence": 0.0}
        
        mean_estimate = statistics.mean(all_estimates)
        median_estimate = statistics.median(all_estimates)
        std_dev = statistics.stdev(all_estimates) if len(all_estimates) > 1 else 0
        
        convergence = 1.0 - (std_dev / mean_estimate if mean_estimate else 0)
        convergence = max(0, min(1, convergence))
        
        return {
            "consensus": median_estimate,
            "mean": mean_estimate,
            "std_dev": std_dev,
            "confidence": convergence,
            "range": (min(all_estimates), max(all_estimates)),
            "method": "delphi_method"
        }
    
    def quorum_check(self, present_members: int, 
                    total_members: int) -> bool:
        """Check if quorum is met."""
        quorum_threshold = self.config.get("council_rules", {}).get("quorum", 0.6)
        return (present_members / total_members) >= quorum_threshold

if __name__ == "__main__":
    # Demo
    config = {"consensus_method": "weighted_majority"}
    engine = ConsensusEngine(config)
    
    proposals = ["Option A", "Option B"]
    votes = {"kimi": "Option A", "claude": "Option A", 
            "deepseek": "Option B", "glm": "Option B"}
    weights = {"kimi": 3.0, "claude": 3.0, "deepseek": 2.0, "glm": 2.0}
    
    result = engine.weighted_majority(proposals, votes, weights, threshold=0.6)
    print(f"Winner: {result['winner']}")
    print(f"Confidence: {result['confidence']:.1%}")
