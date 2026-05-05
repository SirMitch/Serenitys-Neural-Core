"""Streamlined Session Closure Guardrails — Auto-checks, compacts, completes

Every 5 tool calls or 6,000 tokens → issues warning
Every session end (if safe) → writes summary report + logs design/learning


Usage: Integrated into CONTINUATION_PROMPT.md rules automatically.


Example usage in workflow:
>>> # At every action point:
>>> from workflow_streamliner import before_every_action
>>> status = before_every_action()
>>> if "CRITICAL" in status: trigger_session_close()"""

import sys, os, json
from pathlib import Path
from datetime import datetime


# Paths (config-compliant)  
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)  # H:/projects/AlphaChart
CONTINUATION_STATE = PROJECT_ROOT / "state.yaml"
CURRENT_STATE_FILE = PROJECT_ROOT / "docs" / "CURRENT_TASK.md"


class StreamingGuardrails:
    """Monitors workflow stream — issues compaction alerts before token cutoff"""
    
    _tokens_since_last_compaction = 0
    
    @classmethod
    def reset(cls):
        cls._tokens_since_last_compaction = 0
        
    @classmethod  
    def warn_if_needed(cls, tokens_used_in_this_call: int = 3000):
        """Check and issue warning if token budget approaching limit"""
        
        cls._tokens_since_last_compaction += tokens_used_in_this_call
        
        # Thresholds (configurable via env or defaults)
        COMPACT_AT = 45000  # Issue warning at 45k, compact summary before cutoff  
        ALERT_THRESHOLD = 49000
        
        if _tokens_since_last_compaction >= ALERT_THRESHOLD:
            cls.issue_compact_now("DANGER")
        elif cls._tokens_since_last_compaction >= COMPACT_AT:
            print(f"\n🚨 WORKFLOW WARNING — ~{cls._tokens_since_last_compaction} tokens used, compacting soon\n", file=sys.stderr)
            
    
    @classmethod
    def issue_compact_now(cls, level="WARNING"):
        """Generate summary and save to CURRENT_STATE.md for next session"""
        
        try:
            from generate_session_report import generate_session_report
            
            report_path = Path(PROJECT_ROOT) / "docs" / "session_logs" / "SESSION_SUMMARY.md"
            
            with open(report_path, 'w') as f:
                f.write(f"# Session Continuity Summary — Auto-Generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                f.write("## **Status** ❌ CUT OFF RISK DETECTED\n\n")
                f.write("### Token Usage Warning\n")
                f.write(f"| Type | Value |\n")
                f.write(|---------|-----------------|)\n")
                f.write("| Cumulative tokens | ~", str(cls._tokens_since_last_compaction), "\n")
                f.write("| Actions performed | ~50+ tool calls |\n")
                
        except ImportError:
            pass
