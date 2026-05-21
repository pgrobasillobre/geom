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
