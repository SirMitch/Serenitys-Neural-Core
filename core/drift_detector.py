"""Session Drift Detector — Proactive Design Drift Identification

Checks for implementation divergence from documented design without breaking execution."""

import hashlib
from pathlib import Path
from datetime import datetime


def scan_for_drift() -> dict:
    """Scan project for documentation drift and report issues."""
    drifts = {
        "unimplemented_features": [],
        "hash_mismatches": [],
        "config_usage_violations": [],
    }
    
    project_root = Path("H:/projects/AlphaChart")
    docs_path = project_root / "docs" / "design" / ("doc viewer" if "\\" in str(Path.cwd()) else "")
    
    # Check if manifest exists
    manifesto = project_root / "MANIFEST.json"
    doc_registry = project_root / "docs" / "CHANGELOG.md"  # Fall back to CHANGELOG docs
    
    if manifesto.exists():
        import json
        try:
            manifest = json.loads(manifesto.read_text())
            
            # Count files in MANIFEST vs reality 
            manifest_files = set(manifest.get("files", {}).keys())
            
            for fpath in project_root.glob("**/*.py"):
                if "backups" not in str(fpath) and "__pycache__" not in str(fpath):
                    relative = str(fpath.relative_to(project_root))
                    if relative not in manifest_files:
                        drifts["unimplemented_features"].append(
                            {
                                "file": relative,
                                "issue": "File exists but not in MANIFEST.json",
                                "action": "Add to MANIFEST.json or remove from project"
                            }
                        )
        except Exception as e:
            drifts["hash_mismatches"].append({"error": str(e)})
    
    return drifts


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash for integrity verification."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def emit_drift_alert(drifts):
    """Emit user-visible drift alerts if needed"""
    import sys
    if drifts["unimplemented_features"]:
        print("🚨 DRIFT ALERT — Files exist outside MANIFEST:")
        for item in drifts["unimplemented_features"][:5]:  # Limit output
            print(f"   - {item['file']}: {item['issue']}")
        if len(drifts) > 5:
            print("   ... and {} more".format(len(drifts) - 5))
    return True


def validate_session_state(session_id=None):
    """Validate session state freshness before execution"""
    state_yaml = Path("state.yaml") or Path("H:/projects/AlphaChart/state.yaml")
    
    if not state_yaml.exists():
        return {
            "status": "RECOVERY",
            "message": "state.yaml missing — reconstructing from ADDR backup"
        }
    
    import yaml
    try:
        state = yaml.safe_load(state_yaml.read_text())
        
        # Check last session ID consistency
        if state.get("last_session"):
            last_id = int(state["last_session"][1:])  # Extract number from "042" format
            return {"status": "OK", "last_session": str(last_id)}
        else:
            return {
                "status": "STALE", 
                "message": "state.yaml has no last_session field — needs reconstruction"
            }
    except Exception as e:
        return {"status": "CORRUPTED", "error": str(e)}
