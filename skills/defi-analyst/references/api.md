# DeFi Analyst References

## APIs Used

### DeFiLlama
- **Base:** `https://api.llama.fi`
- **Protocol:** `GET /protocol/{name}` — TVL, fees, audits
- **TVL List:** `GET /tvl` — all protocols ranked by TVL
- **Overview:** `GET /overview/dex`, `GET /overview/lending`
- **Rate limit:** ~60 req/min (public)
- **Auth:** None required

### GeckoTerminal
- **Base:** `https://api.geckoterminal.com/api/v2`
- **Network pools:** `GET /networks/{network}/pools`
- **Token info:** `GET /networks/{network}/tokens/{address}/info`
- **Rate limit:** 30 req/min (free tier)
- **Auth:** None required

### Tavily (MCP)
- **Endpoint:** Configured via mcporter MCP client
- **Tools:** `tavily_search`, `tavily_extract`, `tavily_research`
- **Rate limit:** 20 req/min free tier
- **Use for:** News, governance, sentiment, protocol comparisons

## Quick Reference

```bash
# Protocol TVL
curl -s "https://api.llama.fi/protocol/aave" | jq '{tvl, change_1d, change_7d}'

# Top 10 DeFi by TVL
curl -s "https://api.llama.fi/tvl" | jq '.[0:10]'

# Pool APY on BSC
curl -s "https://api.geckoterminal.com/api/v2/networks/bsc/pools" | jq '.[0].attributes | {name, apy}'

# DEX volumes
curl -s "https://api.llama.fi/overview/dex" | jq '.dexes[0:5]'
```

## Notes

- Always use `jq` to extract only needed fields — APIs return large objects
- DeFiLlama TVL = sum of all chains for a protocol
- GeckoTerminal is best for DEX pool-level data
- Tavily fills the gap for qualitative analysis (governance, news, audits)
