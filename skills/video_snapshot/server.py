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

server = Server("video_snapshot")

class VideoSnapshotArgs(BaseModel):
    """Arguments for video_snapshot tool"""
    video_file: str = Field(description="Absolute path to the video file (MP4, MKV, etc.)")
    timestamps: list[str] = Field(description="List of timestamps to capture (e.g., ['00:01:23', '83.5'])")
    output_dir: Optional[str] = Field(default=None, description="Directory to save the snapshots. Defaults to video directory.")

@server.list_tools()
async def list_tools():
    return [Tool(
        name="video_snapshot",
        description="Take high-quality image snapshots from a video at multiple timestamps.",
        inputSchema=VideoSnapshotArgs.model_json_schema()
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != "video_snapshot":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    try:
        args = VideoSnapshotArgs(**arguments)
        result = do_snapshot(args)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


def parse_time_to_seconds(time_str: str) -> float:
    """Convert a time string (HH:MM:SS.mmm or seconds) to float seconds."""
    try:
        # If it's just a number, return it
        return float(time_str)
    except ValueError:
        pass
        
    # Handle HH:MM:SS.mmm
    parts = time_str.split(':')
    seconds = 0.0
    try:
        if len(parts) == 3: # HH:MM:SS
            seconds += float(parts[0]) * 3600
            seconds += float(parts[1]) * 60
            seconds += float(parts[2])
        elif len(parts) == 2: # MM:SS
            seconds += float(parts[0]) * 60
            seconds += float(parts[1])
        else:
            # parsing failed, fallback to 0 or raise
            return 0.0
    except ValueError:
        return 0.0
        
    return seconds

def format_seconds_to_str(seconds: float) -> str:
    """Format seconds to HH-MM-SS-mmm string."""
    h = int(seconds // 3600)
    remainder = seconds % 3600
    m = int(remainder // 60)
    s_float = remainder % 60
    s = int(s_float)
    ms = int((s_float - s) * 1000)
    
    # If hours is 0, we can optionally omit it, but user asked for professional format.
    # Let's include H if > 0, otherwise M-S-ms is usually cleaner, 
    # but "hours, minutes, seconds" request suggests full precision.
    # Let's do a consistent HH-MM-SS-mmm format to sort correctly.
    
    return f"{h:02d}-{m:02d}-{s:02d}-{ms:03d}"

def do_snapshot(args: VideoSnapshotArgs) -> str:
    """Extract frames using ffmpeg"""
    if not os.path.exists(FFMPEG):
        return f"ERROR: ffmpeg not found at {FFMPEG}. Please install it (e.g., brew install ffmpeg)"
    
    if not os.path.exists(args.video_file):
        return f"ERROR: Video file not found: {args.video_file}"

    # Determine output path
    video_path = Path(args.video_file)
    output_dir = Path(args.output_dir) if args.output_dir else video_path.parent
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    output_log = f"=== Video Snapshots ===\nVideo: {args.video_file}\nOutput Dir: {output_dir}\n\n"
    success_count = 0
    
    for ts in args.timestamps:
        # normalize string to standardized filename format
        secs = parse_time_to_seconds(ts)
        time_suffix = format_seconds_to_str(secs)
        
        filename = f"{video_path.stem}_{time_suffix}.jpg"
        output_path = output_dir / filename
        
        # ffmpeg command
        cmd = [
            FFMPEG,
            "-ss", ts, # keep original string for ffmpeg as it handles it well
            "-i", args.video_file,
            "-frames:v", "1",
            "-q:v", "2",
            "-y", # overwrite
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and output_path.exists():
            output_log += f"✅ {ts} -> {filename}\n"
            success_count += 1
        else:
            output_log += f"❌ {ts} -> Failed (code {result.returncode})\n"

    output_log += f"\nSummary: {success_count}/{len(args.timestamps)} snapshots created."
        
    return output_log

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
