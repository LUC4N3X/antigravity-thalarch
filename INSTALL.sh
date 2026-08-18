#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-IDE}"
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/thalarch-mode"

if [[ ! -d "$SOURCE" ]]; then
  echo "Plugin folder not found: $SOURCE" >&2
  exit 1
fi

install_ide() {
  local plugin_root="$HOME/.gemini/config/plugins"
  local destination="$plugin_root/thalarch-mode"
  mkdir -p "$plugin_root"

  if [[ -e "$destination" ]]; then
    local stamp
    stamp="$(date +%Y%m%d-%H%M%S)"
    local backup="${destination}.backup-${stamp}"
    mv "$destination" "$backup"
    echo "Existing Thalarch installation backed up to: $backup"
  fi

  cp -R "$SOURCE" "$destination"
  echo "Installed Thalarch 1.0.0 for Antigravity IDE:"
  echo "  $destination"
}

install_cli() {
  if ! command -v agy >/dev/null 2>&1; then
    echo "The 'agy' command was not found in PATH. Use IDE installation or install Antigravity CLI first." >&2
    exit 1
  fi

  agy plugin install "$SOURCE"
  echo "Installed Thalarch 1.0.0 for Antigravity CLI."
  agy plugin list
}

case "${TARGET^^}" in
  IDE) install_ide ;;
  CLI) install_cli ;;
  BOTH) install_ide; install_cli ;;
  *) echo "Usage: ./INSTALL.sh [IDE|CLI|Both]" >&2; exit 2 ;;
esac

echo
echo "Next:"
echo "1. Restart/reload Antigravity."
echo "2. Select 'thalarch-orchestrator' as the primary agent."
echo "3. Ask: 'Use Thalarch for this task.'"
