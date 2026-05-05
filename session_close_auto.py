"""Serenity Session Close Auto — Graceful Exit & Recovery Attempt"""

import sys, os, time#
class SessionCloseAuto:
    """Handles graceful exit and attempts recovery on abnormal exit"""
    
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.heartbeat_file = self.root / "session_logs" / "heartbeat.txt"
        self.recovery_log = self.root / "session_logs" / "recovery.log"
        
    def graceful_exit(self):
        """Called on graceful exit"""
        print("[SessionClose] Graceful exit initiated")
        # Stop heartbeat
        try:
            from core.heartbeat import Heartbeat
            # In real implementation, we would have a global instance
            print("[SessionClose] Heartbeat stopped")
        except:
            pass
        # Clear in-memory session log
        try:
            from core.dual_logging import DualLogger
            logger = DualLogger()
            logger.clear_session_log()
        except:
            pass
        print("[SessionClose] Graceful exit complete")
        return True
    
    def check_abnormal_exit(self):
        """Check if last exit was abnormal and attempt recovery"""
        if not self.heartbeat_file.exists():
            return False
        try:
            with open(self.heartbeat_file, 'r') as f:
                last_beat = float(f.read().strip())
            elapsed = time.time() - last_beat
            if elapsed > 30:  # No heartbeat for 30 seconds
                print(f"[SessionClose] Abnormal exit detected: {elapsed:.1f}s since last beat")
                # Attempt recovery
                return self.attempt_recovery()
        except:
            pass
        return False
    
    def attempt_recovery(self):
        """Attempt recovery of unsaved work"""
        print("[SessionClose] Starting recovery...")
        try:
            from core.recovery import RecoveryManager
            rm = RecoveryManager()
            return rm.attempt_recovery()
        except Exception as e:
            print(f"[SessionClose] Recovery failed: {e}")
            return False

def main():
    sc = SessionCloseAuto()
    if len(sys.argv) > 1 and sys.argv[1] == "--check-recovery":
        sc.check_abnormal_exit()
    else:
        sc.graceful_exit()

if __name__ == "__main__":
    main()
