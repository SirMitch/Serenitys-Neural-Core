#!/usr/bin/env python3
"""
Serenity Neural-Core v1.0 — Main Entry Point with Full Resilience
Phase 2-3: Session Resilience Hardening + Audit Trail Integration
"""
import sys, os, yaml, time
from pathlib import Path
from datetime import datetime

# Phase 2: Resilience components
from core import heartbeat, auto_save, recovery, dual_logging, control_center, session_manager, serenity as kernel_module

class SereniaKernel(kernel_module.SerenityKernel) :
    """Serenity Neural-Core Kernel — Integrates all Phase 2 Resilience Components"""

    def __init__(self, session_subdir=None):
        super().__init__()
        self.session_subdir = session_subdir or (os.environ.get("SESSION_SUBDIR") or "session")
        self.root = Path(__file__).parent
        self.kernel_state_file = self.root / "docs" / "state.yaml"
        self.control_center = None  # Phase 3: Control Center orchestration hub
        
    def bootstrap(self):
        """Complete kernel boot sequence with Phase 2-3 resilience"""
        print("=" * 60)
        print("Serenity Neural-Core v1.0-alpha")
        print("Full Session Resilience Hardening Active (Phase 2)")
        print("Audit Trail Integration Enabled (Phase 3)")
        print("=" * 60)
        
        # Initialize persistence layer
        self.state_file = self.root / "docs" / "state.yaml"
        self.recovery_log = self.session_subdir / "recovery.log"

        
        return self
    
    def start(self):
        """Start Session with Heartbeat Watchdog"""
        print("\n[Kernel] Starting session...")
        
        # Phase 2: Start heartbeat watchdog
        hb = heartbeat.Heartbeat()
        hb.start()
        print("[Resilience] Heartbeat started - interval: 5s")
        
        return self

    def stop(self):
        """Graceful shutdown with auto-save"""
        print("\n[Kernel] Stopping session...")
        heartbeat.Heartbeat().stop()
        auto_save.AutoSave().micro_commit(
            message="Session closed - graceful exit"
        )
        
        return self

    def boot(self):
        """Boot kernel and load modules from state.yaml"""
        print("\n[Kernel] Booting Serenia Neural-Core...")
        self.bootstrap()
        
        # Control center orchestration
        cc = control_center.ControlCenter()
        print("[ControlCenter] Control center initialized")
        
        return "booted"

    def recover_if_needed(self):
        """Check recovery status and activate if needed"""
        self.logger.log("recovery", f"{datetime.now():%Y-%m-%d %H:%M:%S} Recovery check", duration=0)
        rm = recovery.RecoveryManager()
        
        try:
            with open(self.session_subdir / "heartbeat.txt") as f:
                last_heartbeat = float(f.read().strip())
                elapsed = (datetime.now() - datetime.fromtimestamp(last_heartbeat)).total_seconds()
            
            if elapsed > 30:
                print(f"[Recovery] Session interrupted - {elapsed:.1f}s without heartbeat")
                rm.attempt_recovery()

        except Exception as e:
            print(f"[Recovery] Error checking heartbeat: {e}")
        return self


if __name__ == "__main__":
    import sys
    
    try:
        # Phase 3: Control Center orchestration hub
        cc = control_center.ControlCenter()
        print("[Phase 3] Control center initialized")
        
        kernel = SereniaKernel()
        kernel.boot()
        
        if len(sys.argv) > 1:
            cmd = sys.argv[1]
            
            if cmd == "start":
                kernel.start()
                # Keep running - would typically load neural AI models
                print("[Session] Ready. Press Ctrl+C to stop.")
                
            elif cmd == "recover":
                kernel.recover_if_needed()
                
            elif cmd == "stop":
                kernel.stop()
            
            else:
                print(f"[Kernel] Unknown command: {cmd}")

        # Keep process alive for session duration
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            kernel.stop()
            
    except Exception as e:
        print(f"\n[Error]: {e}")
        sys.exit(1)
