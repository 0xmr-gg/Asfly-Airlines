#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export MPLCONFIGDIR="$SCRIPT_DIR/.cache/matplotlib"

mkdir -p "$MPLCONFIGDIR"
source "$SCRIPT_DIR/.venv/bin/activate"

echo "ASFLY environment active: $VIRTUAL_ENV"
echo "Use ROS 2 launch files or OpenCV-only perception/fusion nodes for runtime."
