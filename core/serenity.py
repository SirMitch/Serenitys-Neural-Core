"""Serenity Neural-Core — Main Entry Point / Kernel"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

class SerenityKernel:
    def __init__(self):
        self.session_id = "KERNEL_" + Path(__file__).stem
        print(f"[Serenity Kernel] Initialized: {self.session_id}")
        
    def boot(self):
        from core.control_center import ControlCenter
        cc = ControlCenter()
        print("Serenity Neural-Core v1.0-alpha — Kernel Active")

def main():
    kernel = SerenityKernel()
    kernel.boot()

if __name__ == "__main__":
    main()
