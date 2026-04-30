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

# Build Windows executable using cargo-xwin with clang-cl linker
echo ""
echo "📦 Building Windows executable..."
echo ""

cd "$PROJECT_ROOT/src-tauri"

# Set linker to clang-cl for xwin
export CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER="clang-cl"

# Build for x86_64
echo "Building x86_64..."
cargo xwin build --release --target x86_64-pc-windows-msvc

# Copy output
cp target/x86_64-pc-windows-msvc/release/mem-switch-desktop.exe "$BUILD_DIR/Mem-Switch_${VERSION:-0.1.0}_x64.exe" 2>/dev/null || \
cp target/x86_64-pc-windows-msvc/release/mem-switch-desktop.exe "$BUILD_DIR/Mem-Switch_x64.exe"

echo ""
echo "✅ x86_64 build complete!"

# Build for ARM64 (if requested)
if [ "$1" = "--arm64" ] || [ "$1" = "--all" ]; then
    echo ""
    echo "Building ARM64..."
    export CARGO_TARGET_AARCH64_PC_WINDOWS_MSVC_LINKER="clang-cl"
    cargo xwin build --release --target aarch64-pc-windows-msvc

    cp target/aarch64-pc-windows-msvc/release/mem-switch-desktop.exe "$BUILD_DIR/Mem-Switch_ARM64.exe" 2>/dev/null || \
    cp target/aarch64-pc-windows-msvc/release/mem-switch-desktop.exe "$BUILD_DIR/Mem-Switch_ARM64.exe"
    echo "✅ ARM64 build complete!"
fi

# Check build output
echo ""
echo "📁 Output directory: $BUILD_DIR"
echo ""
echo "Built executables:"
ls -la "$BUILD_DIR" 2>/dev/null || echo "   No files found"

echo ""
echo "========================================="
echo "Build complete!"
echo ""
echo "Note: To create NSIS installer, run on Windows:"
echo "  cargo tauri build --target x86_64-pc-windows-msvc --bundles nsis"
