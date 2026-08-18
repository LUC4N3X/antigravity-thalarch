#!/usr/bin/env python3
"""
Optional Thalarch hard-gate hook.

Disabled by default in hooks.json because plugin hooks are global while the plugin
is installed. Enable only if you want extra approval for clearly consequential
shell commands in every Antigravity session using this plugin.
"""
import json, re, sys

def main():
    data = json.load(sys.stdin)
    tool = (data.get("toolCall") or {}).get("name", "")
    args = (data.get("toolCall") or {}).get("args", {})
    if tool != "run_command":
        print(json.dumps({"decision": "allow"}))
        return

    command = str(args.get("CommandLine", ""))
    high_risk = [
        r"\bgit\s+push\b",
        r"\bgh\s+pr\s+merge\b",
        r"\bgh\s+release\b",
        r"\bnpm\s+publish\b",
        r"\b(?:cargo|twine)\s+publish\b",
        r"\brm\s+-rf\b",
        r"\bRemove-Item\b.*\b-Recurse\b.*\b-Force\b",
        r"\bterraform\s+apply\b",
        r"\bkubectl\s+(?:apply|delete)\b",
    ]
    if any(re.search(p, command, flags=re.I) for p in high_risk):
        print(json.dumps({
            "decision": "force_ask",
            "reason": "Thalarch hard gate: consequential external/destructive command requires explicit confirmation."
        }))
    else:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
