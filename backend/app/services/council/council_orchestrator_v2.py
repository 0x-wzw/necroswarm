#!/usr/bin/env python3
"""
10-D Council Orchestrator v2.0
Enhanced with fast-path validation and confidence-based tiering.

Usage:
    python council_orchestrator_v2.py --task validate_claim --claim "..." --stakes low
    python council_orchestrator_v2.py --task demo
    python council_orchestrator_v2.py --show-dashboard
"""

import json
import argparse
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from consensus_engine import ConsensusEngine
from cost_tracker import CostTracker, ValidationTier

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "council-members.json"

def load_config() -> Dict:
    """Load council configuration."""
    with open(CONFIG_PATH) as f:
        return json.load(f)

def get_tier_members(config: Dict, tier: str) -> List[Dict]:
    """Get all members of a specific tier."""
    members = []
    for category in ["cognitive_leads", "research_synthesizers", "execution_specialists"]:
        for member in config["council_members"][category]:
            if member["tier"] == tier:
                members.append(member)
    return members

def fast_path_validation(claim: str, config: Dict, stakes_level: str = "low") -> Dict:
    """
    Fast-path validation using single T3 model.
    Bypasses full council for low-stakes claims.
    
    Returns verdict with option to escalate to full council if confidence < 0.7.
    """
    cost_tracker = CostTracker()
    claim_id = str(uuid.uuid4())[:8]
    
    cost_tracker.start_validation(claim_id, stakes_level)
    
    print(f"\n{'='*60}")
    print(f"10-D COUNCIL: Fast-Path Validation")
    print(f"{'='*60}")
    print(f"Claim: \"{claim}\"")
    print(f"Stakes: {stakes_level}")
    print(f"Mode: Single T3 Model (Fast Path)")
    print()
    
    # Get T3 members
    t3_members = get_tier_members(config, "T3")
    if not t3_members:
        return {"error": "No T3 members available"}
    
    # Simulate T3 evaluation (in production: actual API call)
    import random
    member = t3_members[0]  # Use first T3 member
    
    base_confidence = 0.70 if stakes_level == "low" else 0.65
    confidence = min(0.95, base_confidence + random.uniform(-0.05, 0.15))
    
    verdicts = ["CONFIRMED", "DISPUTED", "UNVERIFIABLE"]
    weights = [0.4, 0.4, 0.2]
    verdict = random.choices(verdicts, weights=weights)[0]
    
    cost_tracker.record_model_call(claim_id, member["name"], "T3", 800, 600)
    
    # Check escalation threshold
    escalation_threshold = 0.70
    should_escalate = confidence < escalation_threshold
    
    result = {
        "claim": claim,
        "validation_mode": "fast_path",
        "stakes_level": stakes_level,
        "council_member": member["name"],
        "tier": "T3",
        "verdict": verdict,
        "confidence": confidence,
        "should_escalate": should_escalate,
        "escalation_reason": "confidence_below_threshold" if should_escalate else None,
        "timestamp": datetime.now().isoformat(),
        "claim_id": claim_id
    }
    
    # Complete tracking
    final_tier = ValidationTier.ESCALATED if should_escalate else ValidationTier.FAST_PATH
    cost_tracker.complete_validation(claim_id, final_tier, confidence, verdict)
    
    print(f"T3 Evaluation: {verdict} (confidence: {confidence:.2f})")
    
    if should_escalate:
        print(f"⚠️ ESCALATION TRIGGERED: Confidence {confidence:.2f} < {escalation_threshold}")
        print(f"→ Routing to full council for additional validation...")
        # In production: recursively call full_council_validation
    else:
        print(f"✅ Proceeding with fast-path result (no escalation)")
    
    return result

def confidence_tiered_validation(claim: str, config: Dict, stakes_level: str = "medium") -> Dict:
    """
    Confidence-based tiering: Start with T3, escalate if confidence < 95%.
    More expensive than fast-path but guarantees high confidence.
    """
    cost_tracker = CostTracker()
    claim_id = str(uuid.uuid4())[:8]
    
    cost_tracker.start_validation(claim_id, stakes_level)
    
    print(f"\n{'='*60}")
    print(f"10-D COUNCIL: Confidence-Tiered Validation")
    print(f"{'='*60}")
    print(f"Claim: \"{claim}\"")
    print(f"Stakes: {stakes_level}")
    print(f"Mode: T3 First, Skip Full Council if >95%")
    print()
    
    import random
    
    # Step 1: T3 evaluation
    t3_members = get_tier_members(config, "T3")
    if not t3_members:
        return {"error": "No T3 members available"}
    
    t3_member = t3_members[0]
    t3_confidence = min(0.95, 0.75 + random.uniform(-0.05, 0.20))
    
    verdicts = ["CONFIRMED", "DISPUTED", "UNVERIFIABLE"]
    t3_verdict = random.choices(verdicts, weights=[0.3, 0.5, 0.2])[0]
    
    cost_tracker.record_model_call(claim_id, t3_member["name"], "T3", 800, 600)
    
    print(f"[T3] {t3_member['name']}: {t3_verdict} (confidence: {t3_confidence:.2f})")
    
    # Check if we can skip full council
    skip_threshold = 0.95
    
    if t3_confidence >= skip_threshold:
        # High confidence from T3 alone - skip full council
        cost_tracker.complete_validation(claim_id, ValidationTier.CONFIDENCE_TIERING, 
                                         t3_confidence, t3_verdict)
        
        print(f"\n✅ SKIPPING FULL COUNCIL: T3 confidence {t3_confidence:.2f} >= {skip_threshold}")
        
        return {
            "claim": claim,
            "validation_mode": "confidence_tiered",
            "stakes_level": stakes_level,
            "t3_result": {
                "member": t3_member["name"],
                "verdict": t3_verdict,
                "confidence": t3_confidence
            },
            "full_council_skipped": True,
            "reason": "high_t3_confidence",
            "final_verdict": t3_verdict,
            "final_confidence": t3_confidence,
            "claim_id": claim_id
        }
    else:
        # Low confidence - escalate to full council
        print(f"\n⚠️ LOW T3 CONFIDENCE ({t3_confidence:.2f} < {skip_threshold})")
        print(f"→ Escalating to full council for additional consensus...")
        
        # Continue with full council (simplified)
        t2_members = get_tier_members(config, "T2")
        t1_members = get_tier_members(config, "T1")
        
        for member in t2_members[:2]:
            cost_tracker.record_model_call(claim_id, member["name"], "T2", 1500, 1200)
            print(f"[T2] {member['name']}: Added to deliberation")
        
        for member in t1_members[:1]:
            cost_tracker.record_model_call(claim_id, member["name"], "T1", 2000, 1500)
            print(f"[T1] {member['name']}: Cognitive lead review")
        
        # Simulate consensus
        final_confidence = min(0.99, t3_confidence + 0.15)
        cost_tracker.complete_validation(claim_id, ValidationTier.FULL_COUNCIL, 
                                         final_confidence, t3_verdict)
        
        return {
            "claim": claim,
            "validation_mode": "confidence_tiered_with_escalation",
            "stakes_level": stakes_level,
            "t3_result": {
                "member": t3_member["name"],
                "verdict": t3_verdict,
                "confidence": t3_confidence
            },
            "full_council_skipped": False,
            "final_verdict": t3_verdict,
            "final_confidence": final_confidence,
            "claim_id": claim_id
        }

def show_cost_dashboard():
    """Display the cost dashboard."""
    tracker = CostTracker()
    dashboard = tracker.get_dashboard()
    dashboard.print_console()
    
    stats = tracker.get_fast_path_stats()
    print("\n" + "="*60)
    print("FAST PATH STATISTICS")
    print("="*60)
    for key, value in stats.items():
        print(f"  {key}: {value}")

def demonstrate_enhancements():
    """Demonstrate all 10-D Council enhancement features."""
    config = load_config()
    
    print("\n" + "="*60)
    print("10-D COUNCIL ENHANCEMENTS DEMO")
    print("="*60)
    
    print("\n--- 1. FAST-PATH VALIDATION (Low Stakes) ---")
    result1 = fast_path_validation(
        claim="AI agent completed basic task",
        config=config,
        stakes_level="low"
    )
    print(f"\nResult: {result1['verdict']} (escalate: {result1['should_escalate']})")
    
    print("\n--- 2. FAST-PATH WITH ESCALATION ---")
    result2 = fast_path_validation(
        claim="AI startup raised $100M Series B",
        config=config,
        stakes_level="medium"
    )
    
    print("\n--- 3. CONFIDENCE-TIERED VALIDATION (Skip) ---")
    result3 = confidence_tiered_validation(
        claim="Common data format is JSON",
        config=config,
        stakes_level="low"
    )
    
    print("\n--- 4. CONFIDENCE-TIERED WITH ESCALATION ---")
    result4 = confidence_tiered_validation(
        claim="Revolutionary AI breakthrough announced",
        config=config,
        stakes_level="high"
    )
    
    print("\n--- 5. COST DASHBOARD ---")
    show_cost_dashboard()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="10-D Council Orchestrator v2")
    parser.add_argument("--task", choices=["validate_claim", "fast_path", "confidence_tiered", 
                                           "demo", "show_dashboard"], default="demo")
    parser.add_argument("--claim", help="Claim to validate")
    parser.add_argument("--stakes", choices=["low", "medium", "high"], default="medium")
    
    args = parser.parse_args()
    
    config = load_config()
    
    if args.task == "demo":
        demonstrate_enhancements()
    elif args.task == "show_dashboard":
        show_cost_dashboard()
    elif args.task == "fast_path" and args.claim:
        result = fast_path_validation(args.claim, config, args.stakes)
        print(json.dumps(result, indent=2))
    elif args.task == "confidence_tiered" and args.claim:
        result = confidence_tiered_validation(args.claim, config, args.stakes)
        print(json.dumps(result, indent=2))
    else:
        print("Use --task demo to see enhancements")
    
    return 0

if __name__ == "__main__":
    exit(main())
