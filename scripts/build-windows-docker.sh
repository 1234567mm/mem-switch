#!/bin/bash
# Mem-Switch Windows Build Script (cargo-xwin)
# Builds Windows executable from Linux environment using cargo-xwin

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/dist/windows"

echo "🔨 Mem-Switch Windows Build (cargo-xwin)"
echo "========================================="

# Create build directory
mkdir -p "$BUILD_DIR"

# Check if cargo-xwin is installed
if ! command -v cargo-xwin &> /dev/null; then
    echo "❌ cargo-xwin not found. Installing..."
    cargo install cargo-xwin
fi

echo "✓ cargo-xwin is ready"

# Build Windows executable using cargo-xwin
echo ""
echo "📦 Building Windows executable..."
echo ""

cd "$PROJECT_ROOT/src-tauri"
cargo tauri build \
  --target x86_64-pc-windows-msvc \
  --bundles nsis,app \
  -- --xwin-arch x86_64

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
echo "========================================="
echo "Build complete!"
