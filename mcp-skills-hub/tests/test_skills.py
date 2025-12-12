
import sys
import os
import shutil
import unittest
from pathlib import Path

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.youtube_download.server import do_youtube_download, YouTubeDownloadArgs
from skills.whisper_local.server import do_whisper_transcribe, WhisperTranscribeArgs
from skills.video_snapshot.server import do_snapshot, VideoSnapshotArgs

class TestSkills(unittest.TestCase):
    def setUp(self):
        self.output_dir = Path("tests/output")
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)

    def test_01_youtube_download(self):
        """Test downloading a very short video"""
        print("\n[Test] YouTube Download...")
        # Short video: "Video Test 5sec"
        url = "https://www.youtube.com/watch?v=21X5lGlDOfg" 
        args = YouTubeDownloadArgs(
            url=url,
            output_dir=str(self.output_dir)
        )
        if not shutil.which("yt-dlp"):
            print("Skipping YouTube test: yt-dlp not found")
            return

        result = do_youtube_download(args)
        print(result)
        
        # Verify file exists
        files = list(self.output_dir.glob("*.mp4"))
        self.assertTrue(len(files) > 0, "Video file not downloaded")
        self.vid_path = str(files[0])
        print(f"Downloaded: {self.vid_path}")

    def test_02_video_snapshot(self):
        """Test taking snapshots"""
        print("\n[Test] Video Snapshot...")
        # Create a dummy mp4 if previous test didn't run (e.g. running standalone)
        # For now, let's assume we use a sample file or skip if empty
        # Actually, let's just make a very basic test or reuse the download from above if running suite
        
        # Use existing file if available from previous test, or a known sample
        # Since unittest ordering isn't guaranteed without sort, let's try to find any mp4 in output
        # If not, we download one quickly just for this test
        files = list(self.output_dir.glob("*.mp4"))
        if not files:
             url = "https://www.youtube.com/watch?v=21X5lGlDOfg" 
             do_youtube_download(YouTubeDownloadArgs(url=url, output_dir=str(self.output_dir)))
             files = list(self.output_dir.glob("*.mp4"))
        
        if not files:
            self.skipTest("No video file available for snapshot test")
            
        vid_path = str(files[0])
        args = VideoSnapshotArgs(
            video_file=vid_path,
            timestamps=["1", "2.5", "00:00:03"],
            output_dir=str(self.output_dir)
        )
        
        result = do_snapshot(args)
        print(result)
        self.assertIn("Summary: 3/3", result)
        
        # Check files
        snapshots = list(self.output_dir.glob("*.jpg"))
        self.assertEqual(len(snapshots), 3)

    def test_03_whisper_turbo(self):
        """Test Whisper Turbo (Mocking the heavy lifting to avoid 50min wait in CI)"""
        # For a real regression test, we should transcribe a TINY file.
        print("\n[Test] Whisper Turbo...")
        
        # Download a tiny audio if needed, or use the video audio
        files = list(self.output_dir.glob("*.mp4"))
        if not files:
             self.skipTest("No video available")
             
        # Extract audio using ffmpeg for test
        audio_path = self.output_dir / "test_audio.mp3"
        subprocess.run(["ffmpeg", "-i", str(files[0]), "-q:a", "0", "-map", "a", str(audio_path)], 
                      capture_output=True)
        
        args = WhisperTranscribeArgs(
            audio_file=str(audio_path),
            model="turbo", # Use turbo!
            output_format="srt"
        )
        
        result = do_whisper_transcribe(args)
        print(result)
        self.assertIn("Success", result)
        
        srt_file = list(self.output_dir.glob("*.srt"))
        self.assertTrue(len(srt_file) > 0)

if __name__ == '__main__':
    unittest.main()
