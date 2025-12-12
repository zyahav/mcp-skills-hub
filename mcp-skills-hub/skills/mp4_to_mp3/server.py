#!/usr/bin/env python3
import asyncio
import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

# Configuration
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

# Get tool name from environment (injected by Hub) or fallback
TOOL_NAME = os.environ.get("MCP_SKILL_NAME", "mp4_to_mp3")
server = Server(TOOL_NAME)

class Mp4ToMp3Args(BaseModel):
    """Arguments for mp4_to_mp3 tool"""
    input_file: str = Field(description="Path to input MP4 file")
    output_file: Optional[str] = Field(default=None, description="Output MP3 path (default: same name as input)")
    quality: int = Field(default=2, description="Audio quality 0-9 (lower = better, default: 2)")

@server.list_tools()
async def list_tools():
    return [Tool(
        name=TOOL_NAME,
        description="Convert MP4 video file to MP3 audio using ffmpeg.",
        inputSchema=Mp4ToMp3Args.model_json_schema()
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != TOOL_NAME:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    try:
        args = Mp4ToMp3Args(**arguments)
        result = do_mp4_to_mp3(args)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

def do_mp4_to_mp3(args: Mp4ToMp3Args) -> str:
    """Convert MP4 to MP3"""
    if not os.path.exists(FFMPEG):
        return f"ERROR: ffmpeg not found at {FFMPEG}. Install with: brew install ffmpeg"
    
    if not os.path.exists(args.input_file):
        return f"ERROR: Input file not found: {args.input_file}"
    
    output_file = args.output_file or args.input_file.rsplit(".", 1)[0] + ".mp3"
    
    # -vn: disable video recording
    # -acodec libmp3lame: force mp3 encoding
    # -q:a: variable bit rate quality
    # -y: overwrite output files
    cmd = [FFMPEG, "-i", args.input_file, "-vn", "-acodec", "libmp3lame", "-q:a", str(args.quality), "-y", output_file]
    
    import time
    from datetime import datetime
    
    start_time = time.time()
    start_dt = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    end_time = time.time()
    end_dt = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
    duration = end_time - start_time
    
    # Format duration nicely
    if duration < 60:
        duration_str = f"{duration:.2f} seconds"
    else:
        m, s = divmod(duration, 60)
        duration_str = f"{int(m)}m {s:.2f}s"
    
    output = f"=== MP4 to MP3 ===\n"
    output += f"Input: {args.input_file}\n"
    output += f"Output: {output_file}\n"
    output += f"Start Time: {start_dt}\n"
    output += f"End Time:   {end_dt}\n"
    output += f"Elapsed:    {duration_str}\n\n"
    
    if result.stderr: output += result.stderr[-500:] + "\n"  # ffmpeg outputs to stderr
    output += "✅ Success!" if result.returncode == 0 else f"❌ Failed (code {result.returncode})"
    return output

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
