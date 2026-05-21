#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
pytest -v --tb=short --durations=0
