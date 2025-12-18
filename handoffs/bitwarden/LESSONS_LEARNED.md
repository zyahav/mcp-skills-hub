# 🧠 Lessons Learned: bitwarden

## Architecture Decision (CRITICAL)

**The correct architecture is: One core + Two interfaces**

```
bitwarden_client.ts (sacred core - ALL rules enforced here)
├── CLI interface (bitwarden-mcp get-secret) → for wrapper.sh scripts
└── MCP interface (bitwarden_get_secret)     → for agents
```

**Why NOT MCP-to-MCP:**
- MCP runs on stdio, not a service mesh
- Lifecycle complexity
- Protocol wasn't designed for it

**Why NOT agents passing secrets as arguments:**
- Secrets leak into logs, context windows, traces

**Why NOT raw `bw + jq` in every wrapper:**
- Duplicated logic, inconsistent safety, impossible to audit

## Testing Patterns

1. **Mock child_process.execFile** - vitest mocks work well
2. **Sequential mock setup** - Each bw call needs its own mock (status → list → get)
3. **Verify error codes and metadata** - Not just that errors are thrown
4. **NO live vault in tests** - All mocked

## Implementation Notes

1. **CLI output is raw** - `process.stdout.write(secret)` with no newline, for shell capture
2. **Forbidden commands blocked** - unlock, login, logout, lock
3. **Error messages redacted** - BW_SESSION token stripped from errors
4. **Modern bw CLI (2024+)** - Returns JSON by default, no `--format json` flag needed
5. **bw sync required** - After creating/editing items in Bitwarden, run `bw sync` before CLI access

## Files Created

| File | Purpose |
|------|---------|
| `src/bitwarden_client.ts` | Sacred core - R1-R8 enforced |
| `src/cli.ts` | CLI for wrapper.sh usage |
| `src/__tests__/bitwarden_client.test.ts` | 13 unit tests |
| `vitest.config.ts` | Test config |

## Next Session Shortcut

Don't re-discuss architecture. It's settled:
- Secrets resolved at startup via CLI
- Same core logic everywhere
- MCPs never call Bitwarden at runtime
