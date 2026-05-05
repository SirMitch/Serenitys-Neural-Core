"""Serenity Neural-Core Control Center - Central Orchestration Hub"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

class ControlCenter:
    def __init__(self):
        self.modules = {}
        self.state_file = ROOT / "docs" / "state.yaml"
        
    def register_module(self, name, path, config=None):
        self.modules[name] = {'path': str(path), 'config': config or {}}
        print(f"[ControlCenter] Registered: {name}")
        
    def load_state(self):
        import yaml
        if self.state_file.exists():
            with open(self.state_file) as f:
                return yaml.safe_load(f)
        return {}
    
    def get_modules(self):
        return list(self.modules.keys())

def main():
    cc = ControlCenter()
    print("Serenity Control Center Active")
    print("Modules:", cc.get_modules())

if __name__ == "__main__":
    main()
