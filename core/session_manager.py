"""Serenity Session Manager — Dev Sessions & Learning Sessions with Checkpoint/Recovery"""
import sys, os, json
from pathlib import Path
from datetime import datetime

class SessionManager:
    def __init__(self):
        self.project_path = Path(__file__).parent.parent.parent
        self.session_logs_dir = self.project_path / "session_logs"
        self.state_file = self.project_path / "docs" / "state.yaml"
        
        # Ensure directories exist
        self.session_logs_dir.mkdir(parents=True, exist_ok=True)
    
    def start_dev_session(self):
        """Start a development/coding session (triggers when user is writing code)"""
        return self._start_session("DEV", "Development Session")
    
    def start_learning_session(self):
        """Start a learning/documentation session (triggers when analyzing docs/design)"""
        return self._start_session("LEARNING", "Learning Session")
    
    def _start_session(self, type_, label):
        """Generic session starter with tracking"""
        timestamp = datetime.now()
        session_id = f"{type_}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Log session start
        self._log_session_event(session_id, "start")
        print(f"[{label}] Started: {session_id}")
        
        return {'id': session_id, 'type': type_, 'timestamp': timestamp.isoformat()}
    def complete_session(self, session_id):
        """Trigger: Called when session completes - logs completion and saves checkpoint"""
        self._log_session_event(session_id, "complete")
        print(f"[{session_id}] Completed")
        return self.save_checkpoint()
    
    def save_checkpoint(self):
        """Trigger: Called on every action or before major operations - saves state checkpoint"""
        import yaml
        try:
            # Load current state if exists
            with open(self.state_file, 'r') as f:
                current_state = yaml.safe_load(f.read())
        except (FileNotFoundError, yaml.YamLDaemonError):
            current_state = {}
        
        # Update checkpoint timestamp
        current_state['last_checkpoint'] = datetime.now().isoformat()
        current_state['session_active'] = True
        
        # Save updated state
        with open(self.state_file, 'w') as f:
            yaml.safe_dump(current_state, f)
        
        print(f"[Checkpoint] Saved at {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        return True
    
    def _log_session_event(self, session_id, event_type):
        """Log all session events to session_logs for tracking and recovery"""
        log_file = self.session_logs_dir / f"{session_id}_events.json"
        
        # Load existing events or create new list
        try:
            with open(log_file, 'r') as f:
                events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            events = []
        
        # Add new event
        events.append({
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'session_id': session_id
        })
        
        # Save updated events
        with open(log_file, 'w') as f:
            json.dump(events, f)
    
def get_session_manager():
    return SessionManager()
