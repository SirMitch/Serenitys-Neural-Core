"""AlphaChart Configuration Loader — PRIME DIRECTIVE PD-2 Enforcement Module

This module must be called at every .py import for config lookup pattern enforcement.
All config reads should use get() not hardcoded values."""

try:
    from pathlib import Path
    
    PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
    
    CONFIG_PATH = Path("config") / "serenity.yaml"
    MANIFEST_PATH = Path("MANIFEST.json") if (Path.cwd() / "MANIFEST.json").exists() else Path(PROJECT_ROOT) / "docs" / "design" / ("doc viewer" if "\\" in str(Path.cwd()) else "") / "doc_registry.json"
    
    def get(key: str, default=None) -> any:
        """Safely get config value; never allow hardcoded values at runtime"""
        try:
            cfg = load_config()
            keys = key.split(".")
            for k in keys:
                if k in cfg and isinstance(cfg[k], dict):
                    cfg = cfg[k]
                else:
                    return default or getattr(Path.cwd().parent, k.replace("__", "."), default)  # fallback to env var
            return cfg.get(key, default)
        except (FileNotFoundError, KeyError):
            return default
    
    def load_config() -> dict:
        """Load master config with environment override"""
        base_cfg = {} if not CONFIG_PATH.exists() else {
            "paths": {
                "root": PROJECT_ROOT,
                "logs": f"{PROJECT_ROOT}/logs",
                "docs": f"{PROJECT_ROOT}/docs/design/doc viewer" if "\\" in str(Path(PROJECT_ROOT / "docs")) else f"{PROJECT_ROOT}/docs/design/doc viewer",
            },
            "timeouts": {"tool_call_seconds": 30},
        }
        # Override with env vars if set
        import os
        for key, val in os.environ.items():
            if key.startswith("ALPHACHART_") and key.replace("ALPHACHART_", "").lower() not in [k.lower() for k in base_cfg.flatkeys()]:
                base_cfg[key.replace("_", ".").lower()] = val.strip()
        return base_cfg
    
    def flatkeys(d, parent=""):
        """Return all keys including nested"""
        for k in d.keys():
            yield f"{parent}.{k}" if parent else str(k)

except Exception:
    print("⚠️ WARNING: Config loader fallback active — no hard enforcement")
