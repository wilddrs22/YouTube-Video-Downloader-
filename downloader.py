import subprocess
import json
import os
import re
from ffmpeg import get_ffmpeg_path, ensure_ffmpeg
from debug import log, write_progress

# Try Android imports
try:
    from android.storage import primary_external_storage_path, app_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

def get_ytdlp_path():
    """Get the path to yt-dlp binary"""
    possible_paths = [
        # Installed in app storage
        os.path.join(get_app_dir(), 'binaries', 'yt-dlp'),
        # In APK assets
        'binaries/yt-dlp',
        # System installed
        '/data/data/org.wilddrs.ytdownloader/files/app/binaries/yt-dlp',
        '/data/data/org.wilddrs.ytdownloader/files/binaries/yt-dlp',
        'yt-dlp'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                os.chmod(path, 0o755)
                log(f"Using yt-dlp from: {path}")
                return path
            except:
                pass
    
    # Fallback
    log("Warning: yt-dlp not found in expected locations, using 'yt-dlp'")
    return 'yt-dlp'

def get_app_dir():
    """Get app directory"""
    if ANDROID:
        try:
            return app_storage_path()
        except:
            return '/data/data/org.wilddrs.ytdownloader/files'
    return os.path.expanduser('~')

def get_download_dir():
    """Get the appropriate download directory"""
    if ANDROID:
        try:
            storage = primary_external_storage_path()
            # Try Downloads first, then Download
            for folder in ['Downloads', 'Download']:
                download_dir = os.path.join(storage, folder)
                if os.path.exists(download_dir):
                    log(f"Using download directory: {download_dir}")
                    return download_dir
            # Create Downloads if neither exists
            download_dir = os.path.join(storage, 'Downloads')
            os.makedirs(download_dir, exist_ok=True)
            log(f"Created download directory: {download_dir}")
            return download_dir
        except Exception as e:
            log(f"Error getting Android storage: {e}")
            # Fallback
            return '/sdcard/Download/'
    else:
        # Desktop fallback
        return os.path.expanduser('~/Downloads')

YTDLP_PATH = get_ytdlp_path()
DOWNLOAD_DIR = get_download_dir()
YTDLP_USER_AGENT = ("Mozilla/5.0 (Linux; Android 13) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/118.0.0.0 Mobile Safari/537.36")

def get_available_formats(url):
    """Fetch available video formats/resolutions"""
    log(f"Fetching formats for: {url}")
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
        
        log(f"Found {len(available_res)} formats")
        return available_res
    except subprocess.CalledProcessError as e:
        log(f"Error fetching formats: {e}")
        log(f"stderr: {e.stderr}")
        return {}
    except subprocess.TimeoutExpired:
        log("Timeout while fetching formats")
        return {}
    except Exception as e:
        log(f"Unexpected error: {e}")
        import traceback
        log(traceback.format_exc())
        return {}

def run_with_progress(cmd, prefix="Downloading"):
    """Run subprocess and capture progress in real-time"""
    # Set environment for ffmpeg
    env = os.environ.copy()
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        env['PATH'] = os.path.dirname(ffmpeg_path) + ':' + env.get('PATH', '')
        log(f"FFmpeg path added to PATH: {os.path.dirname(ffmpeg_path)}")
    
    log(f"Running command: {' '.join(cmd)}")
    
    try:
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
                write_progress("Merging video and audio...")
                log(line)
            elif 'Extracting' in line:
                write_progress("Extracting audio...")
                log(line)
            elif 'Destination' in line:
                write_progress("Preparing download...")
                log(line)
            else:
                log(line)
        
        process.wait()
        return process.returncode
    except Exception as e:
        log(f"Error running command: {e}")
        import traceback
        log(traceback.format_exc())
        return 1

def download_video(url, selected_res=None):
    """Download video with real-time progress tracking"""
    try:
        ffmpeg_path = ensure_ffmpeg()
        log(f"FFmpeg verified at: {ffmpeg_path}")
    except Exception as e:
        error_msg = f"ERROR: FFmpeg not found - {str(e)}"
        log(error_msg)
        return error_msg
    
    if not url.strip():
        return "ERROR: Invalid URL"

    log(f"Starting video download for: {url}")
    log(f"Selected resolution: {selected_res}")
    
    height_map = {
        "7680x4320": "4320",
        "3840x2160": "2160",
        "2560x1440": "1440",
        "1920x1080": "1080",
        "1280x720": "720"
    }
    
    height = height_map.get(selected_res or "1920x1080", "1080")
    
    # Create output filename template
    output_file = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    log(f"Output template: {output_file}")

    cmd = [
        YTDLP_PATH,
        "-f", f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
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
        "--no-check-certificates",
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
            return f"✓ Video downloaded successfully!\n\nSaved to: {DOWNLOAD_DIR}\n\nCheck your Downloads folder."
        else:
            write_progress("ERROR: Video download failed")
            log(f"Video download failed with code {returncode}")
            return f"✗ Download failed (error code: {returncode})\n\nPlease check:\n• Internet connection\n• URL is valid\n• Storage permissions"
            
    except Exception as e:
        log(f"Unexpected error: {e}")
        import traceback
        log(traceback.format_exc())
        write_progress("ERROR: Unexpected error occurred")
        return f"✗ Error: {str(e)}"

def download_audio(url):
    """Download audio only and convert to MP3"""
    try:
        ffmpeg_path = ensure_ffmpeg()
        log(f"FFmpeg verified at: {ffmpeg_path}")
    except Exception as e:
        error_msg = f"ERROR: FFmpeg not found - {str(e)}"
        log(error_msg)
        return error_msg
    
    if not url.strip():
        return "ERROR: Invalid URL"

    log(f"Starting audio download for: {url}")
    
    output_file = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    log(f"Output template: {output_file}")

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
        "--no-check-certificates",
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
            return f"✓ Audio downloaded successfully!\n\nSaved to: {DOWNLOAD_DIR}\n\nCheck your Downloads folder for the MP3 file."
        else:
            write_progress("ERROR: Audio download failed")
            log(f"Audio download failed with code {returncode}")
            return f"✗ Download failed (error code: {returncode})\n\nPlease check:\n• Internet connection\n• URL is valid\n• Storage permissions"
            
    except Exception as e:
        log(f"Unexpected error: {e}")
        import traceback
        log(traceback.format_exc())
        write_progress("ERROR: Unexpected error occurred")
        return f"✗ Error: {str(e)}"
