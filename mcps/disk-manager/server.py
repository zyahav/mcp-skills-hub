#!/usr/bin/env python3
"""
DISK_MANAGER - Complete Disk Management Skill
"""
import asyncio
import subprocess
import os
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

# Configuration
DISK_MONITOR_DIR = Path.home() / ".disk_monitor"
SKILL_NAME = os.environ.get("MCP_SKILL_NAME", "disk_manager")
server = Server(SKILL_NAME)

# Thresholds
THRESHOLD_WARNING = 75
THRESHOLD_EMERGENCY = 85
THRESHOLD_CRITICAL = 90


# ============== ARGUMENT MODELS ==============

class EmptyArgs(BaseModel):
    """No arguments needed"""
    pass

class CleanupArgs(BaseModel):
    """Arguments for execute_cleanup"""
    procedure: str = Field(description="Cleanup procedure: npm_cache, dev_caches, homebrew, system_caches, pnpm_store, vscode_caches, google_caches")
    confirm: bool = Field(default=False, description="Set to true to confirm execution. REQUIRED for any cleanup.")

class AppApproveArgs(BaseModel):
    """Arguments for approve_app"""
    app_name: str = Field(description="Name of the application to approve")

class WorkflowArgs(BaseModel):
    """Arguments for get_emergency_workflow"""
    current_percent: Optional[int] = Field(default=None, description="Current disk usage %. If not provided, will be detected automatically.")

class ProcedureArgs(BaseModel):
    """Arguments for get_procedures"""
    category: Optional[str] = Field(default=None, description="Filter by category: npm, dev_caches, system, homebrew, library. Leave empty for all.")

class HistoryArgs(BaseModel):
    """Arguments for get_history"""
    days: int = Field(default=7, description="Number of days of history to return")


# ============== CLEANUP PROCEDURES DATA ==============

CLEANUP_PROCEDURES = {
    "npm_cache": {
        "name": "NPM Cache Cleanup",
        "category": "npm",
        "command": "npm cache clean --force",
        "location": "~/.npm",
        "typical_space_gb": 6.0,
        "safety": "high",
        "description": "Clears npm package cache. Safe - npm rebuilds as needed."
    },
    "dev_caches": {
        "name": "Development Caches",
        "category": "dev_caches",
        "command": "rm -rf ~/.cache/puppeteer/* ~/.cache/uv/* ~/.cache/whisper/* ~/.cache/lm-studio ~/.cache/node/* ~/.nvm/.cache/*",
        "location": "~/.cache/",
        "typical_space_gb": 2.7,
        "safety": "high",
        "description": "Clears dev tool caches (Puppeteer, UV, Whisper, LM-Studio, Node). All regenerate automatically."
    },
    "homebrew": {
        "name": "Homebrew Cleanup",
        "category": "homebrew",
        "command": "brew cleanup",
        "location": "/opt/homebrew",
        "typical_space_gb": 0.8,
        "safety": "high",
        "description": "Removes old versions of installed formulae. Keeps current versions."
    },
    "system_caches": {
        "name": "System Caches",
        "category": "system",
        "command": "rm -rf ~/Library/Caches/*",
        "location": "~/Library/Caches/",
        "typical_space_gb": 3.5,
        "safety": "medium",
        "description": "Clears system and app caches. Apps rebuild as needed."
    },
    "pnpm_store": {
        "name": "pnpm Store Prune",
        "category": "npm",
        "command": "pnpm store prune",
        "location": "~/Library/pnpm/store",
        "typical_space_gb": 2.0,
        "safety": "high",
        "description": "Removes unreferenced packages from pnpm store."
    },
    "vscode_caches": {
        "name": "VS Code Caches",
        "category": "library",
        "command": 'rm -rf ~/Library/"Application Support"/Code/WebStorage ~/Library/"Application Support"/Code/"Service Worker" ~/Library/"Application Support"/Code/CachedExtensionVSIXs ~/Library/"Application Support"/Code/CachedData ~/Library/"Application Support"/Code/GPUCache ~/Library/"Application Support"/Code/logs',
        "location": "~/Library/Application Support/Code/",
        "typical_space_gb": 2.6,
        "safety": "high",
        "description": "Clears VS Code caches. Keeps User folder (extensions & settings)."
    },
    "google_caches": {
        "name": "Google Caches",
        "category": "library",
        "command": 'rm -rf ~/Library/Caches/Google ~/Library/"Application Support"/Google/DriveFS/*/content_cache ~/Library/"Application Support"/Google/DriveFS/*/thumbnails_cache',
        "location": "~/Library/Caches/Google, ~/Library/Application Support/Google/",
        "typical_space_gb": 1.5,
        "safety": "high",
        "description": "Clears Google Chrome and Drive caches."
    }
}


# ============== TOOL DESCRIPTIONS ==============

TOOL_DESCRIPTIONS = {
    "get_disk_status": "Get current disk usage, available space, and health status (normal/warning/emergency/critical).",
    "scan_junk": "Scan for cleanable files: caches, temp files, logs. Returns sizes and locations.",
    "get_procedures": "List available cleanup procedures with expected space savings and safety levels.",
    "get_emergency_workflow": "Get recommended cleanup sequence based on current disk usage percentage.",
    "execute_cleanup": "Execute a cleanup procedure. REQUIRES confirm=true. Always ask user permission first!",
    "get_app_status": "Show installed applications and their approval status (approved/pending).",
    "approve_app": "Approve a pending application by name.",
    "get_history": "Get disk usage history and trends over time."
}

# ============== TOOL LISTING ==============

@server.list_tools()
async def list_tools():
    return [
        Tool(name="get_disk_status", description=TOOL_DESCRIPTIONS["get_disk_status"], inputSchema=EmptyArgs.model_json_schema()),
        Tool(name="scan_junk", description=TOOL_DESCRIPTIONS["scan_junk"], inputSchema=EmptyArgs.model_json_schema()),
        Tool(name="get_procedures", description=TOOL_DESCRIPTIONS["get_procedures"], inputSchema=ProcedureArgs.model_json_schema()),
        Tool(name="get_emergency_workflow", description=TOOL_DESCRIPTIONS["get_emergency_workflow"], inputSchema=WorkflowArgs.model_json_schema()),
        Tool(name="execute_cleanup", description=TOOL_DESCRIPTIONS["execute_cleanup"], inputSchema=CleanupArgs.model_json_schema()),
        Tool(name="get_app_status", description=TOOL_DESCRIPTIONS["get_app_status"], inputSchema=EmptyArgs.model_json_schema()),
        Tool(name="approve_app", description=TOOL_DESCRIPTIONS["approve_app"], inputSchema=AppApproveArgs.model_json_schema()),
        Tool(name="get_history", description=TOOL_DESCRIPTIONS["get_history"], inputSchema=HistoryArgs.model_json_schema()),
    ]


# ============== TOOL ROUTER ==============

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "get_disk_status":
            result = do_get_disk_status()
        elif name == "scan_junk":
            result = do_scan_junk()
        elif name == "get_procedures":
            args = ProcedureArgs(**arguments)
            result = do_get_procedures(args.category)
        elif name == "get_emergency_workflow":
            args = WorkflowArgs(**arguments)
            result = do_get_emergency_workflow(args.current_percent)
        elif name == "execute_cleanup":
            args = CleanupArgs(**arguments)
            result = do_execute_cleanup(args.procedure, args.confirm)
        elif name == "get_app_status":
            result = do_get_app_status()
        elif name == "approve_app":
            args = AppApproveArgs(**arguments)
            result = do_approve_app(args.app_name)
        elif name == "get_history":
            args = HistoryArgs(**arguments)
            result = do_get_history(args.days)
        else:
            result = f"Unknown tool: {name}"
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============== IMPLEMENTATION FUNCTIONS ==============

def run_cmd(cmd: str, timeout: int = 30) -> str:
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {e}"

def get_disk_percent() -> int:
    """Get current disk usage percentage"""
    output = run_cmd("df -h / | tail -1 | awk '{print $5}' | tr -d '%'")
    try:
        return int(output)
    except:
        return 0

def get_status_level(percent: int) -> str:
    """Get status level based on percentage"""
    if percent >= THRESHOLD_CRITICAL:
        return "CRITICAL"
    elif percent >= THRESHOLD_EMERGENCY:
        return "EMERGENCY"
    elif percent >= THRESHOLD_WARNING:
        return "WARNING"
    return "NORMAL"

def do_get_disk_status() -> str:
    """Get current disk status"""
    df_output = run_cmd("df -h / | tail -1")
    parts = df_output.split()
    
    if len(parts) >= 5:
        total = parts[1]
        used = parts[2]
        available = parts[3]
        percent_str = parts[4].replace('%', '')
        try:
            percent = int(percent_str)
        except:
            percent = 0
    else:
        return f"Error parsing df output: {df_output}"
    
    status = get_status_level(percent)
    
    output = f"""=== DISK STATUS ===
Total:     {total}
Used:      {used} ({percent}%)
Available: {available}
Status:    {status}

Thresholds:
- Normal:    < {THRESHOLD_WARNING}%
- Warning:   {THRESHOLD_WARNING}-{THRESHOLD_EMERGENCY}%
- Emergency: {THRESHOLD_EMERGENCY}-{THRESHOLD_CRITICAL}%
- Critical:  > {THRESHOLD_CRITICAL}%
"""
    
    if status != "NORMAL":
        output += f"\n⚠️ ATTENTION: Disk is in {status} state. Consider running cleanup procedures."
    
    return output


def do_scan_junk() -> str:
    """Scan for cleanable junk files"""
    output = "=== JUNK SCAN RESULTS ===\n\n"
    
    # Check various cache locations
    locations = [
        ("NPM Cache", "~/.npm"),
        ("pnpm Store", "~/Library/pnpm/store"),
        ("Homebrew", "/opt/homebrew"),
        ("System Caches", "~/Library/Caches"),
        ("System Logs", "~/Library/Logs"),
        ("Puppeteer Cache", "~/.cache/puppeteer"),
        ("UV Cache", "~/.cache/uv"),
        ("Whisper Cache", "~/.cache/whisper"),
        ("VS Code Caches", '~/Library/"Application Support"/Code/CachedData'),
        ("Google Caches", "~/Library/Caches/Google"),
    ]
    
    total_mb = 0
    output += "📦 CACHE SIZES:\n"
    
    for name, path in locations:
        expanded = os.path.expanduser(path.replace('"', ''))
        if os.path.exists(expanded):
            size_output = run_cmd(f'du -sh "{expanded}" 2>/dev/null | cut -f1')
            if size_output and not size_output.startswith("Error"):
                output += f"  {name}: {size_output}\n"
                # Try to parse size for total
                try:
                    if 'G' in size_output:
                        total_mb += float(size_output.replace('G', '')) * 1024
                    elif 'M' in size_output:
                        total_mb += float(size_output.replace('M', ''))
                except:
                    pass
    
    output += f"\n📊 ESTIMATED CLEANABLE: ~{total_mb/1024:.1f} GB\n"
    output += "\n💡 Use get_procedures() to see cleanup options."
    output += "\n⚠️ Remember: execute_cleanup requires explicit permission!"
    
    return output

def do_get_procedures(category: Optional[str] = None) -> str:
    """Get available cleanup procedures"""
    output = "=== CLEANUP PROCEDURES ===\n\n"
    
    total_space = 0
    for proc_id, proc in CLEANUP_PROCEDURES.items():
        if category and proc["category"] != category:
            continue
        
        output += f"📦 {proc['name']} ({proc_id})\n"
        output += f"   Category: {proc['category']}\n"
        output += f"   Location: {proc['location']}\n"
        output += f"   Expected: ~{proc['typical_space_gb']} GB\n"
        output += f"   Safety: {proc['safety'].upper()}\n"
        output += f"   {proc['description']}\n\n"
        total_space += proc['typical_space_gb']
    
    output += f"💾 TOTAL POTENTIAL SAVINGS: ~{total_space:.1f} GB\n"
    output += "\n⚠️ To execute: use execute_cleanup with procedure name and confirm=true"
    output += "\n🔒 ALWAYS ask user permission before running any cleanup!"
    
    return output


def do_scan_junk() -> str:
    """Scan for cleanable junk files"""
    output = "=== JUNK SCAN RESULTS ===\n\n"
    locations = [
        ("NPM Cache", "~/.npm"),
        ("pnpm Store", "~/Library/pnpm/store"),
        ("System Caches", "~/Library/Caches"),
        ("Puppeteer Cache", "~/.cache/puppeteer"),
        ("UV Cache", "~/.cache/uv"),
        ("Google Caches", "~/Library/Caches/Google"),
    ]
    total_mb = 0
    output += "📦 CACHE SIZES:\n"
    for name, path in locations:
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            size_output = run_cmd(f'du -sh "{expanded}" 2>/dev/null | cut -f1')
            if size_output and not size_output.startswith("Error"):
                output += f"  {name}: {size_output}\n"
    output += "\n💡 Use get_procedures() to see cleanup options."
    return output


def do_get_procedures(category: Optional[str] = None) -> str:
    """Get available cleanup procedures"""
    output = "=== CLEANUP PROCEDURES ===\n\n"
    total_space = 0
    for proc_id, proc in CLEANUP_PROCEDURES.items():
        if category and proc["category"] != category:
            continue
        output += f"📦 {proc['name']} ({proc_id})\n"
        output += f"   Location: {proc['location']}\n"
        output += f"   Expected: ~{proc['typical_space_gb']} GB\n"
        output += f"   Safety: {proc['safety'].upper()}\n\n"
        total_space += proc['typical_space_gb']
    output += f"💾 TOTAL POTENTIAL: ~{total_space:.1f} GB\n"
    output += "\n⚠️ Use execute_cleanup with confirm=true (requires permission!)"
    return output


def do_get_emergency_workflow(current_percent: Optional[int] = None) -> str:
    """Get recommended cleanup workflow based on disk usage"""
    if current_percent is None:
        current_percent = get_disk_percent()
    
    status = get_status_level(current_percent)
    output = f"=== EMERGENCY WORKFLOW ===\n"
    output += f"Current Usage: {current_percent}%\n"
    output += f"Status: {status}\n\n"
    
    if status == "NORMAL":
        output += "✅ Disk is healthy. No immediate action needed.\n"
        output += "💡 Consider monthly maintenance: npm_cache, dev_caches, homebrew"
        return output
    
    output += "🚨 RECOMMENDED CLEANUP SEQUENCE:\n\n"
    
    # Priority order based on safety and impact
    sequence = [
        ("npm_cache", "Priority 1 - Biggest impact, safest"),
        ("dev_caches", "Priority 2 - Dev tool caches"),
        ("homebrew", "Priority 3 - Old package versions"),
    ]
    
    if current_percent >= THRESHOLD_EMERGENCY:
        sequence.append(("system_caches", "Priority 4 - System caches"))
        sequence.append(("vscode_caches", "Priority 5 - VS Code caches"))
    
    if current_percent >= THRESHOLD_CRITICAL:
        sequence.append(("google_caches", "Priority 6 - Google caches"))
        sequence.append(("pnpm_store", "Priority 7 - pnpm store"))
    
    total_expected = 0
    for proc_id, priority in sequence:
        proc = CLEANUP_PROCEDURES[proc_id]
        output += f"  {priority}\n"
        output += f"    → {proc['name']}: ~{proc['typical_space_gb']} GB\n"
        total_expected += proc['typical_space_gb']
    
    output += f"\n💾 Total Expected Recovery: ~{total_expected:.1f} GB\n"
    output += f"📉 Estimated Final: ~{current_percent - (total_expected/2.28):.0f}%\n"
    output += "\n🔒 PERMISSION REQUIRED for each cleanup step!"
    return output


def do_execute_cleanup(procedure: str, confirm: bool) -> str:
    """Execute a cleanup procedure"""
    if procedure not in CLEANUP_PROCEDURES:
        return f"❌ Unknown procedure: {procedure}\nAvailable: {', '.join(CLEANUP_PROCEDURES.keys())}"
    
    if not confirm:
        proc = CLEANUP_PROCEDURES[procedure]
        return f"""⚠️ CONFIRMATION REQUIRED

Procedure: {proc['name']}
Command: {proc['command']}
Location: {proc['location']}
Expected space: ~{proc['typical_space_gb']} GB
Safety: {proc['safety'].upper()}

To execute, call again with confirm=true
🔒 Make sure you have user permission!"""
    
    proc = CLEANUP_PROCEDURES[procedure]
    output = f"=== EXECUTING: {proc['name']} ===\n\n"
    output += f"Command: {proc['command']}\n"
    output += f"Running...\n\n"
    
    # Execute the command
    result = run_cmd(proc['command'], timeout=120)
    
    output += f"Output:\n{result}\n\n"
    
    # Check new disk status
    new_percent = get_disk_percent()
    output += f"✅ Cleanup complete!\n"
    output += f"Current disk usage: {new_percent}%"
    
    return output


def do_get_app_status() -> str:
    """Get application approval status"""
    output = "=== APPLICATION STATUS ===\n\n"
    
    approved_file = DISK_MONITOR_DIR / "approved_apps.txt"
    pending_file = DISK_MONITOR_DIR / "pending_apps.txt"
    
    # Run app_manager.sh to refresh status
    run_cmd(f"{DISK_MONITOR_DIR}/app_manager.sh scan 2>/dev/null")
    
    # Count apps
    approved_count = 0
    pending_count = 0
    
    if approved_file.exists():
        approved_count = len(approved_file.read_text().strip().split('\n'))
    
    if pending_file.exists():
        pending_text = pending_file.read_text().strip()
        if pending_text:
            pending_count = len(pending_text.split('\n'))
    
    output += f"📊 Summary:\n"
    output += f"   Approved: {approved_count} apps\n"
    output += f"   Pending: {pending_count} apps\n\n"
    
    if pending_count > 0:
        output += "⚠️ PENDING APPROVAL:\n"
        for line in pending_file.read_text().strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    output += f"   • {parts[0]} ({parts[1]}) - Installed: {parts[2]}\n"
        output += "\nUse approve_app to approve pending applications."
    else:
        output += "✅ All applications are approved!"
    
    return output

def do_approve_app(app_name: str) -> str:
    """Approve a pending application"""
    pending_file = DISK_MONITOR_DIR / "pending_apps.txt"
    approved_file = DISK_MONITOR_DIR / "approved_apps.txt"
    
    if not pending_file.exists():
        return "❌ No pending apps file found. Run get_app_status first."
    
    pending_text = pending_file.read_text()
    found_line = None
    
    for line in pending_text.strip().split('\n'):
        if line.startswith(f"{app_name}|"):
            found_line = line
            break
    
    if not found_line:
        return f"❌ App '{app_name}' not found in pending list."
    
    # Add to approved
    with open(approved_file, 'a') as f:
        f.write(found_line + '\n')
    
    # Remove from pending
    new_pending = '\n'.join(l for l in pending_text.strip().split('\n') if not l.startswith(f"{app_name}|"))
    pending_file.write_text(new_pending)
    
    return f"✅ Approved: {app_name}"


def do_get_history(days: int = 7) -> str:
    """Get disk usage history"""
    output = "=== DISK USAGE HISTORY ===\n\n"
    
    log_file = DISK_MONITOR_DIR / "disk_usage.log"
    
    if not log_file.exists():
        return "❌ No history file found. Run daily_disk_check.sh to start logging."
    
    lines = log_file.read_text().strip().split('\n')
    recent_lines = lines[-days:] if len(lines) > days else lines
    
    output += f"📈 Last {len(recent_lines)} entries:\n\n"
    
    for line in recent_lines:
        if ',' in line:
            parts = line.split(',')
            if len(parts) >= 2:
                date_time = parts[0]
                try:
                    usage_kb = int(parts[1])
                    usage_gb = usage_kb / 1048576
                    output += f"   {date_time}: {usage_gb:.1f} GB\n"
                except:
                    pass
    
    output += "\n💡 Run daily_disk_check.sh regularly for accurate trends."
    return output

# ============== MAIN ==============

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print(__doc__)
    else:
        asyncio.run(main())
