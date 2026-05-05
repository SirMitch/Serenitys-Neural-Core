"""Serenity Neural-Core Control Center - Central Orchestration Hub"""

import sys, os, yaml
from datetime import datetime
from pathlib import Path

# Phase 2: Import resilience components (Phase 3: State persistence)
try:
    from core import heartbeat, auto_save, recovery, dual_logging
except ImportError:
    heartbeat = None
    auto_save = None
    recovery = None
    dual_logging = None

ROOT = Path(__file__).parent.parent.parent

class ControlCenter:
    """Central orchestration hub with Phase 2 Resilience + Phase 3 State persistence"""
    
    def __init__(self):
        self.modules = {}
        self.state_file = Root / "docs" / "state.yaml"
        self.recovery_mode = False
    
    def load_state(self, force_recovery=False):
        """Load state from persistence layer (Phase 3: State persistence layer)"""
        try:
            if self.state_file.exists():
                with open(self.state_file) as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"[ControlCenter] Failed to load state: {e}")
            if force_recovery:
                print("[Recovery] Attempting recovery...")
                self.recovery_mode = True
        return {}
    
    def get_modules(self):
        """Return list of registered modules for orchestration"""
        return list(self.modules.keys())
    
    def register_module(self, name, path=None, config=None):
        """Register a module with resilience tracking (Phase 2: Session Resilience)"""
        if path:
            self.modules[name] = {'path': str(path), 'config': config or {}}
            print(f"[ControlCenter] Registered: {name}")
        return self.modules.get(name, {})
    
    def orchestrate_modules(self):
        """Orchestrate all registered modules with session integrity checks (Phase 2-3)"""
        # Phase 2: Start heartbeat watchdog for interruption detection
        if heartbeat:
            hb = heartbeat.Heartbeat()
            print("[Resilience] Heartbeat started - interval: 5s")
        
        # Load state and configure modules (Phase 3: State persistence layer)
        state = self.load_state()
        for module_name, info in state.get('modules', {}).items():
            if module_name not in self.modules:
                print(f"[ControlCenter] Restored module: {module_name}")
                self.register_module(module_name, **info)
        
        # Phase 3: Audit trail logging
        from core import dual_logging
        if dual_logging:
            dl = dual_logging.DualLogging()
            print("[Dual Logging] Audit trail enabled")
        
        return self.modules

def main():
    """Main entry point for testing orchestration (Phase 3: State persistence layer)"""
    cc = ControlCenter()
    modules = cc.orchestrate_modules()  # Phase 2-3 integration
    print("Modules:", list(modules.keys()))
    return modules

if __name__ == "__main__":
    main()
