"""Serenity Heartbeat — Session Interruption Detection"""

import sys, os, time, threading
from pathlib import Path

HEARTBEAT_INTERVAL = 5  # seconds between heartbeats
HEARTBEAT_FILE = Path(__file__).parent.parent.parent / "session_logs" / "heartbeat.txt"

class Heartbeat:
    """Detects abrupt session endings via heartbeat file updates"""
    
    def __init__(self):
        self.last_beat = time.time()
        self.running = False
        self.thread = None
        
    def start(self):
        """Start heartbeat thread"""
        self.running = True
        self.thread = threading.Thread(target=self._beat_loop, daemon=True)
        self.thread.start()
        print("[Heartbeat] Started")
        
    def _beat_loop(self):
        """Loop that updates heartbeat file periodically"""
        while self.running:
            self.last_beat = time.time()
            HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(HEARTBEAT_FILE, 'w') as f:
                f.write(str(self.last_beat))
            time.sleep(HEARTBEAT_INTERVAL)
            
    def stop(self):
        """Stop heartbeat"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[Heartbeat] Stopped")
        
    def check_recovery_needed(self):
        """Check if recovery is needed (session was interrupted)"""
        if not HEARTBEAT_FILE.exists():
            return False
        try:
            with open(HEARTBEAT_FILE, 'r') as f:
                last_time = float(f.read().strip())
            elapsed = time.time() - last_time
            # If last heartbeat was more than 30 seconds ago, session likely interrupted
            if elapsed > 30:
                print(f"[Heartbeat] Recovery needed: {elapsed:.1f}s since last beat")
                return True
        except:
            pass
        return False

def main():
    hb = Heartbeat()
    hb.start()
    try:
        time.sleep(20)
    except KeyboardInterrupt:
        hb.stop()

if __name__ == "__main__":
    main()
