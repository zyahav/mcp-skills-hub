#!/usr/bin/env python3
import asyncio, json, sys, subprocess, os
from pathlib import Path
from typing import Dict
import logging

# Setup debug logging to file immediately
log_path = Path(__file__).parent / 'hub_debug.log'
logging.basicConfig(
    filename=str(log_path),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.info("----------------------------------------------------------------")
logging.info(f"Starting MCP Hub. Python: {sys.executable}")

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    logging.info("Successfully imported mcp")
except ImportError as e:
    logging.critical(f"Failed to import mcp: {e}")
    logging.critical(f"sys.path: {sys.path}")
    sys.exit(1)
logging.info(f"Starting MCP Hub. Python: {sys.executable}")
logging.info(f"CWD: {os.getcwd()}")
logging.info(f"Path: {sys.path}")

ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"
SERVER_NAME = "skills-hub"

server = Server(SERVER_NAME)

PROCESSES: Dict[str, asyncio.subprocess.Process] = {}
MANIFESTS: Dict[str, dict] = {}
TOOL_MAPPING: Dict[str, str] = {} # tool_name -> skill_name
SKILL_LOCKS: Dict[str, asyncio.Lock] = {}  # Lock per skill to prevent concurrent access

# Event to signal that skills are ready
STARTUP_EVENT = asyncio.Event()

async def load_skills_and_initialize():
    """Background task to load and initialize skills"""
    print(f"Loading skills from {SKILLS_DIR}...", file=sys.stderr)
    if not SKILLS_DIR.exists():
        print(f"Skills directory not found: {SKILLS_DIR}", file=sys.stderr)
        STARTUP_EVENT.set()
        return

    # 1. Spawn Processes
    spawn_tasks = []
    for skill_dir in SKILLS_DIR.iterdir():
        manifest_path = skill_dir / "skill.json"
        if not manifest_path.exists():
            continue
        spawn_tasks.append(spawn_skill(skill_dir, manifest_path))
    
    await asyncio.gather(*spawn_tasks)
    
    # 2. Initialize Handshakes
    print("Initializing skills...", file=sys.stderr)
    init_tasks = []
    for name, proc in PROCESSES.items():
        init_tasks.append(initialize_skill_process(name, proc))
    
    await asyncio.gather(*init_tasks)
    
    # 3. Build Tool Mapping (Initial Scan)
    print("Building tool mapping...", file=sys.stderr)
    await populate_tool_mapping()
    
    print("Hub startup complete! Skills ready.", file=sys.stderr)
    STARTUP_EVENT.set()

async def spawn_skill(skill_dir: Path, manifest_path: Path):
    try:
        manifest = json.loads(manifest_path.read_text())
        name = manifest["name"]
        cmd = manifest["command"]
        
        # Use the current python interpreter if the command is "python3"
        if cmd[0] == "python3":
            cmd[0] = sys.executable
        
        print(f"Starting skill: {name}", file=sys.stderr)

        env = os.environ.copy()
        env["MCP_SKILL_NAME"] = name

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=skill_dir,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr, # Forward stderr
        )

        PROCESSES[name] = process
        MANIFESTS[name] = manifest
        SKILL_LOCKS[name] = asyncio.Lock()  # Create lock for this skill
    except Exception as e:
        print(f"Failed to load skill {skill_dir.name}: {e}", file=sys.stderr)

async def initialize_skill_process(name: str, proc: asyncio.subprocess.Process):
    """Perform MCP handshake with a skill process"""
    lock = SKILL_LOCKS.get(name)
    if not lock:
        return False
    
    async with lock:
        try:
            # 1. Initialize
            init_req = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", # Updated protocol version
                    "capabilities": {},
                    "clientInfo": {"name": "skills-hub", "version": "1.0"}
                },
                "id": 0
            }
            proc.stdin.write((json.dumps(init_req) + "\n").encode('utf-8'))
            await proc.stdin.drain()
            
            # 2. Await response
            line = await proc.stdout.readline()
            if not line:
                print(f"Skill {name} failed to respond to initialize", file=sys.stderr)
                return False
                
            resp = json.loads(line.decode('utf-8'))
            if "error" in resp:
                print(f"Skill {name} initialization error: {resp['error']}", file=sys.stderr)
                return False
                
            # 3. Send initialized notification
            proc.stdin.write((json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }) + "\n").encode('utf-8'))
            await proc.stdin.drain()
            
            print(f"Skill {name} initialized successfully", file=sys.stderr)
            return True
        except Exception as e:
            print(f"Error initializing skill {name}: {e}", file=sys.stderr)
            return False

async def populate_tool_mapping():
    """Populate TOOL_MAPPING by listing tools from all skills"""
    TOOL_MAPPING.clear()
    for name, proc in list(PROCESSES.items()):
        lock = SKILL_LOCKS.get(name)
        if not lock:
            continue
        async with lock:
            try:
                request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
                proc.stdin.write((json.dumps(request) + "\n").encode('utf-8'))
                await proc.stdin.drain()
                
                line = await proc.stdout.readline()
                if line:
                    response = json.loads(line.decode('utf-8'))
                    if "result" in response:
                        skill_tools = response["result"].get("tools", [])
                        for t in skill_tools:
                            tool_obj = Tool(**t)
                            TOOL_MAPPING[tool_obj.name] = name
            except Exception as e:
                    print(f"Error listing tools for {name}: {e}", file=sys.stderr)

async def proxy_list_tools():
    # Wait for startup to complete
    await STARTUP_EVENT.wait()
    
    tools = []
    # Using list() to iterate copy safe
    for name, proc in list(PROCESSES.items()):
        lock = SKILL_LOCKS.get(name)
        if not lock:
            continue
        async with lock:
            try:
                request = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                }
                if proc.returncode is not None:
                    print(f"Skill {name} is dead. Restarting logic needed.", file=sys.stderr)
                    continue

                proc.stdin.write((json.dumps(request) + "\n").encode('utf-8'))
                await proc.stdin.drain()
                
                line = await proc.stdout.readline()
                if not line:
                    continue
                    
                response = json.loads(line.decode('utf-8'))
                if "error" in response:
                    continue
                    
                for t in response.get("result", {}).get("tools", []):
                    tools.append(Tool(**t))
                    
            except Exception as e:
                print(f"Error communicating with skill {name}: {e}", file=sys.stderr)
            
    return tools


@server.list_tools()
async def list_tools():
    return await proxy_list_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    await STARTUP_EVENT.wait()
    
    skill_name = TOOL_MAPPING.get(name)
    if not skill_name:
        skill_name = name
        
    proc = PROCESSES.get(skill_name)
    lock = SKILL_LOCKS.get(skill_name)
    
    if not proc or not lock:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
        "id": 1
    }

    async with lock:
        try:
            proc.stdin.write((json.dumps(request) + "\n").encode('utf-8'))
            await proc.stdin.drain()

            line = await proc.stdout.readline()
            if not line:
                 return [TextContent(type="text", text="Error: Empty response from skill")]
                 
            response = json.loads(line.decode('utf-8'))
            if "error" in response:
                return [TextContent(type="text", text=f"Error from skill: {response['error']}")]
                
            return response.get("result", {}).get("content", [])
        except Exception as e:
            return [TextContent(type="text", text=f"Error communicating with skill: {str(e)}")]


async def main():
    # Start startup task in background
    asyncio.create_task(load_skills_and_initialize())
    
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
