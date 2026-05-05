"""Deterministic Session Trigger System — DEV/Learning Pass Auto-Triggers via ADDR"""
import json
from pathlib import Path
from datetime import datetime

class DeterministicSessionTrigger:
    """Automatically triggers dev_sessions and learning_sessions based on deterministic rules."""
    
    def __init__(self, addr_file="docs/design doc viewer/ADDR.md"):
        self.addr_file = Path(addr_file)
        # Session tracking state (loaded from ADDR when integrated)
        self.state = {
            'session_tracking': {
                'current_session_id': 0,
                'dev_pass_last_run': None,
                'learning_pass_last_run': None,
                'learning_collect_buffer': []
            }
        }
    
    def start_session(self, session_type="DEV"):
        """Start a new session with deterministic trigger logic."""
        # Increment session ID
        self.state['session_tracking']['current_session_id'] += 1
        current_id = self.state['session_tracking']['current_session_id']
        
        # Always run LEARNING Collection (triggers every session)
        self._collect_learning_data(session_type)
        
        # Check if passes should be triggered after this session
        triggers = {}
        
        # DEV Pass trigger: every 2 sessions minimum
        last_dev = self.state['session_tracking']['dev_pass_last_run']
        if last_dev is None or (current_id - last_dev) >= 2:
            triggers['DEV_PASS'] = True
            self.state['session_tracking']['dev_pass_last_run'] = current_id
        
        # Learning Pass trigger: every 3 sessions with buffer check
        last_learning = self.state['session_tracking']['learning_pass_last_run']
        buffer = self.state['session_tracking']['learning_collect_buffer']
        if last_learning is None or (current_id - last_learning) >= 3:
            triggers['LEARNING_PASS'] = len(buffer) > 0
        
        return {
            'session_id': current_id,
            'triggers': triggers,
            'status': f"Session {current_id} started ({session_type})"
        }
    
    def _collect_learning_data(self, session_type):
        """Collect learning data for buffer (LEARNING Collection - always triggered)."""
        # In real implementation: collect decisions, errors, inefficiencies
        self.state['session_tracking']['learning_collect_buffer'].append({
            'session_id': self.state['session_tracking']['current_session_id'],
            'type': session_type,
            'collected_at': datetime.now().isoformat(),
            # Would include actual learning data in real implementation
        })
    
    def execute_pass(self, pass_type):
        """Execute the specified pass (DEV_PASS or LEARNING_PASS)."""
        if pass_type == 'DEV_PASS':
            return self._execute_dev_pass()
        elif pass_type == 'LEARNING_PASS':
            return self._execute_learning_pass()
        raise ValueError(f"Unknown pass type: {pass_type}")
    
    def _execute_dev_pass(self):
        """Execute architectural work for DEV Pass."""
        # Placeholder - in real implementation would analyze and update design
        print(f"[DEV Pass] Executing at session {self.state['session_tracking']['current_session_id']}")
        return {'status': 'Dev pass completed'}
    
    def _execute_learning_pass(self):
        """Execute learning analysis for Learning Pass."""
        buffer = self.state['session_tracking']['learning_collect_buffer']
        if not buffer:
            print("[Learning Pass] No data collected yet")
            return {'status': 'No data to analyze'}
        
        # Placeholder - would analyze buffer and update memory/system
        print(f"[Learning Pass] Analyzing {len(buffer)} collected sessions")
        self.state['session_tracking']['learning_collect_buffer'] = []
        return {'status': f'Analyzed {len(buffer)} session entries'}
    
    def get_state(self):
        """Return current session tracking state."""
        return self.state

# Simple demo mode - can be integrated with ADDR system
def main():
    """Demo: Show how deterministic triggers work across sessions."""
    trigger = DeterministicSessionTrigger()
    
    print("=== Deterministic Session Trigger Demo ===")
    for i in range(5):
        result = trigger.start_session("DEV")
        print(f"\n--- {result['status']} ---")
        print(f"Current session ID: {result['session_id']}")
        
        # Check and execute triggers
        for pass_type, should_run in result['triggers'].items():
            if should_run:
                print(f"\nTriggering {pass_type}...")
                trigger.execute_pass(pass_type)
    
    print("\n=== Final State ===")
    print(json.dumps(trigger.get_state(), indent=2))

if __name__ == "__main__":
    main()
