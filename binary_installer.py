#!/usr/bin/env python3
"""
Runtime binary installer for Android
This script copies binaries from APK assets to app storage
"""

import os
import shutil
import stat
from android.storage import app_storage_path

def install_binaries():
    """Copy and setup binaries on first run"""
    app_dir = app_storage_path()
    bin_dir = os.path.join(app_dir, 'binaries')
    
    # Create binaries directory
    os.makedirs(bin_dir, exist_ok=True)
    
    # Source paths (in APK)
    apk_bin_dir = os.path.join(os.path.dirname(__file__), 'binaries')
    
    binaries = ['yt-dlp', 'ffmpeg-arm64', 'ffmpeg-armv7', 'get_ffmpeg.sh']
    
    for binary in binaries:
        src = os.path.join(apk_bin_dir, binary)
        dst = os.path.join(bin_dir, binary)
        
        # Copy if not exists or if source is newer
        if os.path.exists(src):
            if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
                try:
                    shutil.copy2(src, dst)
                    # Make executable
                    os.chmod(dst, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    print(f"✓ Installed {binary}")
                except Exception as e:
                    print(f"✗ Failed to install {binary}: {e}")
            else:
                print(f"✓ {binary} already installed")
        else:
            print(f"✗ Source binary not found: {src}")
    
    # Create ffmpeg symlink
    ffmpeg_link = os.path.join(bin_dir, 'ffmpeg')
    ffmpeg_script = os.path.join(bin_dir, 'get_ffmpeg.sh')
    
    if os.path.exists(ffmpeg_script) and not os.path.exists(ffmpeg_link):
        try:
            os.symlink(ffmpeg_script, ffmpeg_link)
            print("✓ Created ffmpeg symlink")
        except:
            # If symlink fails, copy the script
            shutil.copy2(ffmpeg_script, ffmpeg_link)
            os.chmod(ffmpeg_link, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            print("✓ Copied ffmpeg script")
    
    return bin_dir

if __name__ == '__main__':
    try:
        bin_dir = install_binaries()
        print(f"\n✓ All binaries installed to: {bin_dir}")
        print(f"  - yt-dlp: {os.path.join(bin_dir, 'yt-dlp')}")
        print(f"  - ffmpeg: {os.path.join(bin_dir, 'ffmpeg')}")
    except Exception as e:
        print(f"\n✗ Installation failed: {e}")
        import traceback
        traceback.print_exc()
