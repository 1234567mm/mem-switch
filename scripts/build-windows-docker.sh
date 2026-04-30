#!/bin/bash
# Cross-platform build script for Windows using Docker
# Builds Windows executable from Linux environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/dist/windows"

echo "🔨 Mem-Switch Windows Build (Docker)"
echo "===================================="

# Create build directory
mkdir -p "$BUILD_DIR"

# Check if Docker is running
if ! docker info &>/dev/null; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"

# Build Windows executable using Tauri CLI in Docker container
echo ""
echo "📦 Building Windows executable..."
echo ""

docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /workspace/src-tauri \
    -e CI=true \
    ghcr.io/tauri-apps/tauri-cli:v2.0.0 \
    cargo tauri build --target x86_64-pc-windows-msvc --bundles nsis

# Check build output
if [ -d "$BUILD_DIR" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📁 Output directory: $BUILD_DIR"
    echo ""
    ls -la "$BUILD_DIR" 2>/dev/null || echo "   (build artifacts location)"
else
    echo ""
    echo "⚠️  Build completed but output directory not found"
fi

echo ""
echo "===================================="
echo "Build complete!"
