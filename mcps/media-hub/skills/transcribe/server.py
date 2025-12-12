#!/usr/bin/env python3
"""
TRANSCRIBE - Audio/Video to Text Transcription Skill

Converts audio/video files to text with timestamps using OpenAI Whisper (local, free).

SUPPORTED FORMATS: MP3, MP4, WAV, M4A, FLAC, OGG, WEBM, AAC, WMA

MODELS & SPEED (on Mac M1/M2):
  - tiny:   ~10x realtime  (27 min file → ~3 min)   - Good for speech, fastest
  - base:   ~1.5x realtime (27 min file → ~17 min)  - Better accuracy (default)
  - small:  ~0.5x realtime (27 min file → ~50 min)  - Even better accuracy
  - medium: ~0.2x realtime (27 min file → ~2 hours) - High accuracy
  - large:  ~0.1x realtime (27 min file → ~4 hours) - Highest accuracy

OUTPUT FORMATS:
  - txt: Plain text (no timestamps)
  - srt: SubRip subtitles with timestamps (~20-30 sec segments)
  - vtt: WebVTT subtitles with timestamps
  - json: Full data with word-level info

TIMESTAMP GRANULARITY:
  - Default SRT/VTT: ~20-30 second segments (fast)
  - words_per_segment=10: ~3-5 second segments (10x slower, only for files <10 min)

AUTO-COMPRESSION:
  Files >10MB or >5 min are automatically compressed to 32kbps mono for faster processing.

EXAMPLES:
  Quick transcription:     {file: "video.mp4", model: "tiny", output_format: "txt"}
  With timestamps:         {file: "audio.mp3", output_format: "srt"}
  Short segments (<10min): {file: "short.mp3", output_format: "srt", words_per_segment: 10}
  Hebrew transcription:    {file: "hebrew.mp3", language: "he", output_format: "srt"}
"""
import asyncio
import subprocess
import os
import sys
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
TOOL_NAME = os.environ.get("MCP_SKILL_NAME", "transcribe")
server = Server(TOOL_NAME)

TOOL_DESCRIPTION = """Transcribe audio/video to text with timestamps.

MODELS (speed on Mac):
- tiny: ~10x realtime (fastest, good for speech)
- base: ~1.5x realtime (default, better accuracy)  
- small/medium/large: slower but more accurate

FORMATS: MP3, MP4, WAV, M4A, FLAC, OGG, WEBM
OUTPUT: txt (no timestamps), srt/vtt (with timestamps), json (full data)

For SRT timestamps: ~20-30 sec segments by default.
For ~3 sec segments: use words_per_segment=10 (only for files <10 min, 10x slower).

Files >10MB or >5min are auto-compressed for speed."""

class TranscribeArgs(BaseModel):
    """Arguments for transcribe tool"""
    file: str = Field(description="Path to audio/video file (MP3, MP4, WAV, M4A, FLAC, OGG, WEBM, etc.)")
    output_dir: Optional[str] = Field(default=None, description="Output directory (default: same as input)")
    language: str = Field(default="en", description="Language code: en, he, es, fr, de, ja, zh, etc.")
    model: str = Field(default="base", description="Whisper model: tiny (~10x speed), base (default, ~1.5x), small, medium, large (most accurate)")
    output_format: str = Field(default="txt", description="Output: txt (plain text), srt (subtitles with timestamps), vtt (web subtitles), json (full data)")
    words_per_segment: Optional[int] = Field(default=None, description="For shorter timestamp segments (~3 sec), set to 10. Only works for files <10 min. Makes transcription 10x slower.")

@server.list_tools()
async def list_tools():
    return [Tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        inputSchema=TranscribeArgs.model_json_schema()
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != TOOL_NAME:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    try:
        args = TranscribeArgs(**arguments)
        result = do_transcribe(args)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

def do_transcribe(args: TranscribeArgs) -> str:
    """Transcribe audio/video with local Whisper"""
    import time
    from datetime import datetime
    
    # Log file for debugging
    log_file = "/tmp/transcribe.log"
    def log(msg):
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - {msg}\n")
        print(msg, file=sys.stderr)
    
    log(f"=== NEW TRANSCRIPTION REQUEST ===")
    log(f"Input: {args.file}")
    
    if not os.path.exists(WHISPER):
        return f"ERROR: whisper not found at {WHISPER}. Install with: pip install openai-whisper"
    
    if not os.path.exists(args.file):
        return f"ERROR: File not found: {args.file}"
    
    output_dir = args.output_dir or str(Path(args.file).parent)
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if file needs compression (>10MB OR >5 minutes)
    # For speech transcription, 32kbps mono is sufficient and MUCH faster
    file_size = os.path.getsize(args.file) / (1024 * 1024)
    audio_to_transcribe = args.file
    
    # Get duration to decide on compression
    media_duration_for_compress = 0
    ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
    if os.path.exists(ffprobe):
        try:
            probe_cmd = [ffprobe, "-v", "error", "-show_entries", "format=duration", 
                        "-of", "default=noprint_wrappers=1:nokey=1", args.file]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
            if probe_result.returncode == 0:
                media_duration_for_compress = float(probe_result.stdout.strip())
        except Exception:
            pass
    
    # Compress if file > 10MB OR duration > 5 minutes (300 seconds)
    needs_compression = file_size > 10 or media_duration_for_compress > 300
    
    log(f"File size: {file_size:.1f}MB, Duration: {media_duration_for_compress:.0f}s, Needs compression: {needs_compression}")
    
    if needs_compression:
        if not os.path.exists(FFMPEG):
             return f"ERROR: File needs compression but ffmpeg not found at {FFMPEG}"
             
        compressed = f"{output_dir}/compressed_temp.mp3"
        compress_cmd = [FFMPEG, "-i", args.file, "-b:a", "32k", "-ac", "1", "-y", compressed]
        log(f"Starting compression...")
        compress_start = time.time()
        subprocess.run(compress_cmd, capture_output=True, timeout=300)
        compress_time = time.time() - compress_start
        compressed_size = os.path.getsize(compressed) / (1024 * 1024)
        log(f"Compression done in {compress_time:.1f}s. New size: {compressed_size:.1f}MB")
        audio_to_transcribe = compressed
    
    cmd = [WHISPER, audio_to_transcribe, "--output_dir", output_dir, 
           "--output_format", args.output_format, "--model", args.model, "--language", args.language]
    
    # Add word-level timestamps if words_per_segment is specified (for shorter segments ~3-5 sec)
    # But skip for long files (>10 min) as it makes transcription 10x slower
    if args.words_per_segment:
        if media_duration_for_compress > 600:  # > 10 minutes
            log(f"Skipping word_timestamps for long file ({media_duration_for_compress/60:.0f} min) - using standard ~20-30 sec segments instead")
        else:
            cmd.extend(["--word_timestamps", "True", "--max_words_per_line", str(args.words_per_segment)])
            log(f"Using word timestamps with {args.words_per_segment} words per segment")
    
    log(f"Starting whisper with model={args.model}, format={args.output_format}")

    # Get media duration using ffprobe
    media_duration = 0
    ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
    if os.path.exists(ffprobe):
        try:
            # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp3
            probe_cmd = [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", args.file]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            if probe_result.returncode == 0:
                media_duration = float(probe_result.stdout.strip())
        except Exception:
            pass # Ignore if probing fails

    start_time = time.time()
    start_dt = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    
    # 60 minute timeout for transcription
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

    end_time = time.time()
    end_dt = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
    duration = end_time - start_time
    
    log(f"Whisper finished in {duration:.1f}s, exit code: {result.returncode}")
    
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
    file_size_mb = os.path.getsize(args.file) / (1024 * 1024)
    size_str = f"{file_size_mb:.2f} MB"

    # Cleanup temp file if created
    if audio_to_transcribe != args.file and os.path.exists(audio_to_transcribe):
        os.remove(audio_to_transcribe)

    output = f"=== Whisper Transcription ===\n"
    output += f"File:       {args.file}\n"
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
        if audio_to_transcribe != args.file:
            original_base = os.path.splitext(os.path.basename(args.file))[0]
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
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print(__doc__)
        print("\nTOOL DESCRIPTION (what LLM sees):")
        print("-" * 40)
        print(TOOL_DESCRIPTION)
    else:
        asyncio.run(main())
