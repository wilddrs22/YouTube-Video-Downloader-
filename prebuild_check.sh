#!/bin/bash

# Pre-build verification script for YouTube Downloader APK
# Run this before building to catch issues early

set +e  # Don't exit on error, we want to check everything

echo "========================================="
echo "YouTube Downloader - Pre-Build Check"
echo "========================================="
echo ""

ALL_OK=true

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check and report
check_item() {
    local item=$1
    local command=$2
    local required=$3
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $item"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $item - REQUIRED"
            ALL_OK=false
        else
            echo -e "${YELLOW}⚠${NC} $item - OPTIONAL"
        fi
        return 1
    fi
}

# 1. Check System Tools
echo "1. Checking System Tools..."
echo "----------------------------"

check_item "Python 3" "command -v python3" true
check_item "pip3" "command -v pip3" true
check_item "git" "command -v git" true
check_item "Java (JDK)" "command -v java" true
check_item "zip" "command -v zip" true
check_item "unzip" "command -v unzip" true
check_item "wget or curl" "command -v wget || command -v curl" true
check_item "ccache (speeds up builds)" "command -v ccache" false

echo ""

# 2. Check Python Packages
echo "2. Checking Python Packages..."
echo "-------------------------------"

check_item "buildozer" "pip3 show buildozer" true
check_item "cython" "pip3 show cython" true

echo ""

# 3. Check Java Version
echo "3. Checking Java Version..."
echo "---------------------------"

if command -v java > /dev/null 2>&1; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$JAVA_VERSION" -ge 11 ]; then
        echo -e "${GREEN}✓${NC} Java version: $JAVA_VERSION (>= 11 required)"
    else
        echo -e "${RED}✗${NC} Java version: $JAVA_VERSION (>= 11 required)"
        ALL_OK=false
    fi
else
    echo -e "${RED}✗${NC} Java not found"
    ALL_OK=false
fi

echo ""

# 4. Check Environment Variables
echo "4. Checking Environment Variables..."
echo "------------------------------------"

if [ -n "$JAVA_HOME" ]; then
    echo -e "${GREEN}✓${NC} JAVA_HOME is set: $JAVA_HOME"
else
    echo -e "${YELLOW}⚠${NC} JAVA_HOME not set (buildozer might set it)"
fi

if [ -n "$USE_CCACHE" ]; then
    echo -e "${GREEN}✓${NC} ccache enabled"
else
    echo -e "${YELLOW}⚠${NC} ccache not enabled (can speed up builds)"
fi

echo ""

# 5. Check Project Files
echo "5. Checking Project Files..."
echo "----------------------------"

REQUIRED_FILES=(
    "main.py:Main app file"
    "downloader.py:Downloader module"
    "ffmpeg.py:FFmpeg handler"
    "debug.py:Debug module"
    "buildozer.spec:Build configuration"
)

for file_info in "${REQUIRED_FILES[@]}"; do
    IFS=':' read -r file desc <<< "$file_info"
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file ($desc)"
    else
        echo -e "${RED}✗${NC} $file ($desc) - MISSING"
        ALL_OK=false
    fi
done

echo ""

# 6. Check Binaries
echo "6. Checking Binaries..."
echo "-----------------------"

if [ ! -d "binaries" ]; then
    echo -e "${RED}✗${NC} binaries/ directory not found"
    echo -e "   ${YELLOW}Run: ./simple_binary_setup.sh${NC}"
    ALL_OK=false
else
    REQUIRED_BINARIES=(
        "yt-dlp:YouTube downloader"
        "ffmpeg-arm64:FFmpeg for ARM64"
        "ffmpeg-armv7:FFmpeg for ARMv7"
    )
    
    for binary_info in "${REQUIRED_BINARIES[@]}"; do
        IFS=':' read -r binary desc <<< "$binary_info"
        if [ -f "binaries/$binary" ]; then
            size=$(ls -lh "binaries/$binary" | awk '{print $5}')
            if [ -x "binaries/$binary" ]; then
                echo -e "${GREEN}✓${NC} $binary ($desc) - $size [executable]"
            else
                echo -e "${YELLOW}⚠${NC} $binary ($desc) - $size [not executable, will fix during build]"
            fi
        else
            echo -e "${RED}✗${NC} $binary ($desc) - MISSING"
            ALL_OK=false
        fi
    done
fi

echo ""

# 7. Check buildozer.spec
echo "7. Checking buildozer.spec..."
echo "------------------------------"

if [ -f "buildozer.spec" ]; then
    # Check key settings
    PACKAGE_NAME=$(grep "^package.name" buildozer.spec | cut -d'=' -f2 | tr -d ' ')
    PACKAGE_DOMAIN=$(grep "^package.domain" buildozer.spec | cut -d'=' -f2 | tr -d ' ')
    
    if [ -n "$PACKAGE_NAME" ]; then
        echo -e "${GREEN}✓${NC} Package name: $PACKAGE_NAME"
    else
        echo -e "${RED}✗${NC} Package name not set in buildozer.spec"
        ALL_OK=false
    fi
    
    if [ -n "$PACKAGE_DOMAIN" ]; then
        echo -e "${GREEN}✓${NC} Package domain: $PACKAGE_DOMAIN"
    else
        echo -e "${RED}✗${NC} Package domain not set in buildozer.spec"
        ALL_OK=false
    fi
    
    # Check if requirements include kivy
    if grep -q "requirements.*kivy" buildozer.spec; then
        echo -e "${GREEN}✓${NC} Kivy in requirements"
    else
        echo -e "${RED}✗${NC} Kivy not in requirements"
        ALL_OK=false
    fi
else
    echo -e "${RED}✗${NC} buildozer.spec not found"
    ALL_OK=false
fi

echo ""

# 8. Check Disk Space
echo "8. Checking Disk Space..."
echo "-------------------------"

AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
AVAILABLE_SPACE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')

echo "   Available space: $AVAILABLE_SPACE"

if [ "$AVAILABLE_SPACE_GB" -ge 15 ]; then
    echo -e "${GREEN}✓${NC} Sufficient disk space (15GB+ recommended)"
else
    echo -e "${YELLOW}⚠${NC} Low disk space (15GB+ recommended, you have ${AVAILABLE_SPACE_GB}GB)"
fi

echo ""

# 9. Check for Previous Builds
echo "9. Checking Previous Builds..."
echo "-------------------------------"

if [ -d ".buildozer" ]; then
    BUILDOZER_SIZE=$(du -sh .buildozer 2>/dev/null | cut -f1)
    echo -e "${GREEN}✓${NC} .buildozer exists ($BUILDOZER_SIZE) - will speed up build"
else
    echo -e "${YELLOW}ℹ${NC} No .buildozer directory (first build will take longer)"
fi

if [ -d "bin" ]; then
    APK_COUNT=$(ls -1 bin/*.apk 2>/dev/null | wc -l)
    if [ "$APK_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Found $APK_COUNT previous APK(s) in bin/"
        ls -lh bin/*.apk 2>/dev/null | awk '{print "   - " $9 " (" $5 ")"}'
    fi
else
    echo -e "${YELLOW}ℹ${NC} No bin/ directory (will be created during build)"
fi

echo ""

# 10. Summary
echo "========================================="
echo "Summary"
echo "========================================="

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "You're ready to build. Run:"
    echo -e "${GREEN}buildozer android debug${NC}"
    echo ""
    echo "First build will take 20-40 minutes."
    echo "Subsequent builds: 2-5 minutes."
    exit 0
else
    echo -e "${RED}✗ Some checks failed!${NC}"
    echo ""
    echo "Please fix the issues above before building."
    echo ""
    echo "Common fixes:"
    echo "  • Install missing tools: sudo apt install <tool>"
    echo "  • Install Python packages: pip3 install --user <package>"
    echo "  • Download binaries: ./simple_binary_setup.sh"
    echo "  • Rename files: mv kivy_*.py to *.py"
    exit 1
fi
