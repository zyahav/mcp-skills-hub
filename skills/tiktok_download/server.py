#!/usr/bin/env python3
import asyncio
import subprocess
import os
import shutil
from pathlib import Path
from typing import Literal
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

# Configuration
DEFAULT_OUTPUT = Path.home() / "Documents" / "transcriptions"
YT_DLP = shutil.which("yt-dlp") or "/opt/homebrew/bin/yt-dlp"

# Get tool name from environment (injected by Hub) or fallback
TOOL_NAME = os.environ.get("MCP_SKILL_NAME", "tiktok_download")
server = Server(TOOL_NAME)

class TikTokDownloadArgs(BaseModel):
    """Arguments for tiktok_download tool"""
    url: str = Field(description="TikTok video URL")
    format: Literal["mp4", "mp3"] = Field(default="mp4", description="Output format: mp4 (video) or mp3 (audio only)")
    output_dir: str = Field(default=str(DEFAULT_OUTPUT), description="Output directory")

@server.list_tools()
async def list_tools():
    return [Tool(
        name=TOOL_NAME,
        description="Download TikTok video as MP4 or extract audio as MP3.",
        inputSchema=TikTokDownloadArgs.model_json_schema()
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != TOOL_NAME:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    try:
        args = TikTokDownloadArgs(**arguments)
        result = do_tiktok_download(args)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

def do_tiktok_download(args: TikTokDownloadArgs) -> str:
    """Download TikTok video/audio"""
    if not os.path.exists(YT_DLP):
        return f"ERROR: yt-dlp not found at {YT_DLP}. Install with: brew install yt-dlp"
    
    os.makedirs(args.output_dir, exist_ok=True)
    cmd = [YT_DLP, "--no-playlist"]
    
    if args.format == "mp3":
        cmd.extend(["-x", "--audio-format", "mp3"])
    else:
        # TikTok specific format selection or default to best
        # yt-dlp usually handles TikTok pretty well with defaults
        cmd.extend(["--merge-output-format", "mp4"])
    
    # Use generic template to avoid special char issues in filenames
    # For TikTok, %(id)s is usually good to include as titles can be duplicates
    cmd.extend(["-o", f"{args.output_dir}/%(title)s_%(id)s.%(ext)s", args.url])
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    output = f"=== TikTok Download ===\nURL: {args.url}\nFormat: {args.format}\nOutput: {args.output_dir}\n\n"
    if result.stdout: output += result.stdout + "\n"
    if result.stderr: output += result.stderr + "\n"
    output += "✅ Success!" if result.returncode == 0 else f"❌ Failed (code {result.returncode})"
    return output

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
