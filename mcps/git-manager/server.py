#!/usr/bin/env python3
"""
GIT_MANAGER - Worktree-centric Git Management MCP

Tools for managing git worktrees, feature branches, and release workflow.
Designed for a main/dev/feature branch strategy with sibling worktrees.

Directory Layout Expected:
    mcp-skills-hub-monorepo/           <- REPO_ROOT (main branch)
    ├── mcp-skills-hub-dev/            <- dev worktree
    ├── mcp-skills-hub-feature-X/      <- feature worktrees
    └── ...

Environment Variables:
    GIT_MANAGER_REPO_ROOT  - Override auto-detected repo root path
    GIT_MANAGER_TIMEOUT    - Git command timeout in seconds (default: 60)
    GIT_MANAGER_LOG_LEVEL  - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field, field_validator

# ============== LOGGING SETUP ==============

LOG_LEVEL = os.environ.get("GIT_MANAGER_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("git_manager")

# Initialize server
SKILL_NAME = os.environ.get("MCP_SKILL_NAME", "git_manager")
server = Server(SKILL_NAME)

# ============== PATH RESOLUTION ==============
# Can be overridden via GIT_MANAGER_REPO_ROOT environment variable

SCRIPT_DIR = Path(__file__).resolve().parent
MCPS_DIR = SCRIPT_DIR.parent
DEV_WORKTREE = MCPS_DIR.parent  # mcp-skills-hub-dev

# Allow override via environment variable for flexibility
_env_repo_root = os.environ.get("GIT_MANAGER_REPO_ROOT")
if _env_repo_root:
    REPO_ROOT = Path(_env_repo_root).resolve()
    logger.info(f"Using REPO_ROOT from environment: {REPO_ROOT}")
else:
    REPO_ROOT = DEV_WORKTREE.parent  # main worktree (mcp-skills-hub-monorepo)
    logger.debug(f"Auto-detected REPO_ROOT: {REPO_ROOT}")

# Configurable timeout
DEFAULT_TIMEOUT = int(os.environ.get("GIT_MANAGER_TIMEOUT", "60"))


# ============== HELPER FUNCTIONS ==============

def run_git(args: List[str], cwd: Path = None, timeout: int = None) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    cmd = ["git"] + args
    logger.debug(f"Running: {' '.join(cmd)} in {cwd or REPO_ROOT}")
    result = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        logger.warning(f"Git command failed: {' '.join(cmd)} -> {result.stderr.strip()}")
    return result

def format_result(proc: subprocess.CompletedProcess) -> str:
    """Format command result for output."""
    parts = []
    if proc.stdout.strip():
        parts.append(proc.stdout.strip())
    if proc.stderr.strip():
        parts.append(f"stderr: {proc.stderr.strip()}")
    if proc.returncode != 0:
        parts.append(f"exit code: {proc.returncode}")
    return "\n".join(parts) if parts else "(no output)"

def get_current_branch(cwd: Path = None) -> str:
    """Get current branch name."""
    result = run_git(["branch", "--show-current"], cwd)
    return result.stdout.strip()

def branch_exists(branch: str, cwd: Path = None) -> bool:
    """Check if a branch exists locally."""
    result = run_git(["show-ref", "--verify", f"refs/heads/{branch}"], cwd)
    return result.returncode == 0

def prune_worktrees() -> None:
    """Prune stale worktree references to prevent git errors."""
    logger.debug("Pruning stale worktree references...")
    run_git(["worktree", "prune"])


# ============== ARGUMENT MODELS ==============

class EmptyArgs(BaseModel):
    """No arguments required."""
    pass

class FeatureArgs(BaseModel):
    """Arguments for feature operations."""
    feature: str = Field(description="Feature name/slug (e.g., 'add-logging', 'fix-bug-123')")
    
    @field_validator("feature")
    @classmethod
    def validate_feature(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("feature cannot be empty")
        v = v.strip()
        if v.startswith("-"):
            raise ValueError("feature cannot start with '-' (e.g. --help)")
        if any(c in v for c in " \t\n/\\"):
            raise ValueError("feature cannot contain spaces or path separators")
        return v

class MergeFeatureArgs(FeatureArgs):
    """Arguments for merging a feature."""
    push: bool = Field(default=False, description="Push to origin after merge")
    delete_branch: bool = Field(default=False, description="Delete feature branch after merge")

class ReleaseMergeArgs(BaseModel):
    """Arguments for release merge (dev -> main)."""
    push: bool = Field(default=False, description="Push main to origin after merge")
    ff_only: bool = Field(default=True, description="Use --ff-only (fail if not fast-forward)")

class TagArgs(BaseModel):
    """Arguments for creating a release tag."""
    version: str = Field(description="Version tag (e.g., 'v1.0.0', 'v2.1.3')")
    message: Optional[str] = Field(default=None, description="Tag message (defaults to 'Release {version}')")
    push: bool = Field(default=True, description="Push tag to origin")

class StatusArgs(BaseModel):
    """Arguments for status check."""
    worktree: Optional[str] = Field(default=None, description="Specific worktree to check (default: current)")


class HelpArgs(BaseModel):
    """Arguments for help."""
    tool_name: Optional[str] = Field(default=None, description="Specific tool to get help for")


class CommitPushArgs(BaseModel):
    """Arguments for add, commit, and push."""
    message: Optional[str] = Field(default=None, description="Commit message (optional, auto-generated if empty)")
    worktree: Optional[str] = Field(default=None, description="Specific worktree to act on (default: dev)")
    push: bool = Field(default=True, description="Push to origin after commit")


# ============== TOOL DEFINITIONS ==============

TOOLS = {
    "list_worktrees": {
        "description": "List all git worktrees with their branches and paths.",
        "schema": EmptyArgs,
    },
    "get_status": {
        "description": "Get git status (modified files, staged changes, branch info) for a worktree.",
        "schema": StatusArgs,
    },
    "create_feature": {
        "description": "Create a new feature branch and worktree from dev. Creates mcp-skills-hub-feature-<name> directory.",
        "schema": FeatureArgs,
    },
    "delete_feature": {
        "description": "Delete a feature worktree and optionally its branch.",
        "schema": FeatureArgs,
    },
    "merge_feature": {
        "description": "Merge a feature branch into dev. Optionally push and/or delete the feature branch.",
        "schema": MergeFeatureArgs,
    },
    "release_merge": {
        "description": "Merge dev into main for release. Use ff_only=true (default) for clean releases.",
        "schema": ReleaseMergeArgs,
    },
    "tag_release": {
        "description": "Create an annotated version tag on main and push it.",
        "schema": TagArgs,
    },
    "sync_env": {
        "description": "Copy .env file from dev worktree to all feature worktrees.",
        "schema": EmptyArgs,
    },
    "pull_all": {
        "description": "Pull latest changes in all worktrees (main, dev, features).",
        "schema": EmptyArgs,
    },
    "git_add_commit_push": {
        "description": "Stage all changes (git add .), commit, and optionally push.",
        "schema": CommitPushArgs,
    },
    "get_help": {
        "description": "Get usage help for a specific tool or list all tools.",
        "schema": HelpArgs,
    },
}

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name=name,
            description=info["description"],
            inputSchema=info["schema"].model_json_schema(),
        )
        for name, info in TOOLS.items()
    ]


# ============== TOOL ROUTER ==============

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "list_worktrees":
            result = do_list_worktrees()
        elif name == "get_status":
            args = StatusArgs(**arguments)
            result = do_get_status(args.worktree)
        elif name == "create_feature":
            args = FeatureArgs(**arguments)
            result = do_create_feature(args.feature)
        elif name == "delete_feature":
            args = FeatureArgs(**arguments)
            result = do_delete_feature(args.feature)
        elif name == "merge_feature":
            args = MergeFeatureArgs(**arguments)
            result = do_merge_feature(args.feature, args.push, args.delete_branch)
        elif name == "release_merge":
            args = ReleaseMergeArgs(**arguments)
            result = do_release_merge(args.push, args.ff_only)
        elif name == "tag_release":
            args = TagArgs(**arguments)
            result = do_tag_release(args.version, args.message, args.push)
        elif name == "sync_env":
            result = do_sync_env()
        elif name == "pull_all":
            result = do_pull_all()
        elif name == "git_add_commit_push":
            args = CommitPushArgs(**arguments)
            result = do_git_add_commit_push(args.message, args.worktree, args.push)
        elif name == "get_help":
            args = HelpArgs(**arguments)
            result = do_get_help(args.tool_name)
        else:
            result = f"Unknown tool: {name}"
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============== IMPLEMENTATION FUNCTIONS ==============

def do_list_worktrees() -> str:
    """List all worktrees."""
    # Prune stale references first for accurate listing
    prune_worktrees()
    
    output = ["=== GIT WORKTREES ===\n"]
    
    # Get worktree list
    wt_result = run_git(["worktree", "list", "--porcelain"])
    if wt_result.returncode != 0:
        return f"Error listing worktrees: {format_result(wt_result)}"
    
    # Parse porcelain output
    worktrees = []
    current_wt = {}
    for line in wt_result.stdout.split("\n"):
        if line.startswith("worktree "):
            if current_wt:
                worktrees.append(current_wt)
            current_wt = {"path": line[9:]}
        elif line.startswith("HEAD "):
            current_wt["head"] = line[5:8]  # Short SHA
        elif line.startswith("branch "):
            current_wt["branch"] = line[7:].replace("refs/heads/", "")
        elif line == "bare":
            current_wt["bare"] = True
    if current_wt:
        worktrees.append(current_wt)
    
    # Format output
    for wt in worktrees:
        path = Path(wt.get("path", ""))
        branch = wt.get("branch", "detached")
        name = path.name
        output.append(f"📁 {name}")
        output.append(f"   Branch: {branch}")
        output.append(f"   Path: {path}\n")
    
    # Also show branches
    output.append("\n=== ALL BRANCHES ===")
    branches = run_git(["branch", "-a", "-v", "--no-abbrev"])
    output.append(branches.stdout[:500] if branches.stdout else "(no branches)")
    
    return "\n".join(output)


def do_get_status(worktree: Optional[str] = None) -> str:
    """Get git status for a worktree."""
    if worktree:
        wt_path = REPO_ROOT / f"mcp-skills-hub-{worktree}"
        if not wt_path.exists():
            wt_path = REPO_ROOT / worktree
        if not wt_path.exists():
            return f"Worktree not found: {worktree}"
    else:
        wt_path = DEV_WORKTREE
    
    output = [f"=== STATUS: {wt_path.name} ===\n"]
    
    # Current branch
    branch = get_current_branch(wt_path)
    output.append(f"Branch: {branch}")
    
    # Status
    status = run_git(["status", "--short"], wt_path)
    if status.stdout.strip():
        output.append(f"\nChanges:\n{status.stdout}")
    else:
        output.append("\n✅ Working tree clean")
    
    # Ahead/behind
    upstream = run_git(["rev-list", "--left-right", "--count", f"{branch}...origin/{branch}"], wt_path)
    if upstream.returncode == 0 and upstream.stdout.strip():
        parts = upstream.stdout.strip().split()
        if len(parts) == 2:
            ahead, behind = int(parts[0]), int(parts[1])
            if ahead > 0:
                output.append(f"⬆️  {ahead} commit(s) ahead of origin")
            if behind > 0:
                output.append(f"⬇️  {behind} commit(s) behind origin")
    
    return "\n".join(output)


def do_create_feature(feature: str) -> str:
    """Create a new feature branch and worktree."""
    branch_name = f"feature/{feature}"
    worktree_path = REPO_ROOT / f"mcp-skills-hub-feature-{feature}"
    
    output = [f"=== CREATING FEATURE: {feature} ===\n"]
    
    # Check if already exists
    if worktree_path.exists():
        return f"❌ Worktree already exists: {worktree_path}"
    if branch_exists(branch_name):
        return f"❌ Branch already exists: {branch_name}"
    
    # Make sure dev is up to date
    output.append("Updating dev branch...")
    run_git(["fetch", "origin", "dev"], DEV_WORKTREE)
    
    # Create worktree with new branch from dev
    output.append(f"Creating worktree at {worktree_path}...")
    result = run_git(["worktree", "add", str(worktree_path), "-b", branch_name, "dev"])
    if result.returncode != 0:
        return f"❌ Failed to create worktree:\n{format_result(result)}"
    
    output.append(format_result(result))
    
    # Copy .env if exists
    env_src = DEV_WORKTREE / ".env"
    if env_src.exists():
        shutil.copy(env_src, worktree_path / ".env")
        output.append("✅ Copied .env from dev")
    
    output.append(f"\n✅ Feature created!")
    output.append(f"   Branch: {branch_name}")
    output.append(f"   Path: {worktree_path}")
    output.append(f"\n💡 cd {worktree_path}")
    
    return "\n".join(output)


def do_delete_feature(feature: str) -> str:
    """Delete a feature worktree and branch."""
    branch_name = f"feature/{feature}"
    worktree_path = REPO_ROOT / f"mcp-skills-hub-feature-{feature}"
    
    output = [f"=== DELETING FEATURE: {feature} ===\n"]
    
    # Remove worktree
    if worktree_path.exists():
        result = run_git(["worktree", "remove", str(worktree_path), "--force"])
        if result.returncode == 0:
            output.append(f"✅ Removed worktree: {worktree_path}")
        else:
            output.append(f"⚠️ Worktree removal: {format_result(result)}")
    else:
        output.append(f"ℹ️  Worktree not found: {worktree_path}")
    
    # Delete branch
    if branch_exists(branch_name):
        result = run_git(["branch", "-D", branch_name])
        if result.returncode == 0:
            output.append(f"✅ Deleted branch: {branch_name}")
        else:
            output.append(f"⚠️ Branch deletion: {format_result(result)}")
    else:
        output.append(f"ℹ️  Branch not found: {branch_name}")
    
    # Prune worktree list
    run_git(["worktree", "prune"])
    
    return "\n".join(output)


def do_merge_feature(feature: str, push: bool, delete_branch: bool) -> str:
    """Merge a feature branch into dev."""
    branch_name = f"feature/{feature}"
    
    output = [f"=== MERGING FEATURE: {feature} → dev ===\n"]
    
    # Check branch exists
    if not branch_exists(branch_name):
        return f"❌ Branch not found: {branch_name}"
    
    # Switch to dev and update
    output.append("Switching to dev and pulling...")
    run_git(["checkout", "dev"], DEV_WORKTREE)
    run_git(["pull", "origin", "dev"], DEV_WORKTREE)
    
    # Merge feature
    output.append(f"Merging {branch_name}...")
    result = run_git(["merge", branch_name, "--no-ff", "-m", f"Merge {branch_name} into dev"], DEV_WORKTREE)
    output.append(format_result(result))
    
    if result.returncode != 0:
        output.append("\n❌ Merge failed - resolve conflicts manually")
        return "\n".join(output)
    
    # Push if requested
    if push:
        output.append("\nPushing dev to origin...")
        push_result = run_git(["push", "origin", "dev"], DEV_WORKTREE)
        output.append(format_result(push_result))
    
    # Delete branch if requested
    if delete_branch:
        output.append(f"\nDeleting {branch_name}...")
        do_delete_feature(feature)
    
    output.append("\n✅ Merge complete!")
    return "\n".join(output)


def do_release_merge(push: bool, ff_only: bool) -> str:
    """Merge dev into main for release."""
    output = ["=== RELEASE MERGE: dev → main ===\n"]
    
    # Prune stale worktree references first
    prune_worktrees()
    
    # Define main worktree path
    MAIN_WORKTREE = REPO_ROOT / "mcp-skills-hub-main"
    
    # Verify main worktree exists
    if not MAIN_WORKTREE.exists():
        return f"❌ Main worktree not found at {MAIN_WORKTREE}"
    
    # Update main
    output.append("Fetching and updating main...")
    run_git(["fetch", "origin", "main:main"], MAIN_WORKTREE)
    run_git(["checkout", "main"], MAIN_WORKTREE)
    run_git(["pull", "origin", "main"], MAIN_WORKTREE)
    
    # Update dev reference
    run_git(["fetch", "origin", "dev:dev"], MAIN_WORKTREE)
    
    # Merge dev into main
    merge_cmd = ["merge", "dev"]
    if ff_only:
        merge_cmd.append("--ff-only")
    else:
        merge_cmd.extend(["--no-ff", "-m", "Merge dev into main for release"])
    
    output.append("Merging dev into main...")
    result = run_git(merge_cmd, MAIN_WORKTREE)
    output.append(format_result(result))
    
    if result.returncode != 0:
        output.append("\n❌ Merge failed")
        if ff_only:
            output.append("💡 Try with ff_only=false if branches have diverged")
        return "\n".join(output)
    
    # Push if requested
    if push:
        output.append("\nPushing main to origin...")
        push_result = run_git(["push", "origin", "main"], MAIN_WORKTREE)
        output.append(format_result(push_result))
    
    output.append("\n✅ Release merge complete!")
    return "\n".join(output)


def do_tag_release(version: str, message: Optional[str], push: bool) -> str:
    """Create a release tag on main."""
    output = [f"=== TAGGING RELEASE: {version} ===\n"]
    
    # Prune stale worktree references first
    prune_worktrees()
    
    # Define main worktree path
    MAIN_WORKTREE = REPO_ROOT / "mcp-skills-hub-main"
    
    # Verify main worktree exists
    if not MAIN_WORKTREE.exists():
        return f"❌ Main worktree not found at {MAIN_WORKTREE}"
    
    if not message:
        message = f"Release {version}"
    
    # Make sure we're on main
    run_git(["checkout", "main"], MAIN_WORKTREE)
    
    # Create annotated tag
    output.append(f"Creating tag {version}...")
    result = run_git(["tag", "-a", version, "-m", message], MAIN_WORKTREE)
    
    if result.returncode != 0:
        return f"❌ Failed to create tag:\n{format_result(result)}"
    
    output.append(f"✅ Created tag: {version}")
    
    # Push tag if requested
    if push:
        output.append(f"\nPushing tag to origin...")
        push_result = run_git(["push", "origin", version], MAIN_WORKTREE)
        output.append(format_result(push_result))
    
    return "\n".join(output)


def do_sync_env() -> str:
    """Sync .env from dev to all feature worktrees."""
    output = ["=== SYNCING .env FILES ===\n"]
    
    env_src = DEV_WORKTREE / ".env"
    if not env_src.exists():
        return "❌ No .env found in dev worktree"
    
    count = 0
    for item in REPO_ROOT.iterdir():
        if item.is_dir() and item.name.startswith("mcp-skills-hub-feature-"):
            shutil.copy(env_src, item / ".env")
            output.append(f"✅ Copied to {item.name}")
            count += 1
    
    if count == 0:
        output.append("ℹ️  No feature worktrees found")
    else:
        output.append(f"\n✅ Synced .env to {count} feature worktree(s)")
    
    return "\n".join(output)


def do_pull_all() -> str:
    """Pull latest changes in all worktrees."""
    output = ["=== PULLING ALL WORKTREES ===\n"]
    
    # Get all worktrees
    wt_result = run_git(["worktree", "list", "--porcelain"])
    
    worktree_paths = []
    for line in wt_result.stdout.split("\n"):
        if line.startswith("worktree "):
            worktree_paths.append(Path(line[9:]))
    
    for wt_path in worktree_paths:
        if not wt_path.exists():
            continue
        
        branch = get_current_branch(wt_path)
        output.append(f"📁 {wt_path.name} ({branch})")
        
        # Pull
        result = run_git(["pull", "origin", branch], wt_path)
        if result.returncode == 0:
            if "Already up to date" in result.stdout:
                output.append("   ✅ Already up to date\n")
            else:
                output.append(f"   ✅ Updated\n")
        else:
            output.append(f"   ⚠️ {result.stderr.strip()}\n")
    
    return "\n".join(output)


def do_git_add_commit_push(message: Optional[str], worktree: Optional[str], push: bool) -> str:
    """Stage, commit, and push changes in a worktree."""
    # Determine worktree path
    if worktree:
        wt_path = REPO_ROOT / f"mcp-skills-hub-{worktree}"
        if not wt_path.exists():
            wt_path = REPO_ROOT / worktree
        if not wt_path.exists():
            return f"❌ Worktree not found: {worktree}"
    else:
        wt_path = DEV_WORKTREE

    output = [f"=== COMMIT & PUSH: {wt_path.name} ===\n"]

    # Git Add
    output.append("Staging changes (git add .)...")
    add_res = run_git(["add", "."], wt_path)
    if add_res.returncode != 0:
        return f"❌ Git add failed:\n{format_result(add_res)}"

    # Check validity (status)
    status = run_git(["status", "--porcelain"], wt_path)
    if not status.stdout.strip():
        return "ℹ️  Nothing to commit (working tree clean)"

    # Auto-generate message if missing
    if not message:
        lines = status.stdout.strip().splitlines()
        files = [l.strip().split()[-1] for l in lines]
        file_summary = ", ".join(files[:3])
        if len(files) > 3:
            file_summary += f" and {len(files)-3} others"
        message = f"wip: Update {file_summary}"

    # Git Commit
    output.append(f"Committing with message: '{message}'...")
    commit_res = run_git(["commit", "-m", message], wt_path)
    output.append(format_result(commit_res))
    
    if commit_res.returncode != 0:
        return f"\n❌ Commit failed:\n{format_result(commit_res)}"

    # Git Push
    if push:
        branch = get_current_branch(wt_path)
        output.append(f"\nPushing {branch} to origin...")
        push_res = run_git(["push", "origin", branch], wt_path)
        output.append(format_result(push_res))
        if push_res.returncode != 0:
             output.append("\n⚠️ Push failed (check upstream/conflicts)")
        else:
             output.append("\n✅ Pushed successfully")

    return "\n".join(output)


def do_get_help(tool_name: Optional[str] = None) -> str:
    """Get help for tools."""
    if tool_name:
        if tool_name not in TOOLS:
            return f"❌ Unknown tool: {tool_name}"
        
        info = TOOLS[tool_name]
        schema = info["schema"]
        
        output = [f"=== HELP: {tool_name} ==="]
        output.append(info["description"])
        output.append("\nArguments:")
        
        props = schema.model_json_schema().get("properties", {})
        required = schema.model_json_schema().get("required", [])
        
        for name, prop in props.items():
            req_mark = "*" if name in required else ""
            desc = prop.get("description", "(no description)")
            output.append(f"- {name}{req_mark}: {desc}")
            
        return "\n".join(output)
            
    # List all
    output = ["=== AVAILABLE TOOLS ==="]
    for name, info in TOOLS.items():
        output.append(f"- {name}: {info['description']}")
    
    output.append("\n💡 Use get_help(tool_name='...') for details.")
    return "\n".join(output)


# ============== MAIN ==============

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
