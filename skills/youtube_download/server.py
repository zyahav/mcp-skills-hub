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
DEFAULT_OUTPUT = Path.home() / "Downloads"
YT_DLP = shutil.which("yt-dlp") or "/opt/homebrew/bin/yt-dlp"

server = Server("youtube_download")

class YouTubeDownloadArgs(BaseModel):
    """Arguments for youtube_download tool"""
    url: str = Field(description="YouTube video URL")
    format: Literal["mp4", "mp3"] = Field(default="mp4", description="Output format: mp4 (video) or mp3 (audio only)")
    output_dir: str = Field(default=str(DEFAULT_OUTPUT), description="Output directory")
    quality: str = Field(default="best", description="Quality: best, 1080p, 720p, 480p for video; best, 320, 192, 128 for audio")

@server.list_tools()
async def list_tools():
    return [Tool(
        name="youtube_download",
        description="Download YouTube video as MP4 or extract audio as MP3.",
        inputSchema=YouTubeDownloadArgs.model_json_schema()
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != "youtube_download":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    try:
        args = YouTubeDownloadArgs(**arguments)
        result = do_youtube_download(args)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

def do_youtube_download(args: YouTubeDownloadArgs) -> str:
    """Download YouTube video/audio"""
    if not os.path.exists(YT_DLP):
        return f"ERROR: yt-dlp not found at {YT_DLP}. Install with: brew install yt-dlp"
    
    os.makedirs(args.output_dir, exist_ok=True)
    cmd = [YT_DLP, "--no-playlist"]
    
    if args.format == "mp3":
        cmd.extend(["-x", "--audio-format", "mp3"])
        if args.quality != "best":
            cmd.extend(["--audio-quality", args.quality])
    else:
        # Force AVC (H.264) for MP4 compatibility on macOS/QuickLook
        # Try to find H.264 video first, then fallback to any MP4 video
        format_map = {
            "best": "bv*[vcodec^=avc][ext=mp4]+ba[ext=m4a]/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "1080p": "bv*[vcodec^=avc][height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080][ext=mp4]+ba[ext=m4a]/best",
            "720p": "bv*[vcodec^=avc][height<=720][ext=mp4]+ba[ext=m4a]/bv*[height<=720][ext=mp4]+ba[ext=m4a]/best",
            "480p": "bv*[vcodec^=avc][height<=480][ext=mp4]+ba[ext=m4a]/bv*[height<=480][ext=mp4]+ba[ext=m4a]/best",
        }
        cmd.extend(["-f", format_map.get(args.quality, format_map["best"])])
        cmd.extend(["--merge-output-format", "mp4"])
    
    # Use generic template to avoid special char issues in filenames
    cmd.extend(["-o", f"{args.output_dir}/%(title)s.%(ext)s", args.url])
    
    # Run synchronously as this is already in a subprocess from the Hub's perspective
    # But wait, MCP server.run is async. 
    # For a long running job like download, we should accept blocking IF the hub handles it.
    # The Hub uses standard asyncio.subprocess, so if we block the event loop HERE, 
    # we block this specific skill, which is fine (one req at a time per skill is default stdio behavior anyway).
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    output = f"=== YouTube Download ===\nURL: {args.url}\nFormat: {args.format}\nOutput: {args.output_dir}\n\n"
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
