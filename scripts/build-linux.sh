#!/bin/bash
# Mem-Switch Linux Build Script
# Builds AppImage and .deb packages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔨 Mem-Switch Linux Build"
echo "========================="

cd "$PROJECT_ROOT/src-tauri"

# Check if cargo tauri is available
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust/Cargo not found. Please install Rust first."
    echo "   Visit: https://rustup.rs/"
    exit 1
fi

# Install Tauri CLI if needed
if ! cargo tauri --version &> /dev/null; then
    echo "📦 Installing Tauri CLI..."
    cargo install tauri-cli
fi

echo "✓ Building Linux packages..."
echo ""

# Build all Linux targets
cargo tauri build --bundles appimage,deb

echo ""
echo "✅ Build complete!"
echo ""
echo "📁 Output directory: $PROJECT_ROOT/src-tauri/target/release/bundle/"
echo ""

# List built packages
echo "Built packages:"
find "$PROJECT_ROOT/src-tauri/target/release/bundle/" -type f \( -name "*.AppImage" -o -name "*.deb" \) 2>/dev/null | while read -r pkg; do
    echo "  - $(basename "$pkg")"
done

echo ""
echo "========================="
echo "Installation:"
echo ""
echo "  AppImage: chmod +x Mem-Switch*.AppImage && ./Mem-Switch*.AppImage"
echo "  deb:      sudo dpkg -i mem-switch*.deb"
echo ""
