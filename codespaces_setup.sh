#!/bin/bash

# GitHub Codespaces Build Script for YouTube Downloader
# Run this in a GitHub Codespace to build your APK

echo "========================================="
echo "YouTube Downloader - Codespaces Build"
echo "========================================="
echo ""

set -e  # Exit on error

# 1. Install system dependencies
echo "1/5 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    git \
    zip \
    unzip \
    openjdk-17-jdk \
    wget \
    curl \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    build-essential \
    ccache

# 2. Set up Java
echo ""
echo "2/5 Setting up Java..."
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
echo "JAVA_HOME=$JAVA_HOME" >> ~/.bashrc
echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> ~/.bashrc

# 3. Install Python packages
echo ""
echo "3/5 Installing Python packages..."
pip3 install --upgrade pip setuptools wheel
pip3 install buildozer cython==0.29.33

# 4. Rename files if needed
echo ""
echo "4/5 Preparing project files..."
if [ -f "kivy_main.py" ]; then
    echo "Renaming kivy_* files..."
    mv kivy_main.py main.py 2>/dev/null || true
    mv kivy_downloader.py downloader.py 2>/dev/null || true
    mv kivy_ffmpeg.py ffmpeg.py 2>/dev/null || true
    mv kivy_debug.py debug.py 2>/dev/null || true
    mv buildozer_spec.txt buildozer.spec 2>/dev/null || true
fi

# 5. Download binaries
echo ""
echo "5/5 Downloading binaries..."
if [ ! -f "simple_binary_setup.sh" ]; then
    echo "Error: simple_binary_setup.sh not found!"
    exit 1
fi

chmod +x simple_binary_setup.sh
./simple_binary_setup.sh

# 6. Build
echo ""
echo "========================================="
echo "Ready to build!"
echo "========================================="
echo ""
echo "Run this command to build:"
echo "  buildozer android debug"
echo ""
echo "This will take 20-40 minutes on first build."
echo ""
echo "Your APK will be in: bin/ytdownloader-*.apk"
