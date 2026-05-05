"""Serenity Dual Logging — In-Memory Session Log + Persistent Recovery Log"""

import sys, time#
class DualLogger:
    """Maintains both in-memory session log and persistent append-only recovery log"""
    
    def __init__(self):
        self.root = Path(__file__).parent.parent.parent
        self.session_log = []  # In-memory
        self.recovery_log = self.root / "session_logs" / "recovery.log"
        self.recovery_log.parent.mkdir(parents=True, exist_ok=True)
        
    def log(self, event_type, message, **kwargs):
        """Log an event both in-memory and to persistent recovery log"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        entry = {
            'timestamp': timestamp,
            'type': event_type,
            'message': message,
            **kwargs
        }
        # In-memory log
        self.session_log.append(entry)
        # Persistent append-only recovery log
        with open(self.recovery_log, 'a') as f:
            f.write(f"{timestamp} [{event_type}] {message} {kwargs}\n")
        return entry
    
    def get_session_log(self):
        """Return in-memory session log"""
        return self.session_log
    
    def get_recovery_log(self, last_n=100):
        """Return last N lines of recovery log"""
        try:
            with open(self.recovery_log, 'r') as f:
                lines = f.readlines()
            return lines[-last_n:] if last_n else lines
        except:
            return []
    
    def clear_session_log(self):
        """Clear in-memory log (call on graceful exit)"""
        self.session_log.clear()
        self.log('session', 'Session log cleared after graceful exit')

def main():
    logger = DualLogger()
    logger.log('test', 'Dual logging active')
    print(logger.get_recovery_log(5))

if __name__ == "__main__":
    main()
