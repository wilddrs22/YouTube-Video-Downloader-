import os
import shutil

def get_ffmpeg_path():
    """Get the path to ffmpeg binary, checking bundled location first"""
    # Check bundled binary locations (for APK)
    bundled_paths = [
        '/data/data/org.yourapp.ytdownloader/files/app/binaries/ffmpeg',
        'binaries/ffmpeg',
        '/data/data/org.yourapp.ytdownloader/files/ffmpeg',
    ]
    
    for path in bundled_paths:
        if os.path.exists(path):
            # Make sure it's executable
            try:
                os.chmod(path, 0o755)
                return path
            except:
                pass
    
    # Check system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    return None

def ensure_ffmpeg():
    """Ensure ffmpeg is available"""
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        raise FileNotFoundError(
            "FFmpeg not found! The app requires FFmpeg to work. "
            "Please ensure the binaries are properly packaged."
        )
    return ffmpeg_path
