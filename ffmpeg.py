import os
import shutil
import stat

# Try Android imports
try:
    from android.storage import app_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

def get_app_dir():
    """Get app storage directory"""
    if ANDROID:
        try:
            return app_storage_path()
        except:
            return '/data/data/org.wilddrs.ytdownloader/files'
    return os.path.expanduser('~')

def get_ffmpeg_path():
    """Get the path to ffmpeg binary, checking bundled location first"""
    
    # Define all possible paths in priority order
    app_dir = get_app_dir()
    bundled_paths = [
        # Installed in app storage
        os.path.join(app_dir, 'binaries', 'ffmpeg'),
        # Architecture-specific binaries
        os.path.join(app_dir, 'binaries', 'ffmpeg-arm64'),
        os.path.join(app_dir, 'binaries', 'ffmpeg-armv7'),
        # In APK assets
        'binaries/ffmpeg',
        'binaries/ffmpeg-arm64',
        'binaries/ffmpeg-armv7',
        # Hardcoded Android paths
        '/data/data/org.wilddrs.ytdownloader/files/app/binaries/ffmpeg',
        '/data/data/org.wilddrs.ytdownloader/files/binaries/ffmpeg',
        '/data/data/org.wilddrs.ytdownloader/files/app/binaries/ffmpeg-arm64',
        '/data/data/org.wilddrs.ytdownloader/files/binaries/ffmpeg-arm64',
    ]
    
    for path in bundled_paths:
        if os.path.exists(path):
            try:
                # Make sure it's executable
                os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                print(f"✓ Found FFmpeg at: {path}")
                return path
            except Exception as e:
                print(f"✗ Found FFmpeg at {path} but couldn't make it executable: {e}")
    
    # Check system PATH as last resort
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        print(f"✓ Using system FFmpeg: {system_ffmpeg}")
        return system_ffmpeg
    
    print("✗ FFmpeg not found in any location")
    return None

def ensure_ffmpeg():
    """Ensure ffmpeg is available, raise error if not"""
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        error_msg = (
            "FFmpeg not found!\n\n"
            "The app requires FFmpeg to process videos.\n"
            "Please ensure the binaries are properly packaged in the APK.\n\n"
            "If you built this yourself, run:\n"
            "./setup_binaries_simple.sh\n"
            "before building with buildozer."
        )
        raise FileNotFoundError(error_msg)
    
    # Verify it's actually executable
    if not os.access(ffmpeg_path, os.X_OK):
        try:
            os.chmod(ffmpeg_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        except:
            raise PermissionError(f"FFmpeg found at {ffmpeg_path} but is not executable")
    
    return ffmpeg_path

def test_ffmpeg():
    """Test if FFmpeg is working"""
    try:
        ffmpeg = ensure_ffmpeg()
        import subprocess
        result = subprocess.run([ffmpeg, '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg is working: {version}")
            return True
        else:
            print(f"✗ FFmpeg error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ FFmpeg test failed: {e}")
        return False

if __name__ == '__main__':
    # Test when run directly
    print("Testing FFmpeg setup...")
    print(f"App directory: {get_app_dir()}")
    print(f"Android mode: {ANDROID}")
    print()
    
    path = get_ffmpeg_path()
    if path:
        print(f"FFmpeg path: {path}")
        print(f"Exists: {os.path.exists(path)}")
        print(f"Executable: {os.access(path, os.X_OK)}")
        print()
        test_ffmpeg()
    else:
        print("FFmpeg not found!")
