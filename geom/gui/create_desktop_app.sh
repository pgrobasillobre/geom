#!/bin/bash

set -e

ENV_NAME="geom_env"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_NAME="GEOM Structure Studio"
APP_DIR="$ROOT_DIR/dist/${APP_NAME}.app"
MACOS_DIR="$APP_DIR/Contents/MacOS"
RESOURCES_DIR="$APP_DIR/Contents/Resources"

OS_TYPE="$(uname -s)"

if [[ "$OS_TYPE" != "Darwin" ]]; then
    echo "Clickable app bundle creation is currently implemented for macOS."
    echo "The GUI is still available cross-platform after geom_load with:"
    echo "  geomapp"
    echo
    echo "Packaging hooks are intentionally separate here so Linux .desktop/AppImage"
    echo "and Windows shortcut/MSI support can be added without changing the GUI code."
    exit 0
fi

if ! command -v conda &> /dev/null; then
    echo "Conda is required. Run ./install.sh first, then source your shell rc and run geom_load."
    exit 1
fi

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>geom-structure-studio</string>
    <key>CFBundleIdentifier</key>
    <string>org.geom.structure-studio</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
</dict>
</plist>
EOF

cat > "$MACOS_DIR/geom-structure-studio" << EOF
#!/bin/bash
source "\$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
cd "$ROOT_DIR"
exec python "$ROOT_DIR/geom/gui/structure_gui.py"
EOF

chmod +x "$MACOS_DIR/geom-structure-studio"

echo "Created clickable macOS app:"
echo "  $APP_DIR"
echo
echo "Open it from Finder or run:"
echo "  open \"$APP_DIR\""

