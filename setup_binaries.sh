#!/bin/bash

# Script to download and setup ffmpeg and yt-dlp binaries for Android

echo "Setting up binaries for Android build..."

# Create binaries directory
mkdir -p binaries

# Download yt-dlp for Android
echo "Downloading yt-dlp..."
if [ ! -f "binaries/yt-dlp" ]; then
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o binaries/yt-dlp
    chmod +x binaries/yt-dlp
    echo "✓ yt-dlp downloaded"
else
    echo "✓ yt-dlp already exists"
fi

# Download FFmpeg for Android (arm64-v8a)
echo "Downloading FFmpeg for arm64-v8a..."
if [ ! -f "binaries/ffmpeg-arm64" ]; then
    # Using ffmpeg-kit releases for Android
    wget https://github.com/arthenica/ffmpeg-kit/releases/download/v6.0/ffmpeg-kit-full-6.0-android.zip -O ffmpeg-android.zip
    unzip -j ffmpeg-android.zip "*arm64-v8a/ffmpeg" -d binaries/
    mv binaries/ffmpeg binaries/ffmpeg-arm64
    rm ffmpeg-android.zip
    chmod +x binaries/ffmpeg-arm64
    echo "✓ FFmpeg arm64 downloaded"
else
    echo "✓ FFmpeg arm64 already exists"
fi

# Download FFmpeg for Android (armeabi-v7a)
echo "Downloading FFmpeg for armeabi-v7a..."
if [ ! -f "binaries/ffmpeg-armv7" ]; then
    wget https://github.com/arthenica/ffmpeg-kit/releases/download/v6.0/ffmpeg-kit-full-6.0-android.zip -O ffmpeg-android.zip
    unzip -j ffmpeg-android.zip "*armeabi-v7a/ffmpeg" -d binaries/
    mv binaries/ffmpeg binaries/ffmpeg-armv7
    rm ffmpeg-android.zip
    chmod +x binaries/ffmpeg-armv7
    echo "✓ FFmpeg armv7 downloaded"
else
    echo "✓ FFmpeg armv7 already exists"
fi

# Create a simple arch detection script
cat > binaries/get_ffmpeg.sh << 'EOF'
#!/bin/bash
ARCH=$(uname -m)
case $ARCH in
    aarch64|arm64)
        exec $(dirname $0)/ffmpeg-arm64 "$@"
        ;;
    armv7l|armv7)
        exec $(dirname $0)/ffmpeg-armv7 "$@"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac
EOF

chmod +x binaries/get_ffmpeg.sh

# Create symlink for easier access
ln -sf get_ffmpeg.sh binaries/ffmpeg

echo ""
echo "✓ All binaries setup complete!"
echo "  - yt-dlp: binaries/yt-dlp"
echo "  - ffmpeg (arm64): binaries/ffmpeg-arm64"
echo "  - ffmpeg (armv7): binaries/ffmpeg-armv7"
echo "  - ffmpeg (auto): binaries/ffmpeg"
echo ""
echo "You can now run: buildozer android debug"
