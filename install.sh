#!/bin/bash

set -e

ENV_NAME="geom_env"
GEOM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GEOM_VERSION="$(grep '^version' "$GEOM_ROOT/pyproject.toml" | head -1 | sed 's/version = "\(.*\)"/\1/')"

echo " Setting up GEOM with conda environment..."

# Check for conda
if ! command -v conda &> /dev/null; then
    echo ""
    echo " Conda was not found in your system."

    # Check if Miniconda is already installed
    if [[ -x "$HOME/miniconda/bin/conda" ]]; then
        echo " Detected Miniconda installed at $HOME/miniconda. Using it."
        export PATH="$HOME/miniconda/bin:$PATH"
        eval "$($HOME/miniconda/bin/conda shell.bash hook)"
    else
        echo " Conda is required to continue."
        echo " You can install it manually from:"
        echo "   Anaconda (full): https://www.anaconda.com/products/distribution"
        echo "   Miniconda (lightweight): https://docs.conda.io/en/latest/miniconda.html"
        echo
        read -p " Would you like to automatically install Miniconda now? (y/N): " INSTALL_MINICONDA
        if [[ "$INSTALL_MINICONDA" =~ ^[Yy]$ ]]; then
            OS_TYPE="$(uname -s)"
            ARCH="$(uname -m)"
            echo " Downloading Miniconda installer..."
            curl -L "https://repo.anaconda.com/miniconda/Miniconda3-latest-$([[ $OS_TYPE == "Darwin" ]] && echo "MacOSX" || echo "Linux")-${ARCH}.sh" -o miniconda.sh

            echo " Running Miniconda installer..."
            bash miniconda.sh -b -p "$HOME/miniconda"

            echo " Initializing Miniconda..."
            export PATH="$HOME/miniconda/bin:$PATH"
            eval "$($HOME/miniconda/bin/conda shell.bash hook)"
            "$HOME/miniconda/bin/conda" init
            source "$HOME/.bashrc"
        else
            echo " Installation aborted. Please install Conda manually and re-run this script."
            exit 1
        fi
    fi
fi

# Create conda environment if it doesn't exist
if conda info --envs | grep -q "^$ENV_NAME"; then
    echo " Conda environment '$ENV_NAME' already exists. Skipping creation."
else
    echo " Creating conda environment..."
    conda env create -f environment.yml
fi

echo " Installing Python package inside the conda environment..."
conda run -n "$ENV_NAME" python -m pip install --upgrade pip setuptools wheel
conda run -n "$ENV_NAME" python -m pip install gmsh==4.11.1
conda run -n "$ENV_NAME" python -m pip install --editable ".[ui]" --config-settings editable_mode=compat

# Set up shell config file
SHELL_RC="$HOME/.bashrc"
if [[ "$SHELL" == *"zsh" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"fish" ]]; then
    SHELL_RC="$HOME/.config/fish/config.fish"
fi

# Add conda init and geom_load if missing
if ! grep -q "conda initialize" "$SHELL_RC"; then
    echo "Adding conda init block to $SHELL_RC..."
    cat << 'EOF' >> "$SHELL_RC"
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('$HOME/miniconda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$HOME/miniconda/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniconda/etc/profile.d/conda.sh"
    else
        export PATH="$HOME/miniconda/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
EOF
fi

MAIN_PATH="$(realpath ./geom/ai_agent/desktop_chat_qt.py)"
GUI_PATH="$(realpath ./geom/gui/structure_gui.py)"
LOGO_PATH="$(realpath ./docs/_static/geom-logo-cloud.png)"
if [[ ! -f "$LOGO_PATH" ]]; then
    LOGO_PATH="$(realpath ./docs/_static/geom-logo-desktop.png)"
fi
ENV_PYTHON="$(conda run -n "$ENV_NAME" which python)"
echo "Installing geom_load shell helper in $SHELL_RC..."

touch "$SHELL_RC"

if grep -q "# >>> geom shell helpers >>>" "$SHELL_RC"; then
    awk '
        /# >>> geom shell helpers >>>/ {skip=1; next}
        /# <<< geom shell helpers <<</ {skip=0; next}
        skip == 0 {print}
    ' "$SHELL_RC" > "$SHELL_RC.tmp"
    mv "$SHELL_RC.tmp" "$SHELL_RC"
fi

if grep -Eq '^[[:space:]]*(function[[:space:]]+geom_load[[:space:]]*\{|geom_load[[:space:]]*\(\)[[:space:]]*\{)' "$SHELL_RC"; then
    echo " Removing stale geom_load function from $SHELL_RC..."
    awk '
        function brace_delta(line, stripped, opens, closes) {
            stripped = line
            opens = gsub(/\{/, "{", stripped)
            stripped = line
            closes = gsub(/\}/, "}", stripped)
            return opens - closes
        }
        /^[[:space:]]*(function[[:space:]]+geom_load[[:space:]]*\{|geom_load[[:space:]]*\(\)[[:space:]]*\{)/ {
            skip = 1
            depth = brace_delta($0)
            if (depth <= 0) {
                skip = 0
            }
            next
        }
        skip {
            depth += brace_delta($0)
            if (depth <= 0) {
                skip = 0
            }
            next
        }
        {print}
    ' "$SHELL_RC" > "$SHELL_RC.tmp"
    mv "$SHELL_RC.tmp" "$SHELL_RC"
fi

cat << EOF >> "$SHELL_RC"

# >>> geom shell helpers >>>
function geom_load {
    conda activate $ENV_NAME
    alias geom='$ENV_PYTHON -m geom'
    alias ai_geom='$ENV_PYTHON $MAIN_PATH'
    alias geomapp='$ENV_PYTHON $GUI_PATH'
}
# <<< geom shell helpers <<<
EOF

create_macos_geom_app() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        return 0
    fi

    APP_NAME="GEOM"
    APP_DIR="$HOME/Applications/${APP_NAME}.app"
    MACOS_DIR="$APP_DIR/Contents/MacOS"
    RESOURCES_DIR="$APP_DIR/Contents/Resources"
    EXECUTABLE="$MACOS_DIR/geomapp"
    ICON_NAME="geom-logo.icns"
    ICON_PATH="$RESOURCES_DIR/$ICON_NAME"

    mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

    cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>geomapp</string>
    <key>CFBundleIdentifier</key>
    <string>org.geom.app</string>
    <key>CFBundleName</key>
    <string>GEOM</string>
    <key>CFBundleDisplayName</key>
    <string>GEOM</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$GEOM_VERSION</string>
    <key>CFBundleIconFile</key>
    <string>geom-logo</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
EOF

    cat > "$EXECUTABLE" << EOF
#!/bin/bash
cd "$GEOM_ROOT"
exec "$ENV_PYTHON" "$GUI_PATH"
EOF
    chmod +x "$EXECUTABLE"

    if [[ -f "$LOGO_PATH" ]] && command -v sips &> /dev/null && command -v iconutil &> /dev/null; then
        ICONSET_DIR="$RESOURCES_DIR/geom-logo.iconset"
        rm -rf "$ICONSET_DIR"
        mkdir -p "$ICONSET_DIR"
        sips -z 16 16     "$LOGO_PATH" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
        sips -z 32 32     "$LOGO_PATH" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
        sips -z 32 32     "$LOGO_PATH" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
        sips -z 64 64     "$LOGO_PATH" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
        sips -z 128 128   "$LOGO_PATH" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
        sips -z 256 256   "$LOGO_PATH" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
        sips -z 256 256   "$LOGO_PATH" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
        sips -z 512 512   "$LOGO_PATH" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
        sips -z 512 512   "$LOGO_PATH" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
        cp "$LOGO_PATH" "$ICONSET_DIR/icon_512x512@2x.png"
        iconutil -c icns "$ICONSET_DIR" -o "$ICON_PATH" >/dev/null
        rm -rf "$ICONSET_DIR"
    elif [[ -f "$LOGO_PATH" ]]; then
        cp "$LOGO_PATH" "$RESOURCES_DIR/geom-logo.png"
    fi

    touch "$APP_DIR"
    echo " Created macOS GEOM app:"
    echo "   $APP_DIR"
}

create_macos_geom_app

create_linux_geom_app() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        return 0
    fi

    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons"
    DESKTOP_FILE="$DESKTOP_DIR/geom.desktop"

    mkdir -p "$DESKTOP_DIR" "$ICON_DIR"

    if [[ -f "$LOGO_PATH" ]]; then
        cp "$LOGO_PATH" "$ICON_DIR/geom-logo.png"
    fi

    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=GEOM
Comment=GEOM Structure Studio
Exec=$ENV_PYTHON $GUI_PATH
Icon=$ICON_DIR/geom-logo.png
Type=Application
Categories=Science;Education;
Terminal=false
StartupNotify=true
EOF

    chmod +x "$DESKTOP_FILE"

    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi

    echo " Created Linux desktop entry:"
    echo "   $DESKTOP_FILE"
}

create_linux_geom_app

create_uninstall_script() {
    cat > "$GEOM_ROOT/uninstall.sh" << 'UNINSTALL_EOF'
#!/bin/bash

set -e

ENV_NAME="geom_env"

echo " Uninstalling GEOM helpers..."

SHELL_RC="$HOME/.bashrc"
if [[ "$SHELL" == *"zsh" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"fish" ]]; then
    SHELL_RC="$HOME/.config/fish/config.fish"
fi

remove_geom_load_function() {
    local rc_file="$1"
    if [[ ! -f "$rc_file" ]]; then
        return 0
    fi

    if grep -q "# >>> geom shell helpers >>>" "$rc_file"; then
        awk '
            /# >>> geom shell helpers >>>/ {skip=1; next}
            /# <<< geom shell helpers <<</ {skip=0; next}
            skip == 0 {print}
        ' "$rc_file" > "$rc_file.tmp"
        mv "$rc_file.tmp" "$rc_file"
    fi

    if grep -Eq '^[[:space:]]*(function[[:space:]]+geom_load[[:space:]]*\{|geom_load[[:space:]]*\(\)[[:space:]]*\{)' "$rc_file"; then
        awk '
            function brace_delta(line, stripped, opens, closes) {
                stripped = line
                opens = gsub(/\{/, "{", stripped)
                stripped = line
                closes = gsub(/\}/, "}", stripped)
                return opens - closes
            }
            /^[[:space:]]*(function[[:space:]]+geom_load[[:space:]]*\{|geom_load[[:space:]]*\(\)[[:space:]]*\{)/ {
                skip = 1
                depth = brace_delta($0)
                if (depth <= 0) {
                    skip = 0
                }
                next
            }
            skip {
                depth += brace_delta($0)
                if (depth <= 0) {
                    skip = 0
                }
                next
            }
            {print}
        ' "$rc_file" > "$rc_file.tmp"
        mv "$rc_file.tmp" "$rc_file"
    fi
}

remove_geom_load_function "$SHELL_RC"
echo " Removed GEOM shell helpers from $SHELL_RC if present."

if [[ "$(uname -s)" == "Darwin" ]]; then
    APP_DIR="$HOME/Applications/GEOM.app"
    if [[ -d "$APP_DIR" ]]; then
        rm -rf "$APP_DIR"
        echo " Removed $APP_DIR"
    fi
fi

if [[ "$(uname -s)" == "Linux" ]]; then
    DESKTOP_FILE="$HOME/.local/share/applications/geom.desktop"
    ICON_FILE="$HOME/.local/share/icons/geom-logo.png"
    if [[ -f "$DESKTOP_FILE" ]]; then
        rm -f "$DESKTOP_FILE"
        echo " Removed $DESKTOP_FILE"
    fi
    if [[ -f "$ICON_FILE" ]]; then
        rm -f "$ICON_FILE"
        echo " Removed $ICON_FILE"
    fi
fi

if command -v conda &> /dev/null; then
    if conda info --envs | grep -q "^$ENV_NAME"; then
        read -p " Remove conda environment '$ENV_NAME'? (y/N): " REMOVE_ENV
        if [[ "$REMOVE_ENV" =~ ^[Yy]$ ]]; then
            conda env remove -n "$ENV_NAME" -y
            echo " Removed conda environment '$ENV_NAME'."
        else
            echo " Kept conda environment '$ENV_NAME'."
        fi
    fi
fi

echo " "
echo " Uninstall complete."
echo " Reload your shell with:"
echo "   source $SHELL_RC"
UNINSTALL_EOF
    chmod +x "$GEOM_ROOT/uninstall.sh"
}

echo " Running tests..."
echo " Running GEOM command tests..."
conda run -n "$ENV_NAME" bash ./geom/tests/run_all_tests.sh
echo " Running GEOM GUI tests..."
conda run -n "$ENV_NAME" bash ./geom/gui/tests/run_gui_tests.sh

create_uninstall_script

echo "  Installation complete!"
echo " "
echo "  To uninstall GEOM helpers and the desktop app:"
echo "     ./uninstall.sh"
echo " "
echo "  Next steps"
echo "  ----------"
echo " "
echo "  1. Reload your shell:"
echo "     source $SHELL_RC"
echo " "
echo "  2. Load the GEOM environment:"
echo "     geom_load"
echo " "
echo "  3. Open the GEOM App:"
echo "     geomapp"
if [[ "$(uname -s)" == "Darwin" ]]; then
echo " "
echo "  You can also open GEOM from Spotlight/Finder:"
echo "     ~/Applications/GEOM.app"
fi
if [[ "$(uname -s)" == "Linux" ]]; then
echo " "
echo "  You can also open GEOM from your desktop application launcher."
fi
echo " "
echo "  Check GEOM options using: geom -h"
echo " "
