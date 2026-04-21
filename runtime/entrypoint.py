"""
Entrypoint dual-mode de Atlas.
MODE=slack_listener  → bot Slack (producción / ECS)
MODE=cli             → prompt único desde stdin (smoke test / dev)
"""
import os
import sys
import importlib

MODE = os.getenv("MODE", "slack_listener")

MODES = {
    "slack_listener": ("runtime.tools.slack_bot", "main"),
    "cli":            ("runtime.tools.cli_runner", "main"),
}

if MODE not in MODES:
    print(f"[entrypoint] ERROR: MODE '{MODE}' no reconocido. Válidos: {list(MODES.keys())}")
    sys.exit(1)

module_path, func_name = MODES[MODE]
module = importlib.import_module(module_path)
print(f"[entrypoint] Arrancando modo: {MODE}")
getattr(module, func_name)()
