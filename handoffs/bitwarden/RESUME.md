# 🚀 Resume Instructions: bitwarden

**Status:** 🟡 IN PROGRESS (Milestone 2 in review)
**Archon Project ID:** `1f1b0204-a804-4266-a451-4d37d0cd25e0`

## Current State

### Completed
- ✅ Milestone 1: Scaffolding (done)
- ✅ Milestone 2: Client Implementation (in review)
  - `bitwarden_client.ts` - core with R1-R8
  - `cli.ts` - CLI interface
  - 13 tests passing

### Next Task
**Milestone 3: MCP Server Implementation**
- Update `src/index.ts` to expose real tools
- `bitwarden_get_secret(item, field)`
- `bitwarden_get_notes(item)`
- Verify: `npm run build`

## Quick Start for Next Session

```bash
cd mcps/bitwarden
npm test        # Should show 13 passing
npm run build   # Should succeed
```

Then check Archon:
```
find_tasks(project_id="1f1b0204-a804-4266-a451-4d37d0cd25e0")
```

## Architecture (SETTLED - Don't re-discuss)

See LESSONS_LEARNED.md. Summary:
- One core (`bitwarden_client.ts`)
- Two interfaces: CLI + MCP
- Wrappers use CLI at startup
- Agents use MCP tools
