# Session Retrospective & Lessons Learned

## Session: 2025-12-18 (Cloudflare DNS Implementation)

### 1. The "Phantom Scaffolding" Trap
**Observation:** The handoff documentation (`claude-progress.txt`) explicitly stated that Milestone 1 was "COMPLETE" and listed files like `package.json` and `tsconfig.json` as created.
**Reality:** These files did not exist in the directory.
**Lesson:** **Trust but Verify.** Never trust the handoff document blindly. Always verify file existence (`ls -R`) before assuming the environment is ready. Handoffs may represent "intent" rather than "disk state" if the previous agent failed to commit or save properly.

### 2. Aggressive Gitignore Blocking
**Observation:** The project's `.gitignore` is set to "deny by default" for many file types. It effectively blocked access to standard Node.js config files (`package.json`) and some handoff artifacts (`feature_list.json`).
**Impact:** `read_file` and `write_to_file` tools failed unexpectedly.
**Fix:** We had to explicitly update `.gitignore` to allow these specific files:
```gitignore
!**/package.json
!**/tsconfig.json
```
**Lesson:** Check `.gitignore` immediately when adding new infrastructure files. If a file "should be there" or "should be writeable" but isn't, `.gitignore` is the prime suspect in this monorepo.

### 3. Atomic Execution & Evidence
**Observation:** The requirement for "Atomic Execution" (stopping after every milestone to prove success) proved valuable. Because we stopped to verify Milestone 2, we caught the missing dependencies from Milestone 1 immediately, rather than discovering them deep in integration testing.
**Lesson:** The step-by-step verification protocol works. It forces us to stabilize the foundation to ensure it is solid before building higher.
