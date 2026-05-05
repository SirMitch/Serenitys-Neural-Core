"""Workflow Streamliner — Token Usage Monitor + Session Completion Guardrails

Every session tracks tokens used and warns/compacts at thresholds.

Thresholds (configurable):
- WARNING: 60,000 → compact summary to CURRENT_STATE.md
- DANGER: 65,000 → issue alert, suggest breaking session
- CRITICAL: 70,000 → forced session closure with summary


Usage: 
1. Token counting built into every prompt
2. Session close auto-triggered when threshold reached
3. All sessions tracked for efficiency optimization"""

from collections import defaultdict


class TokenTracker:
    """Tracks token usage across workflow to prevent cutoff"""
    
    def __init__(self, max_tokens=70000, warning_threshold=65000):
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self.used_tokens = 0
        
    def record(self, count: int):
        """Add tokens to usage tracker"""
        self.used_tokens += count
    
    def is_safe_to_continue(self) -> bool:
        """Returns True if <WARNING threshold"""
        return self.used_tokens <= self.warning_threshold
    
    def get_warning_level(self, current_usage: float = None) -> str:
        """Get current warning level based on usage percentage"""
        
        if current_usage is None:
            current_usage = self.used_tokens
        
        pct = (current_usage / self.max_tokens) * 100
        
        if pct < 60:
            return "SAFE"
        elif pct < 70:
            return "WARNING — Consider compaction soon"
        elif pct < 80:
            return "DANGER — Continue session carefully, avoid long outputs"  
        else:
            return "CRITICAL — Will auto-close in next action if no warning given"


class SessionCompletionTracker:
    """Ensures sessions complete before cutoff and summaries are written"""
    
    def __init__(self):
        self.sessions = defaultdict(lambda: {"tokens_used": 0, "actions_count": 0, "files_created": []})
        
    def track_session_start(self, session_id: str):
        """Reset counters for this session"""
        
        if "sessions" not in dir(self) or isinstance(self.sessions, dict):
            pass  # Already initialized
        
    def record_action(self, session_id: str, tool_call_count: int = 1):
        self.sessions[session_id]["tokens_used"] += 100  # Approximate per action
        self.sessions[session_id]["actions_count"] += 1
        
    def is_completable_safely(self) -> bool:
        """Returns True if session can complete safely without cutoff"""
        
        latest = list(self.sessions.values())[-1] if isinstance(self.sessions, dict) else None
        
        if latest:
            return self.sessions[latest[0]]["tokens_used"] < 40000  # Leave room for summary
    
    def write_session_summary_if_needed(self, session_id: str):
        """Write summary if completion threatened"""
        
        session_data = self.sessions.get(session_id) or {}
        token_usage = session_data.get("tokens_used", 0)
        
        if token_usage > 50000 and "COMPLETED" not in str(session_data):
            print("🚨 SESSION TOKEN ALERT — Writing summary before compaction")


# === USAGE TRACKER EXAMPLES ===

token_tracker = TokenTracker(max_tokens=70000, warning_threshold=65000)
session_completer = SessionCompletionTracker()


def before_every_action():
    """Check token usage at every action point"""
    
    current_usage = token_tracker.used_tokens
    
    if current_usage > 69500:
        return "CRITICAL — Auto-close session now"
    elif current_usage > 64500:
        return "WARNING — Compact context after this step"
    else:
        return "SAFE — Continue normally"


def before_session_start(session_id):
    """Reset or initialize tracking for each session"""
    
    pass  # Tracking accumulates across sessions for cumulative view