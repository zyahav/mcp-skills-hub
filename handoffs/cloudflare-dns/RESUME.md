# 🚀 Resume Instructions: Cloudflare DNS Skill

**Role:** You are the **Execution Agent** picking up an active project.
**Goal:** Continue implementing the `mcp-cloudflare-dns` skill.

## 1. Orient Yourself
Run the initialization script to inspect the environment and git status:
```bash
./handoffs/cloudflare-dns/init.sh
```

## 2. Load Context
Read these files to understand the project state, architecture, and constraints:
1.  **Status**: [claude-progress.txt](file://handoffs/cloudflare-dns/claude-progress.txt) (Read the latest session log)
2.  **Plan**: [feature_list.json](file://handoffs/cloudflare-dns/feature_list.json) (Check what is passed/failing)
3.  **Rules**: [cloudflare-dns-execution.xml](file://handoffs/cloudflare-dns/cloudflare-dns-execution.xml) (Strict "Atomic Execution" protocol)
4.  **Hazards**: [LESSONS_LEARNED.md](file://handoffs/cloudflare-dns/LESSONS_LEARNED.md) (Avoid known traps)

## 3. Current State
- **Milestone 1 (Scaffolding)**: ✅ Complete
- **Milestone 2 (Safety/Client)**: ✅ Complete (Verified 2025-12-18)
- **Current Objective**: **Milestone 3 (MCP Server & Bitwarden Wrapper)**

## 4. Immediate Tasks
1.  Implement `src/index.ts` (MCP Server with `upsert_dns_record` and `delete_dns_record`).
2.  Implement `wrapper.sh` (Bitwarden secrets integration).
3.  Build and verify.

## 5. Execution Protocol
> [!IMPORTANT]
> **Atomic Execution**: You must STOP after completing Milestone 3 and provide proof of verification (build success, file existence) before proceeding to Milestone 4. Do not attempt to do both in one pass.
