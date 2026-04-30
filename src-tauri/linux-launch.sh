#!/bin/bash
# Mem-Switch Linux Launcher
# Supports WSL, X11, Wayland, and headless environments

set -e

echo "🚀 Mem-Switch Launcher"

# Function to check if running in WSL
is_wsl() {
    if grep -qi "microsoft" /proc/version 2>/dev/null; then
        return 0
    fi
    return 1
}

# Function to check graphical environment
check_display() {
    # Check for Wayland
    if [ -n "$WAYLAND_DISPLAY" ]; then
        echo "✓ Wayland display detected: $WAYLAND_DISPLAY"
        return 0
    fi

    # Check for X11
    if [ -n "$DISPLAY" ]; then
        echo "✓ X11 display detected: $DISPLAY"
        return 0
    fi

    # Check for WSLg (Windows 11)
    if is_wsl && [ -d "/mnt/wslg" ]; then
        export DISPLAY=:0
        echo "✓ WSLg detected, using DISPLAY=:0"
        return 0
    fi

    return 1
}

# Main startup logic
main() {
    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    APP_BIN="$SCRIPT_DIR/mem-switch"

    # Check if binary exists
    if [ ! -f "$APP_BIN" ]; then
        echo "❌ Error: Application binary not found at $APP_BIN"
        exit 1
    fi

    # Check for graphical environment
    if check_display; then
        echo "🎨 Starting Mem-Switch with graphical interface..."
        exec "$APP_BIN" "$@"
    else
        # No graphical environment detected
        echo ""
        echo "⚠️  No graphical display detected"
        echo ""

        if is_wsl; then
            echo "🪟 Running in WSL environment"
            echo ""
            echo "To run Mem-Switch with GUI, you need to:"
            echo ""
            echo "  Option 1: Use WSLg (Windows 10/11)"
            echo "    - Ensure Windows is updated (Windows 11 recommended)"
            echo "    - Run: wsl --shutdown"
            echo "    - Restart WSL and try again"
            echo ""
            echo "  Option 2: Install X Server (e.g., VcXsrv, Xming)"
            echo "    1. Install VcXsrv on Windows"
            echo "    2. Run XLaunch with these settings:"
            echo "       - Multiple windows"
            echo "       - Start no client"
            echo "       - Disable access control"
            echo "    3. Then run:"
            echo "       export DISPLAY=:0"
            echo "       $APP_BIN"
            echo ""
            echo "  Option 3: Run in browser mode (if available)"
            echo "    $APP_BIN --browser"
            echo ""
        else
            echo "🐧 Running in Linux environment"
            echo ""
            echo "To run Mem-Switch with GUI:"
            echo ""
            echo "  Option 1: Start X11 session"
            echo "    export DISPLAY=:0"
            echo "    $APP_BIN"
            echo ""
            echo "  Option 2: Install required packages"
            echo "    sudo apt install libgtk-3-0 libwebkit2gtk-4.0-37"
            echo ""
            echo "  Option 3: Run in browser mode (if available)"
            echo "    $APP_BIN --browser"
            echo ""
        fi

        exit 1
    fi
}

main "$@"
