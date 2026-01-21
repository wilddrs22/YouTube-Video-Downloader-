import subprocess
import json
import os
import re
from ffmpeg import get_ffmpeg_path
from debug import log, write_progress
from android.storage import primary_external_storage_path

def get_ytdlp_path():
    """Get the path to yt-dlp binary"""
    if os.path.exists('/data/data/org.yourapp.ytdownloader/files/app/binaries/yt-dlp'):
        return '/data/data/org.yourapp.ytdownloader/files/app/binaries/yt-dlp'
    elif os.path.exists('binaries/yt-dlp'):
        return 'binaries/yt-dlp'
    else:
        return 'yt-dlp'  # Fallback

YTDLP_PATH = get_ytdlp_path()

def get_download_dir():
    """Get the appropriate download directory for Android"""
    try:
        storage = primary_external_storage_path()
        download_dir = os.path.join(storage, 'Download')
        if not os.path.exists(download_dir):
            download_dir = os.path.join(storage, 'Downloads')
        return download_dir
    except:
        return '/sdcard/Download/'

DOWNLOAD_DIR = get_download_dir()
YTDLP_USER_AGENT = ("Mozilla/5.0 (Linux; Android 13) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/118.0.0.0 Mobile Safari/537.36")

def get_available_formats(url):
    """Fetch available video formats/resolutions"""
    try:
        result = subprocess.run(
            [YTDLP_PATH, "-j", url], 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=30
        )
        info = json.loads(result.stdout)
        formats = info.get("formats", [])
        available_res = {}
        target_res = {
            "7680x4320": "8K", 
            "3840x2160": "4K",
            "2560x1440": "2K", 
            "1920x1080": "1080p",
            "1280x720": "720p"
        }
        
        for f in formats:
            if f.get("vcodec") != "none" and f.get("height") and f.get("width"):
                res_str = f"{f['width']}x{f['height']}"
                fps = f.get("fps", 0)
                if res_str in target_res and res_str not in available_res:
                    available_res[res_str] = {"id": f["format_id"], "fps": fps}
        
        return available_res
    except subprocess.CalledProcessError as e:
        log(f"Error fetching formats: {e}")
        return {}
    except Exception as e:
        log(f"Unexpected error: {e}")
        return {}

def run_with_progress(cmd, prefix="Downloading"):
    """Run subprocess and capture progress in real-time"""
    # Set environment for ffmpeg
    env = os.environ.copy()
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        env['PATH'] = os.path.dirname(ffmpeg_path) + ':' + env.get('PATH', '')
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        env=env
    )
    
    for line in process.stdout:
        line = line.strip()
        
        # Look for download progress patterns
        if '[download]' in line:
            match = re.search(r'(\d+\.?\d*)%', line)
            if match:
                percent = match.group(1)
                write_progress(f"{prefix}: {percent}%")
                log(line)
            elif 'ETA' in line:
                write_progress(f"{prefix}: {line}")
                log(line)
        elif 'Merging' in line or 'merge' in line.lower():
            write_progress("Merging files...")
            log(line)
        elif 'Extracting' in line:
            write_progress("Extracting audio...")
            log(line)
        else:
            log(line)
    
    process.wait()
    return process.returncode

def download_video(url, selected_res=None):
    """Download video with real-time progress tracking"""
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        return "ERROR: FFmpeg not found"
    
    if not url.strip():
        return "ERROR: Invalid URL"

    log(f"Starting video download for: {url}")
    
    height_map = {
        "7680x4320": "4320",
        "3840x2160": "2160",
        "2560x1440": "1440",
        "1920x1080": "1080",
        "1280x720": "720"
    }
    
    height = height_map.get(selected_res or "1920x1080", "1080")
    output_file = os.path.join(DOWNLOAD_DIR, "%(title)s.mp4")

    cmd = [
        YTDLP_PATH,
        "-f", f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
        "-o", output_file,
        "--merge-output-format", "mp4",
        "--ffmpeg-location", os.path.dirname(ffmpeg_path),
        "--user-agent", YTDLP_USER_AGENT,
        "--referer", url,
        "--add-header", "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "--add-header", "Accept-Language:en-us,en;q=0.5",
        "--retries", "10",
        "--fragment-retries", "10",
        "--extractor-retries", "5",
        "--geo-bypass",
        "--sleep-requests", "1",
        "--http-chunk-size", "10M",
        "--newline",
        url
    ]
    
    write_progress("Starting video download...")
    
    try:
        returncode = run_with_progress(cmd, "VIDEO")
        
        if returncode == 0:
            write_progress("SUCCESS: Video download complete")
            log("Video download successful")
            return f"Video download complete! Saved to {DOWNLOAD_DIR}"
        else:
            write_progress("ERROR: Video download failed")
            log(f"Video download failed with code {returncode}")
            return f"Video download failed (error code: {returncode})"
            
    except Exception as e:
        log(f"Unexpected error: {e}")
        write_progress("ERROR: Unexpected error occurred")
        return f"Error: {str(e)}"

def download_audio(url):
    """Download audio only and convert to MP3"""
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        return "ERROR: FFmpeg not found"
    
    if not url.strip():
        return "ERROR: Invalid URL"

    log(f"Starting audio download for: {url}")
    
    output_file = os.path.join(DOWNLOAD_DIR, "%(title)s.mp3")

    cmd = [
        YTDLP_PATH,
        "-f", "bestaudio/best",
        "-o", output_file,
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--ffmpeg-location", os.path.dirname(ffmpeg_path),
        "--user-agent", YTDLP_USER_AGENT,
        "--referer", url,
        "--add-header", "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "--add-header", "Accept-Language:en-us,en;q=0.5",
        "--retries", "10",
        "--fragment-retries", "10",
        "--extractor-retries", "5",
        "--geo-bypass",
        "--sleep-requests", "1",
        "--newline",
        url
    ]
    
    write_progress("Starting audio download...")
    
    try:
        returncode = run_with_progress(cmd, "AUDIO")
        
        if returncode == 0:
            write_progress("SUCCESS: Audio download complete")
            log("Audio download successful")
            return f"Audio download complete! Saved to {DOWNLOAD_DIR}"
        else:
            write_progress("ERROR: Audio download failed")
            log(f"Audio download failed with code {returncode}")
            return f"Audio download failed (error code: {returncode})"
            
    except Exception as e:
        log(f"Unexpected error: {e}")
        write_progress("ERROR: Unexpected error occurred")
        return f"Error: {str(e)}"
