# Standard Skill Specification

This document defines the "Golden Set" of files and directory structure required for every new MCP skill in this monorepo.

## 1. Directory Structure

Every new skill MUST have two distinct locations:

1.  **Management & Handoffs**: `handoffs/<skill-name>/`
    - Contains project management, status tracking, and context for agents.
2.  **Implementation**: `mcps/<skill-name>/`
    - Contains the actual source code and configuration for the MCP server.

### Complete Tree
```text
monorepo/
├── handoffs/
│   └── <skill-name>/
│       ├── feature_list.json       # REQUIRED: Truth source for features & status
│       ├── progress.txt            # REQUIRED: Chronological work log
│       ├── RESUME.md               # REQUIRED: High-level context & next actions
│       └── LESSONS_LEARNED.md      # REQUIRED: Accumulated knowledge & pitfalls
├── mcps/
│   └── <skill-name>/
│       ├── src/
│       │   └── index.ts            # Entry point
│       ├── package.json
│       ├── tsconfig.json
│       └── README.md               # User-facing documentation
```

## 2. File Templates

### A. Management Files (`handoffs/<skill-name>/`)

#### 1. `feature_list.json`
The single source of truth for what needs to be done and what is done.
```json
[
  {
    "milestone": 1,
    "category": "scaffolding",
    "description": "Project Scaffolding",
    "deliverables": ["mcps/<skill-name>/package.json"],
    "passes": false,
    "verified_at": null
  }
]
```

#### 2. `progress.txt`
A chronological log of actions taken by agents.
```text
# Progress Log: <skill-name>

## Session [YYYY-MM-DD]
- [INIT] Scaffolding created.
```

#### 3. `RESUME.md`
Standard instruction file for the next agent.
```markdown
# 🚀 Resume Instructions: <skill-name>

**Status:** 🟡 STARTING

## Immediate Tasks
1. Review feature_list.json
2. ...
```

#### 4. `LESSONS_LEARNED.md`
Capture pitfalls to avoid repeating mistakes.
```markdown
# 🧠 Lessons Learned: <skill-name>

## Known Pitfalls
- [ ] Add new items here
```

### B. Implementation Files (`mcps/<skill-name>/`)

#### 1. `package.json`
Standard Node.js/MCP configuration.
```json
{
  "name": "mcp-<skill-name>",
  "version": "0.1.0",
  "type": "module",
  "bin": {
    "mcp-<skill-name>": "./build/index.js"
  },
  "scripts": {
    "build": "tsc && chmod +x build/index.js",
    "start": "node build/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "latest",
    "zod": "^3.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

#### 2. `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

#### 3. `.gitignore`
```text
node_modules/
build/
.env
.DS_Store
```
