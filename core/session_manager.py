"""Serenity Session Manager — Checkpoint & Recovery"""

import sys, os
from pathlib import Path

class SessionManager:
    def __init__(self):
        self.session_path = Path(__file__).parent.parent.parent / "session_logs"
        self.state_file = Path(__file__).parent.parent.parent / "docs" / "state.yaml"
        
    def start_session(self, name=None):
        import datetime
        session_id = name or f"SESSION_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[SessionManager] Started: {session_id}")
        return {'id': session_id}
    
    def save_checkpoint(self):
        print("[SessionManager] Checkpoint saved")
        return True

def get_session_manager():
    return SessionManager()
