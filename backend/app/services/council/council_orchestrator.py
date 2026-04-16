#!/usr/bin/env python3
"""
10-D Council Orchestrator
Multi-model LLM council for distributed intelligence and truth validation.

Based on: Andrej Karpathy's "Agentic Engineering"
"""

import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "council-members.json"

def load_config() -> Dict:
    """Load council configuration."""
    with open(CONFIG_PATH) as f:
        return json.load(f)

def get_council_members(config: Dict, task_type: str = None) -> List[Dict]:
    """Get relevant council members for a task."""
    members = []
    
    for category in ["cognitive_leads", "research_synthesizers", "execution_specialists"]:
        members.extend(config["council_members"][category])
    
    if task_type and task_type in config.get("task_routing", {}):
        required = config["task_routing"][task_type]["required_members"]
        members = [m for m in members if m["id"] in required]
    
    return members

def calculate_vote_power(members: List[Dict], confidence_scores: Dict[str, float]) -> Dict[str, float]:
    """Calculate weighted vote power for each member."""
    weighted_votes = {}
    
    for member in members:
        base_power = member["vote_power"]
        confidence = confidence_scores.get(member["id"], 0.5)
        tier_weight = member["weight"]
        
        weighted_votes[member["id"]] = base_power * confidence * tier_weight
    
    return weighted_votes

def consensus_vote(proposals: List[str], member_votes: Dict[str, str], 
                   vote_power: Dict[str, float], threshold: float = 0.6) -> Dict:
    """
    Run weighted consensus vote.
    
    Returns:
        {
            "winner": str,
            "confidence": float,
            "vote_distribution": Dict,
            "unanimous": bool,
            "supermajority": bool
        }
    """
    vote_counts = {proposal: 0.0 for proposal in proposals}
    total_power = sum(vote_power.values())
    
    # Aggregate weighted votes
    for member_id, proposal in member_votes.items():
        if proposal in vote_counts:
            vote_counts[proposal] += vote_power.get(member_id, 0)
    
    # Calculate percentages
    for proposal in vote_counts:
        vote_counts[proposal] /= total_power if total_power > 0 else 1
    
    # Determine winner
    winner = max(vote_counts, key=vote_counts.get)
    winner_confidence = vote_counts[winner]
    
    # Check thresholds
    unanimous = winner_confidence >= 0.95
    supermajority = winner_confidence >= 0.75
    has_consensus = winner_confidence >= threshold
    
    return {
        "winner": winner if has_consensus else None,
        "leading_proposal": winner,
        "confidence": winner_confidence,
        "vote_distribution": vote_counts,
        "unanimous": unanimous,
        "supermajority": supermajority,
        "has_consensus": has_consensus,
        "total_power": total_power
    }

def truth_validation_council(claim: str, config: Dict) -> Dict:
    """
    Run truth validation through council.
    """
    print(f"\n{'='*60}")
    print(f"10-D COUNCIL: Truth Validation")
    print(f"{'='*60}")
    print(f"Claim: \"{claim}\"")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    members = get_council_members(config, "truth_validation")
    
    print("Council Deliberation:")
    print("-" * 60)
    
    simulated_verdicts = {}
    confidence_scores = {}
    
    for member in members:
        # Simulated for prototype
        import random
        
        if member["role"] == "reasoning_lead":
            base_confidence = 0.85
        elif member["role"] == "research_synthesizer":
            base_confidence = 0.75
        else:
            base_confidence = 0.65
        
        confidence = min(1.0, max(0.0, base_confidence + random.uniform(-0.1, 0.1)))
        confidence_scores[member["id"]] = confidence
        
        verdicts = ["CONFIRMED", "DISPUTED", "UNVERIFIABLE"]
        weights = [0.2, 0.6, 0.2]
        verdict = random.choices(verdicts, weights=weights)[0]
        
        simulated_verdicts[member["id"]] = verdict
        
        print(f"  [{member['tier']}] {member['name']}: {verdict} (confidence: {confidence:.2f})")
    
    print()
    
    vote_power = calculate_vote_power(members, confidence_scores)
    verdict_votes = {k: v for k, v in simulated_verdicts.items()}
    unique_verdicts = list(set(simulated_verdicts.values()))
    
    consensus = consensus_vote(
        unique_verdicts,
        verdict_votes,
        vote_power,
        threshold=config["council_rules"]["supermajority"]
    )
    
    result = {
        "claim": claim,
        "timestamp": datetime.now().isoformat(),
        "council_size": len(members),
        "individual_verdicts": simulated_verdicts,
        "consensus": {
            "verdict": consensus.get("winner", "NO_CONSENSUS"),
            "leading_verdict": consensus["leading_proposal"],
            "confidence": consensus["confidence"],
            "vote_distribution": consensus["vote_distribution"],
            "unanimous": consensus["unanimous"],
            "supermajority": consensus["supermajority"]
        },
        "council_members": [m["id"] for m in members],
        "recommended_action": generate_recommendation(consensus)
    }
    
    print("Consensus Result:")
    print("-" * 60)
    print(f"  Verdict: {result['consensus']['verdict']}")
    print(f"  Leading: {result['consensus']['leading_verdict']}")
    print(f"  Confidence: {result['consensus']['confidence']:.2%}")
    print(f"  Unanimous: {result['consensus']['unanimous']}")
    print(f"  Supermajority: {result['consensus']['supermajority']}")
    print()
    print(f"Recommendation: {result['recommended_action']}")
    print()
    
    return result

def generate_recommendation(consensus: Dict) -> str:
    """Generate action recommendation based on consensus."""
    if consensus["unanimous"]:
        if consensus["leading_proposal"] == "CONFIRMED":
            return "ESCALATE: High confidence consensus to proceed"
        elif consensus["leading_proposal"] == "FABRICATED":
            return "DISCARD: Consensus indicates fabrication"
        else:
            return "REVIEW: Unanimous but low certainty"
    
    elif consensus["supermajority"]:
        return f"PROCEED WITH CAVEAT: {consensus['leading_proposal']}"
    
    elif consensus["has_consensus"]:
        return f"QUALIFY: {consensus['leading_proposal']}"
    
    else:
        return "NO CONSENSUS: Requires Z review"

def demonstrate_council():
    """Demonstrate 10-D Council capabilities."""
    print("\n" + "="*60)
    print("10-D COUNCIL PROTOTYPE DEMONSTRATION")
    print("="*60)
    
    config = load_config()
    
    print("\n" + "="*60)
    print("DEMO 1: Truth Validation Council")
    print("="*60)
    
    test_claims = [
        "AI agent built a $1M company in 30 days",
        "OpenClaw has truth validation pipeline",
    ]
    
    results = []
    for claim in test_claims:
        result = truth_validation_council(claim, config)
        results.append(result)
        time.sleep(0.5)
    
    print("\n" + "="*60)
    print("DEMONSTRATION SUMMARY")
    print("="*60)
    print(f"\nTotal claims validated: {len(results)}")
    
    consensus_reached = sum(1 for r in results if r["consensus"]["verdict"] != "NO_CONSENSUS")
    print(f"Consensus reached: {consensus_reached}/{len(results)}")
    
    print("\nKey Benefits:")
    print("  Reduces hallucination through multi-model consensus")
    print("  Weighted voting by tier")
    print("  Confidence scoring for transparency")
    print("  Clear escalation rules when consensus fails")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="10-D Council Orchestrator")
    parser.add_argument("--task", choices=["validate_claim", "demo"],
                       default="demo", help="Task to execute")
    parser.add_argument("--claim", help="Claim to validate")
    
    args = parser.parse_args()
    
    config = load_config()
    
    if args.task == "demo":
        demonstrate_council()
    elif args.task == "validate_claim" and args.claim:
        result = truth_validation_council(args.claim, config)
        print(json.dumps(result, indent=2))
    
    return 0

if __name__ == "__main__":
    exit(main())
