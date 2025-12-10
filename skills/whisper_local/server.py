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
WHISPER = shutil.which("whisper") or "/opt/homebrew/bin/whisper"
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

# Get tool name from environment (injected by Hub) or fallback
TOOL_NAME = os.environ.get("MCP_SKILL_NAME", "whisper_local")
server = Server(TOOL_NAME)

class WhisperTranscribeArgs(BaseModel):
    """Arguments for whisper_transcribe tool"""
    audio_file: str = Field(description="Path to audio file (MP3, WAV, M4A)")
    output_dir: Optional[str] = Field(default=None, description="Output directory (default: same as input)")
    language: str = Field(default="en", description="Language code: en, he, es, etc.")
    model: str = Field(default="base", description="Whisper model: base, small, medium, large")
    output_format: str = Field(default="txt", description="Output format: txt, srt, vtt, json")

@server.list_tools()
async def list_tools():
    return [Tool(
        name=TOOL_NAME,
        description="Transcribe audio file locally using Whisper (free, no API).",
        inputSchema=WhisperTranscribeArgs.model_json_schema()
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != TOOL_NAME:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    try:
        args = WhisperTranscribeArgs(**arguments)
        result = do_whisper_transcribe(args)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

def do_whisper_transcribe(args: WhisperTranscribeArgs) -> str:
    """Transcribe audio with local Whisper"""
    if not os.path.exists(WHISPER):
        return f"ERROR: whisper not found at {WHISPER}. Install with: pip install openai-whisper"
    
    if not os.path.exists(args.audio_file):
        return f"ERROR: Audio file not found: {args.audio_file}"
    
    output_dir = args.output_dir or str(Path(args.audio_file).parent)
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if file needs compression (>25MB)
    file_size = os.path.getsize(args.audio_file) / (1024 * 1024)
    audio_to_transcribe = args.audio_file
    
    if file_size > 25:
        if not os.path.exists(FFMPEG):
             return f"ERROR: File > 25MB requires compression but ffmpeg not found at {FFMPEG}"
             
        compressed = f"{output_dir}/compressed_temp.mp3"
        compress_cmd = [FFMPEG, "-i", args.audio_file, "-b:a", "32k", "-ac", "1", "-y", compressed]
        subprocess.run(compress_cmd, capture_output=True, timeout=300)
        audio_to_transcribe = compressed
    
    cmd = [WHISPER, audio_to_transcribe, "--output_dir", output_dir, 
           "--output_format", args.output_format, "--model", args.model, "--language", args.language]

    import time
    from datetime import datetime

    # Get media duration using ffprobe
    media_duration = 0
    ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
    if os.path.exists(ffprobe):
        try:
            # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp3
            probe_cmd = [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", args.audio_file]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            if probe_result.returncode == 0:
                media_duration = float(probe_result.stdout.strip())
        except Exception:
            pass # Ignore if probing fails

    start_time = time.time()
    start_dt = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    
    # 30 minute timeout for transcription
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

    end_time = time.time()
    end_dt = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
    duration = end_time - start_time
    
    # Format duration nicely
    if duration < 60:
        duration_str = f"{duration:.2f} seconds"
    else:
        m, s = divmod(duration, 60)
        duration_str = f"{int(m)}m {s:.2f}s"
    
    # Format media duration nicely
    if media_duration < 60:
        media_str = f"{media_duration:.2f} seconds"
    else:
        mm, ss = divmod(media_duration, 60)
        media_str = f"{int(mm)}m {ss:.2f}s"

    # Calculate Speed (Real-time factor)
    speed_str = "N/A"
    if duration > 0 and media_duration > 0:
        speed = media_duration / duration
        speed_str = f"{speed:.1f}x"
    
    # Format file size nicely
    file_size_mb = os.path.getsize(args.audio_file) / (1024 * 1024)
    size_str = f"{file_size_mb:.2f} MB"

    # Cleanup temp file if created
    if audio_to_transcribe != args.audio_file and os.path.exists(audio_to_transcribe):
        os.remove(audio_to_transcribe)

    output = f"=== Whisper Transcription ===\n"
    output += f"File:       {args.audio_file}\n"
    output += f"Size:       {size_str}\n"
    output += f"Length:     {media_str}\n"
    output += f"Model:      {args.model}\n"
    output += f"Language:   {args.language}\n"
    output += f"Output Dir: {output_dir}\n"
    output += f"Start Time: {start_dt}\n"
    output += f"End Time:   {end_dt}\n"
    output += f"Elapsed:    {duration_str}\n"
    output += f"Speed:      {speed_str}\n\n"
    
    if result.returncode == 0:
        # Attempt to read the generated file content
        # Whisper saves as <filename>.<format>
        # If we used a temp compressed file, the output name will match that temp file (e.g. compressed_temp.srt)
        # We want to restore the original filename format
        
        generated_base = os.path.splitext(os.path.basename(audio_to_transcribe))[0]
        generated_filename = f"{generated_base}.{args.output_format}"
        generated_path = os.path.join(output_dir, generated_filename)
        
        # If we used compression, we should rename the output to match original file
        if audio_to_transcribe != args.audio_file:
            original_base = os.path.splitext(os.path.basename(args.audio_file))[0]
            final_filename = f"{original_base}.{args.output_format}"
            final_path = os.path.join(output_dir, final_filename)
            if os.path.exists(generated_path):
                os.rename(generated_path, final_path)
            output_filename = final_filename
            output_path = final_path
        else:
             output_filename = generated_filename
             output_path = generated_path
        
        if os.path.exists(output_path):
            try:
                content = Path(output_path).read_text()
                # Truncate if too long (e.g. 100KB) to avoid context limit issues
                if len(content) > 50000:
                    content = content[:50000] + "\n... (truncated)"
                
                output += f"--- Transcript ({output_filename}) ---\n{content}\n-----------------------------------\n"
                output += "✅ Success!"
            except Exception as e:
                output += f"✅ Success (but failed to read output file: {e})"
        else:
            output += f"✅ Success (saved to {output_dir})"
    else:
        output += f"❌ Failed (code {result.returncode})\n"
        if result.stderr: output += f"Error: {result.stderr[-500:]}"
    return output

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
