#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-IDE}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$ROOT/thalarch-mode"
LOCK_TOOL="$ROOT/scripts/security/behavior_lock.py"

if [[ ! -d "$SOURCE" ]]; then
  echo "Plugin folder not found: $SOURCE" >&2
  exit 1
fi

PYTHON_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "Thalarch 1.0.0 requires Python 3.10+ for its hard anti-hallucination hooks." >&2
  echo "Install Python 3 and rerun this installer." >&2
  exit 1
fi
if [[ ! -f "$LOCK_TOOL" ]]; then
  echo "Behavior-lock tool not found: $LOCK_TOOL" >&2
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
  "$PYTHON_BIN" "$LOCK_TOOL" write "$destination"
  "$PYTHON_BIN" "$LOCK_TOOL" verify "$destination"
  echo "Installed Thalarch 1.0.0 for Antigravity IDE:"
  echo "  $destination"
  echo "Hard anti-hallucination evidence gates: ENABLED"
  echo "Behavior integrity lock: VERIFIED"
}

install_cli() {
  if ! command -v agy >/dev/null 2>&1; then
    echo "The 'agy' command was not found in PATH. Use IDE installation or install Antigravity CLI first." >&2
    exit 1
  fi

  local source_lock="$SOURCE/behavior-lock.json"
  if [[ -e "$source_lock" ]]; then
    echo "Refusing to overwrite existing source behavior-lock.json: $source_lock" >&2
    exit 1
  fi

  "$PYTHON_BIN" "$LOCK_TOOL" write "$SOURCE" --output "$source_lock"
  trap 'rm -f "$SOURCE/behavior-lock.json"' EXIT
  agy plugin install "$SOURCE"
  rm -f "$source_lock"
  trap - EXIT

  echo "Installed Thalarch 1.0.0 for Antigravity CLI."
  echo "Hard anti-hallucination evidence gates: ENABLED"
  echo "Behavior integrity lock: STAGED WITH PLUGIN"
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
