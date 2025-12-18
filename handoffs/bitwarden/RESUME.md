# 🚀 Resume Instructions: bitwarden

**Status:** 🟡 IN PROGRESS (Milestone 3 in review)
**Archon Project ID:** `1f1b0204-a804-4266-a451-4d37d0cd25e0`

## Context (Why This Exists)

We're building a **standalone Bitwarden MCP** to replace ad-hoc `bw + jq` parsing in wrapper.sh scripts.

**Current state (Cloudflare DNS):**
```bash
# wrapper.sh - messy, duplicated logic
ITEM_JSON=$(bw get item "Cloudflare DNS Manager")
export CLOUDFLARE_API_TOKEN=$(echo "$ITEM_JSON" | jq -r '.fields[] | select(.name=="CLOUDFLARE_API_TOKEN") | .value')
```

**Future state (after this MCP):**
```bash
# wrapper.sh - clean, centralized
export CLOUDFLARE_API_TOKEN=$(bitwarden-mcp get-secret "Cloudflare DNS Manager" "CLOUDFLARE_API_TOKEN")
```

## Architecture (SETTLED - Don't Re-discuss)

```
bitwarden_client.ts (sacred core - R1-R8 rules enforced)
├── CLI: bitwarden-mcp get-secret "item" "field"  → for wrapper.sh
└── MCP: bitwarden_get_secret(item, field)        → for agents
```

See `LESSONS_LEARNED.md` for why alternatives were rejected.

## Current State

| Milestone | Status | Verification |
|-----------|--------|--------------|
| 1. Scaffolding | ✅ done | `ls mcps/bitwarden` |
| 2. Client Implementation | ✅ done | `npm test` → 13 pass |
| 3. MCP Server | 🟡 review | `npm run build` → pass |
| 4. Integration | ⬜ todo | Live test with mcp-cli |

## Quick Start

```bash
cd /Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-feature-cloudflare-dns/mcps/bitwarden
npm test        # 13 tests should pass
npm run build   # Should succeed
```

Check Archon for tasks:
```
find_tasks(project_id="1f1b0204-a804-4266-a451-4d37d0cd25e0")
```

Full spec is in Archon:
```
find_documents(project_id="1f1b0204-a804-4266-a451-4d37d0cd25e0")
```

## Next Task (Milestone 4)

Live integration test:
- Configure agent to use the Bitwarden MCP
- Test with `mcp-cli` or real invocation
- Verify: `bitwarden_get_secret` returns correct value

## Key Files

| File | Purpose |
|------|---------|
| `src/bitwarden_client.ts` | Sacred core - all bw access here |
| `src/cli.ts` | CLI for wrapper.sh scripts |
| `src/index.ts` | MCP server (DONE - exposes tools) |
| `src/__tests__/bitwarden_client.test.ts` | 13 unit tests |
| `skill.json` | Tool definitions for agents |

## After This MCP is Done

Refactor `mcps/cloudflare-dns/wrapper.sh` to use `bitwarden-mcp` CLI instead of raw bw + jq.
