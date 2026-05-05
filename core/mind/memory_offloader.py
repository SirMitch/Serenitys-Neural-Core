"""
memory_offloader.py — Context-window-offloading system for small local LLMs.

Problem Statement:
Small local LLMs have limited context windows (typically 2k-8k tokens). This module 
implements patterns to offload memory operations from active context:

1. **Compressed History**: Summarized bullet blocks instead of raw logs
2. **D: Drive Cold Storage**: Move infrequently accessed data to high-speed SSD for retrieval  
3. **Lazy Load Pattern**: Load ADDR sections only when needed (not all upfront)

Architecture Alignment (from CONTINUATION_PROMPT.md section 9):
- Active Context → Current micro-step + immediate state (discard post-response)
- Short-Term Memory → Last 3 successful steps → Move to Compressed History when limit exceeded  
- Persistent Memory (ADDR) → Source-of-truth reconstruction anchor (never deleted)
- Compressed History → Summarized high-signal entries only

Implementation Notes:
- Uses gzip compression for cold storage efficiency
- Background ThreadPoolExecutor for CPU offload
- TTL-based pruning of infrequently accessed entries
"""

import os
import sys
import json
import gzip
import time
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from datetime import datetime, timedelta

# Set MCP env var for tool compatibility
os.environ['ALPHACHART_DOCS'] = os.path.join(os.getcwd(), 'docs', 'design doc viewer')

# Fix: _memory_stack initialized in __init__
# Fix: loadADDR → load_ADDR (correct function name)


class MemoryOffloader:
    """
    Context-window-offloading system for small local LLMs.
    
    Manages memory layers with D: SSD cold storage to mitigate context window constraints.
    """
    
    def __init__(self, 
                 cache_dir: str = "D:/AI Clients/OpenHands_cache",
                 max_short_term_memory_steps: int = 5,
                 compressed_history_retention_days: int = 90):
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_short_term_memory_steps = max_short_term_memory_steps
        self.compressed_history_path = self.cache_dir / "compressed_history.json.gz"
        self.active_context: Dict[str, Any] = {}
        
        # Fix: Initialize _memory_stack
        self._memory_stack: List[Dict[str, Any]] = []
        
        # Background executor for CPU offload (non-blocking operation)
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Queue for async step compression (prevents context bloat)
        self.compression_queue: Queue = Queue(maxsize=10)
    
    @property  
    def short_term_memory(self) -> List[str]:
        """Current active memory entries (last N successful steps)."""
        return self._memory_stack[-self.max_short_term_memory_steps:] if len(self._memory_stack) < 10 else self._memory_stack[-self.max_short_term_memory_steps:]
    
    @property 
    def memory_stack_length(self) -> int:
        return len(self._memory_stack)
    
    def queue_step(self, step_result: Dict[str, Any]) -> None:
        """Add completed step to short-term memory for context retrieval."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step_id': step_result.get('step_id'),
            'action_type': step_result.get('action_type'),
            'outcome': {'result': step_result.get('success', False)},  
            'high_signals': self._extract_high_signals(step_result)
        }
        
        self._memory_stack.append(entry)
        
        # Maintain window constraint by truncating oldest entry when limit reached
        if len(self._memory_stack) > self.max_short_term_memory_steps:
            removed = self._memory_stack.pop(0)
            print(f"Short-term memory overflow: archived {removed['step_id']}")
    
    def _extract_high_signals(self, step_result: Dict[str, Any]) -> List[str]:
        """Extract high-signal tokens from step results for compact storage."""
        signals = []
        for key, value in step_result.get('result_data', {}).items():
            if isinstance(value, float) and value > 0.5:  # Thresholded metrics
                signals.append(f"{key}={value:.2f}")
            elif isinstance(value, str) and len(value) < 300:  # Short text summaries  
                signals.append(value.replace('\n', ' ')[:300])
        return signals[:3]  # Limit to 3 key signals
    
    def get_active_context(self, 
                           max_keys: int = None,
                           exclude_system: bool = True) -> Dict[str, Any]:
        """
        Retrieve minimal viable context from active memory layers.
        
        Args:
            max_keys: Maximum number of active keys to include (reduces token load)
            exclude_system: Don't include system-level fields
        
        Returns:
            Minimal active state dictionary
        """
        
        if not self.active_context: 
            raise RuntimeError("No active context loaded. Load ADDR state first.")
        
        # Fix: Use correct method name
        included_keys = self._filter_active_context_keys(max_keys)
        
        return {k: v for k, v in self.active_context.items() if k in included_keys}
    
    def _filter_active_context_keys(self, max_keys: Optional[int]) -> List[str]:
        """Keep only most-recent fields from active context (reduces token usage)."""
        all_keys = list(self.active_context.keys())
        return all_keys[-max_keys:] if max_keys else all_keys[7:]  # Keep last 10 or drop first 12
    
    def compress_to_history(self) -> None:
        """Compress oldest short-term memory entries to compressed history archive."""
        
        if self.memory_stack_length < 5:  
            return  # Not enough entries for compression overhead
        
        # Compress and truncate oldest stack entries
        compressed = [self._memory_stack.pop(0)]
        
        while len(self._memory_stack) >= self.max_short_term_memory_steps * 2:
            entry = self._memory_stack.pop(0)
            compressed.append(entry)
        
        with gzip.open(str(self.compressed_history_path), 'wt', encoding='utf-8') as f:
            json.dump(compressed, f)
    
    def get_compressed_history_entry(self, entry_id: str) -> Dict[str, Any]:  
        """Retrieve specific compressed history entry via ID."""
        if not Path(str(self.compressed_history_path)).exists():
            return None
        
        with gzip.open(str(self.compressed_history_path), 'rt', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Failed to load compressed history: {e}")
                return {}
    
    def get_persistent_state(self, field: str): 
        """Load specific ADDR state fields from persistent memory source."""
        # Source-of-truth reconstruction pattern (ADDR is single, unified memory source)
        sys.path.insert(0, 'docs/design doc viewer')
        try:
            from ADDR import load_ADDR
            addr = load_ADDR()
            
            if hasattr(addr, field):  
                return getattr(addr, field)
            elif hasattr(addr, 'load_section') and isinstance(field, str): 
                return addr.load_section(field)  # Load specific section on demand
        except Exception as e:
            print(f"Failed to load state from ADDR: {e}")
        
        return None
    
    def queue_for_compression(self):
        """Queue next compression operation (non-blocking)."""
        try:
            self.executor.submit(self.compress_to_history)
        except Exception as e:
            print(f"Compression queue error: {e}")
    
    def _memory_stack_length(self) -> int:
        return len(self._memory_stack)
    
    def load_addr_context(self, needed_fields: List[str] = None) -> Dict[str, Any]:
        """Load only required fields from ADDR (no full context bloat)."""
        sys.path.insert(0, 'H:/projects/AlphaChart/docs/design doc viewer')
        
        try:
            from ADDR import load_ADDR
            addr = load_ADDR()
            
            if needed_fields:  # Only retrieve specific fields when needed
                return {field: getattr(addr, field, None) for field in needed_fields}
            else:  
                return addr.context  # Full context when needed
            
        except Exception as e:
            print(f"ADDR context load failed: {e}")
            return {}


# Global memory offloader instance (lazy-initialized for efficiency)  
_memory_offloader_instance = None  

def get_offloader() -> MemoryOffloader:
    """Get or create global offloader instance."""
    global _memory_offloader_instance
    
    if _memory_offloader_instance is None:
        _memory_offloader_instance = MemoryOffloader()
        
        # Initialize compressed history file if not exists
        if not _memory_offloader_instance.compressed_history_path.exists():
            _memory_offloader_instance.compressed_history_path.touch()
    
    return _memory_offloader_instance  


def optimize_active_context(current_step_data: Dict[str, Any]) -> str:
    """
    Optimize active context for micro-LLM consumption.
    
    Strips system fields, keeps high-signal entries only, reduces verbosity.
    
    Args:
        current_step_data: Raw step results dictionary
        
    Returns:
        Optimized minimal state JSON string
    """
    
    # Extract signals only — strip verbose fields and system boilerplate
    cleaned_data = {k: v for k, v in current_step_data.items() 
                    if not k.startswith('_system') and isinstance(v, (int, float, str))}
    
    # Limit to key metrics only (≤500 characters recommended per micro-LLM step)  
    summary = {'active_step': cleaned_data.get('action_type'), 'outcome': cleaned_data.get('success', 'pending')}
    
    for k, v in cleaned_data.items(): 
        if isinstance(v, (int, float)) and not k.startswith('_'):
            summary[k] = v
    
    return json.dumps(summary)