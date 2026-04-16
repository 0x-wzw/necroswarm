---
name: agent-identity
description: ERC-8004 agent identity management. Register AI agents on-chain, update reputation scores, query the validation registry, and manage agent attestations. Use when operating autonomous agents that need verifiable identity (e.g., DeFi transactions, governance participation, cross-agent trust). Requires web3 wallet with gas for on-chain calls.
---

# Agent Identity (ERC-8004)

ERC-8004 defines a standard for AI agent on-chain identity. This skill handles registration, reputation updates, and validation queries.

## What ERC-8004 Provides

- **Agent Registry** — on-chain map of agent IDs to metadata (name, version, capabilities)
- **Reputation Scores** — mutable scores updated by authorized validators
- **Validation Registry** — check if an agent is registered and trusted
- **Attestations** — signed claims about agent behavior/purpose

## Prerequisites

- **Wallet** — EOA or smart wallet with gas (for writes)
- **RPC URL** — e.g., from Infura, Alchemy, or public RPC
- **Agent contract address** — deployed ERC-8004 registry on your target chain

## Configuration

```bash
export AGENT_REGISTRY_ADDRESS="0x..."        # ERC-8004 registry
export WEB3_RPC_URL="https://eth-mainnet.alchemy.io/..."  # or use ETH_RPC_URL
export AGENT_WALLET_PRIVATE_KEY="0x..."       # for writes
```

## Core Operations

### Register an Agent

```bash
# Register agent with metadata
cast send $AGENT_REGISTRY_ADDRESS \
  "register((string,string,bytes32,uint256))" \
  '("MyAgent","v1.0",0x...,1710000000)' \
  --rpc-url $WEB3_RPC_URL \
  --private-key $AGENT_WALLET_PRIVATE_KEY
```

### Query Registration

```bash
# Check if agent is registered
cast call $AGENT_REGISTRY_ADDRESS \
  "isRegistered(address)" $AGENT_ADDRESS \
  --rpc-url $WEB3_RPC_URL

# Get agent metadata
cast call $AGENT_REGISTRY_ADDRESS \
  "getAgent(address)" $AGENT_ADDRESS \
  --rpc-url $WEB3_RPC_URL
```

### Update Reputation

```bash
# Validator updates reputation score (0-100)
cast send $AGENT_REGISTRY_ADDRESS \
  "updateReputation(address,uint256)" \
  $AGENT_ADDRESS 85 \
  --rpc-url $WEB3_RPC_URL \
  --private-key $VALIDATOR_PRIVATE_KEY
```

### Query Reputation

```bash
cast call $AGENT_REGISTRY_ADDRESS \
  "getReputation(address)" $AGENT_ADDRESS \
  --rpc-url $WEB3_RPC_URL
```

### Add/Verify Attestation

```bash
# Submit attestation (signed claim)
cast send $AGENT_REGISTRY_ADDRESS \
  "addAttestation(address,bytes)" \
  $AGENT_ADDRESS $SIGNATURE \
  --rpc-url $WEB3_RPC_URL \
  --private-key $ATTESTER_PRIVATE_KEY
```

## Use Cases

### Trust Gate for DeFi Protocol

Before executing a high-value tx, check the agent's reputation:
```bash
REPUTATION=$(cast call $AGENT_REGISTRY_ADDRESS "getReputation(address)" $AGENT_ID --rpc-url $WEB3_RPC_URL)
if [ "$REPUTATION" -lt 70 ]; then
  echo "Low reputation — flag for human review"
fi
```

### Cross-Agent Trust establishment

When two agents need to cooperate (e.g., a swap agent + a lending agent):
```bash
IS_REGISTERED=$(cast call $AGENT_REGISTRY_ADDRESS "isRegistered(address)" $PARTNER_AGENT --rpc-url $WEB3_RPC_URL)
```

### Governance Participation

Agents voting in a DAO can use ERC-8004 to prove identity:
```bash
cast call $AGENT_REGISTRY_ADDRESS "getAgent(address)" $PROPOSER_AGENT --rpc-url $WEB3_RPC_URL
```

## Notes

- ERC-8004 is an emerging standard — verify contract interface matches
- Reputation is subjective — always check validator source
- Gas costs apply for all write operations
- Test on testnet before mainnet deployment

## References

- [ERC-8004 Draft](https://eips.ethereum.org/EIPS/eip-8004)
- [Agent Identity Workshop](https://ethereum-magicians.org/t/erc-8004-agent-identity-standard/)
