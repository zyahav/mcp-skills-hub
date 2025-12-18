# 🚀 Resume Instructions: bitwarden

**Status:** ✅ COMPLETE
**Archon Project ID:** `1f1b0204-a804-4266-a451-4d37d0cd25e0`

## Context (Why This Exists)

We built a **standalone Bitwarden MCP** to replace ad-hoc `bw + jq` parsing in wrapper.sh scripts.

**Before:**
```bash
ITEM_JSON=$(bw get item "Cloudflare DNS Manager")
export CLOUDFLARE_API_TOKEN=$(echo "$ITEM_JSON" | jq -r '.fields[] | select(.name=="CLOUDFLARE_API_TOKEN") | .value')
```

**After:**
```bash
export CLOUDFLARE_API_TOKEN=$(bitwarden-mcp get-secret "Cloudflare DNS Manager" "CLOUDFLARE_API_TOKEN")
```

## Final State

| Milestone | Status | Verification |
|-----------|--------|--------------|
| 1. Scaffolding | ✅ done | `ls mcps/bitwarden` |
| 2. Client Implementation | ✅ done | `npm test` → 13 pass |
| 3. MCP Server | ✅ done | `npm run build` → pass |
| 4. Integration | ✅ done | `./test-live.sh` → pass |

## What's Ready to Use

**CLI (for wrapper.sh):**
```bash
bitwarden-mcp get-secret "Item Name" "FIELD_NAME"
bitwarden-mcp get-notes "Item Name"
```

**MCP Tools (for agents):**
- `bitwarden_get_secret(item, field)`
- `bitwarden_get_notes(item)`

## Next Step: Refactor Cloudflare DNS

Update `mcps/cloudflare-dns/wrapper.sh` to use the new CLI:
```bash
export CLOUDFLARE_API_TOKEN=$(bitwarden-mcp get-secret "Cloudflare DNS Manager" "CLOUDFLARE_API_TOKEN")
export CLOUDFLARE_ZONE_ID=$(bitwarden-mcp get-secret "Cloudflare DNS Manager" "CLOUDFLARE_ZONE_ID")
```

## Key Files

| File | Purpose |
|------|---------|
| `src/bitwarden_client.ts` | Sacred core - all rules enforced |
| `src/cli.ts` | CLI for wrapper.sh scripts |
| `src/index.ts` | MCP server |
| `wrapper.sh` | MCP startup script |
| `test-live.sh` | Integration test |
