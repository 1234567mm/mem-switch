#!/bin/bash
# Mem-Switch Release Script
# Creates a git tag and triggers GitHub Actions release build

set -e

VERSION=${1:-$(cat src-tauri/Cargo.toml | grep '^version' | cut -d'"' -f2)}

echo "🔖 Creating release for version $VERSION"

# Check if tag already exists
if git tag | grep -q "^v$VERSION$"; then
    echo "❌ Tag v$VERSION already exists"
    exit 1
fi

# Prompt for confirmation
echo ""
echo "This will:"
echo "  1. Create git tag v$VERSION"
echo "  2. Push to origin"
echo "  3. Trigger GitHub Actions release build"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Create and push tag
git tag "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"

echo ""
echo "✅ Tag v$VERSION pushed!"
echo ""
echo "GitHub Actions will now:"
echo "  - Build Linux (AppImage + deb) for x86_64 and ARM64"
echo "  - Build Windows (exe) for x86_64 and ARM64"
echo "  - Build macOS (app + dmg) for x86_64, ARM64, and Universal"
echo ""
echo "Check progress at: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
