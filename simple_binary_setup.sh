#!/bin/bash

# Simplified script to setup binaries for Android
# Uses pre-built static binaries that are easier to package

set -e  # Exit on error

echo "========================================="
echo "YouTube Downloader - Binary Setup"
echo "========================================="
echo ""

# Create binaries directory
mkdir -p binaries
cd binaries

# Function to download with progress
download_file() {
    local url=$1
    local output=$2
    echo "Downloading $output..."
    if command -v wget &> /dev/null; then
        wget -q --show-progress "$url" -O "$output"
    elif command -v curl &> /dev/null; then
        curl -L --progress-bar "$url" -o "$output"
    else
        echo "Error: Neither wget nor curl found. Please install one of them."
        exit 1
    fi
}

# 1. Download yt-dlp (universal Python script)
echo "1/3 Setting up yt-dlp..."
if [ ! -f "yt-dlp" ]; then
    download_file "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp" "yt-dlp"
    chmod +x yt-dlp
    echo "✓ yt-dlp ready"
else
    echo "✓ yt-dlp already exists"
fi

echo ""

# 2. Download FFmpeg for ARM64 (from John Vansickle's static builds)
echo "2/3 Setting up FFmpeg for ARM64..."
if [ ! -f "ffmpeg-arm64" ]; then
    # Note: Using a reliable static build source
    # Alternative: https://github.com/BtbN/FFmpeg-Builds/releases
    echo "Downloading FFmpeg static build for Android ARM64..."
    
    # Create a temporary directory
    mkdir -p tmp_ffmpeg
    cd tmp_ffmpeg
    
    # Download from BtbN builds (works well for Android)
    download_file \
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n6.1-latest-linux-arm64-gpl-6.1.tar.xz" \
        "ffmpeg-arm64.tar.xz"
    
    # Extract
    echo "Extracting..."
    tar -xf ffmpeg-arm64.tar.xz
    
    # Find and copy the binary
    find . -name "ffmpeg" -type f -exec cp {} ../ffmpeg-arm64 \;
    
    # Cleanup
    cd ..
    rm -rf tmp_ffmpeg
    
    chmod +x ffmpeg-arm64
    echo "✓ FFmpeg ARM64 ready"
else
    echo "✓ FFmpeg ARM64 already exists"
fi

echo ""

# 3. Download FFmpeg for ARMv7 (32-bit)
echo "3/3 Setting up FFmpeg for ARMv7..."
if [ ! -f "ffmpeg-armv7" ]; then
    echo "Downloading FFmpeg static build for Android ARMv7..."
    
    mkdir -p tmp_ffmpeg
    cd tmp_ffmpeg
    
    # Download ARMv7 version
    download_file \
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n6.1-latest-linux-armhf-gpl-6.1.tar.xz" \
        "ffmpeg-armv7.tar.xz"
    
    # Extract
    echo "Extracting..."
    tar -xf ffmpeg-armv7.tar.xz
    
    # Find and copy the binary
    find . -name "ffmpeg" -type f -exec cp {} ../ffmpeg-armv7 \;
    
    # Cleanup
    cd ..
    rm -rf tmp_ffmpeg
    
    chmod +x ffmpeg-armv7
    echo "✓ FFmpeg ARMv7 ready"
else
    echo "✓ FFmpeg ARMv7 already exists"
fi

# Create architecture detection wrapper
echo ""
echo "Creating architecture detection wrapper..."
cat > get_ffmpeg.sh << 'EOFSCRIPT'
#!/system/bin/sh
# FFmpeg wrapper for Android - auto-detects architecture

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect architecture
ARCH=$(uname -m)

case "$ARCH" in
    aarch64|arm64)
        FFMPEG_BIN="$SCRIPT_DIR/ffmpeg-arm64"
        ;;
    armv7l|armv7|arm)
        FFMPEG_BIN="$SCRIPT_DIR/ffmpeg-armv7"
        ;;
    *)
        echo "Unsupported architecture: $ARCH" >&2
        exit 1
        ;;
esac

if [ ! -f "$FFMPEG_BIN" ]; then
    echo "FFmpeg binary not found: $FFMPEG_BIN" >&2
    exit 1
fi

# Execute FFmpeg with all arguments
exec "$FFMPEG_BIN" "$@"
EOFSCRIPT

chmod +x get_ffmpeg.sh

# Create ffmpeg symlink/copy
if [ -f "get_ffmpeg.sh" ]; then
    cp get_ffmpeg.sh ffmpeg
    chmod +x ffmpeg
fi

cd ..

# Verify all binaries
echo ""
echo "========================================="
echo "Verification"
echo "========================================="

verify_binary() {
    local binary=$1
    if [ -f "binaries/$binary" ] && [ -x "binaries/$binary" ]; then
        local size=$(ls -lh "binaries/$binary" | awk '{print $5}')
        echo "✓ $binary ($size)"
        return 0
    else
        echo "✗ $binary - MISSING OR NOT EXECUTABLE"
        return 1
    fi
}

ALL_OK=true

verify_binary "yt-dlp" || ALL_OK=false
verify_binary "ffmpeg-arm64" || ALL_OK=false
verify_binary "ffmpeg-armv7" || ALL_OK=false
verify_binary "get_ffmpeg.sh" || ALL_OK=false
verify_binary "ffmpeg" || ALL_OK=false

echo ""
echo "Binary location: $(pwd)/binaries/"
echo ""

if [ "$ALL_OK" = true ]; then
    echo "========================================="
    echo "✓ Setup Complete!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Run: buildozer android debug"
    echo "2. Or: buildozer android release"
    echo ""
    echo "The binaries will be packaged into your APK."
    exit 0
else
    echo "========================================="
    echo "✗ Setup Failed"
    echo "========================================="
    echo ""
    echo "Some binaries are missing. Please check errors above."
    exit 1
fi
