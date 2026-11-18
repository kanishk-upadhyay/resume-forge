#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Building ResumeForge Studio release binary via SwiftPM..."
swift build -c release

BIN_PATH="$SCRIPT_DIR/.build/release/ResumeForgeStudio"
APP_DEST="/Applications/ResumeForge Studio.app"
LOCAL_APP="$SCRIPT_DIR/ResumeForge Studio.app"

for TARGET_APP in "$APP_DEST" "$LOCAL_APP"; do
    echo "==> Bundling into $TARGET_APP..."
    mkdir -p "$TARGET_APP/Contents/MacOS"
    mkdir -p "$TARGET_APP/Contents/Resources"
    
    cp "$BIN_PATH" "$TARGET_APP/Contents/MacOS/ResumeForgeStudio"
    cp "$SCRIPT_DIR/AppIcon.icns" "$TARGET_APP/Contents/Resources/AppIcon.icns"
    cp "$SCRIPT_DIR/Info.plist" "$TARGET_APP/Contents/Info.plist"
    
    echo "==> Applying ad-hoc code signature..."
    codesign --force --deep -s - "$TARGET_APP"
done

echo "==> Refreshing LaunchServices database..."
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f -u "$APP_DEST" 2>/dev/null || true
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP_DEST"

touch "$APP_DEST"
echo "==> Refreshing macOS Dock..."
killall Dock 2>/dev/null || true

echo "✓ Build and bundling successful: $APP_DEST"
