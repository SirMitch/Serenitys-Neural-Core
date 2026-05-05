"""
ADDR Module — Unified Source-of-Truth State Machine + Doc Indexer
Integrates with 5-Layer Serenity Memory System (Layer 5: Persistent Backbone)
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import sys

# Add docs path to sys.path for internal imports
DOCS_PATH = Path(__file__).parent
sys.path.insert(0, str(DOCS_PATH))


class ADDRIndexer:
    """Indexes all system-relevant text files in docs/design doc viewer/"""
    
    EXCLUDED_DIRS = {"__pycache__", ".bak", "finrlx", "temp"}
    TEXT_EXTENSIONS = {".md", ".py", ".json", ".csv", ".log", ".txt"}
    BINARY_METADATA_EXTENSIONS = {".png", ".pkl", ".db"}
    
    def __init__(self, docs_root: str = None):
        self.docs_root = Path(docs_root) if docs_root else DOCS_PATH
        self.file_index: List[Dict[str, Any]] = []
        self._build_index()
    
    def _build_index(self):
        """Recursively index all relevant files in docs root."""
        self.file_index.clear()
        for root, dirs, files in os.walk(self.docs_root):
            # Filter excluded directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                entry = {
                    "path": str(file_path.relative_to(self.docs_root)),
                    "abs_path": str(file_path),
                    "name": file,
                    "ext": ext,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "type": "text" if ext in self.TEXT_EXTENSIONS else "binary_metadata" if ext in self.BINARY_METADATA_EXTENSIONS else "excluded"
                }
                
                if entry["type"] != "excluded":
                    self.file_index.append(entry)
    
    def search_files(self, query: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search file names/paths for query string."""
        results = []
        for entry in self.file_index:
            if file_types and entry["type"] not in file_types:
                continue
            if query.lower() in entry["name"].lower() or query.lower() in entry["path"].lower():
                results.append(entry)
        return results
    
    def get_file_content(self, relative_path: str) -> str:
        """Read text file content (lazy load)."""
        target = self.docs_root / relative_path
        if target.exists() and target.suffix.lower() in self.TEXT_EXTENSIONS:
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        return ""


class ADDRStateMachine:
    """Parses ADDR.md into structured sessions and system state."""
    
    SESSION_HEADER_REGEX = re.compile(r'^##\s+Session\s+(\d+)\s+—\s+(.+?)\s+\((\d{4}-\d{2}-\d{2})\)', re.MULTILINE)
    STATE_SECTION_REGEX = re.compile(r'^##\s+SYSTEM STATE\s+(.*?)(?=^##|\Z)', re.DOTALL | re.MULTILINE)
    
    def __init__(self, addr_content: str):
        self.raw_content = addr_content
        self.sessions: List[Dict[str, Any]] = []
        self.current_session: Optional[Dict[str, Any]] = None
        self.next_steps: List[str] = []
        self.system_state: Dict[str, Any] = {}
        self._parse_sessions()
        self._extract_system_state()
    
    def _parse_sessions(self):
        """Split ADDR.md into individual session entries with metadata."""
        matches = list(self.SESSION_HEADER_REGEX.finditer(self.raw_content))
        
        for i, match in enumerate(matches):
            session_num = int(match.group(1))
            title = match.group(2).strip()
            date = match.group(3)
            start_pos = match.start()
            end_pos = matches[i+1].start() if i+1 < len(matches) else len(self.raw_content)
            content = self.raw_content[start_pos:end_pos].strip()
            
            # Extract status (✅/⏳/? markers)
            status_match = re.search(r'^[✅⏳?]\s+', content, re.MULTILINE)
            status = status_match.group(0).strip() if status_match else "?"
            
            # Extract next steps (lines starting with ⏳ or ### Next)
            next_steps = []
            for line in content.split('\n'):
                if line.strip().startswith('⏳') or 'Next Step' in line:
                    next_steps.append(line.strip().lstrip('⏳').strip())
            
            session = {
                "session_num": session_num,
                "title": title,
                "date": date,
                "status": status,
                "content": content,
                "next_steps": next_steps
            }
            
            self.sessions.append(session)
            
            # Track most recent session
            if not self.current_session or session_num > self.current_session["session_num"]:
                self.current_session = session
    
    def _extract_system_state(self):
        """Extract top-level system state from ADDR.md."""
        state_match = self.STATE_SECTION_REGEX.search(self.raw_content)
        if state_match:
            state_content = state_match.group(1).strip()
            # Parse key-value pairs from state section
            for line in state_content.split('\n'):
                if ':' in line and not line.strip().startswith('|'):
                    key, val = line.split(':', 1)
                    self.system_state[key.strip().lower()] = val.strip()
        
        # Extract global next steps from current session
        if self.current_session:
            self.next_steps = self.current_session.get("next_steps", [])


class ADDR:
    """Main ADDR interface: Single source-of-truth for state, docs, and memory."""
    
    def __init__(self, address: str = None, content: str = None):
        self.address = address or str(DOCS_PATH / "ADDR.md")
        self.content = content or ""
        self.indexer = ADDRIndexer()
        self.state_machine = None
        self.context = {}
        
        if self.content:
            self.state_machine = ADDRStateMachine(self.content)
            self.context = self._extract_context()
    
    def _extract_context(self) -> Dict[str, Any]:
        """Extract flat key-value pairs from ADDR content (legacy support)."""
        context = {}
        if self.content:
            for line in self.content.split('\n'):
                if ':' in line and not line.strip().startswith('|'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        val = parts[1].strip()
                        context[key] = val
        return context
    
    def load_section(self, section_name: str) -> str:
        """Lazy-load specific ADDR section by header name."""
        pattern = re.compile(rf'^##\s+{re.escape(section_name)}\s+(.*?)(?=^##|\Z)', re.DOTALL | re.MULTILINE)
        match = pattern.search(self.content)
        return match.group(1).strip() if match else ""
    
    def search(self, query: str, scope: str = "all") -> List[Tuple[str, str]]:
        """
        Full-text search across ADDR content or all indexed docs.
        
        Args:
            query: Search term
            scope: "addr" (only ADDR.md), "docs" (only indexed docs), "all" (both)
        
        Returns:
            List of (source, snippet) tuples
        """
        results = []
        
        # Search ADDR.md
        if scope in ("addr", "all"):
            for line_num, line in enumerate(self.content.split('\n'), 1):
                if query.lower() in line.lower():
                    results.append((f"ADDR.md:{line_num}", line.strip()))
        
        # Search indexed docs
        if scope in ("docs", "all"):
            for entry in self.indexer.file_index:
                if entry["type"] == "text":
                    content = self.indexer.get_file_content(entry["path"])
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if query.lower() in line.lower():
                            results.append((f"{entry['path']}:{line_num}", line.strip()))
        
        return results
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Return most recent session data."""
        return self.state_machine.current_session if self.state_machine else None
    
    def get_next_steps(self) -> List[str]:
        """Return pending next steps from current session."""
        return self.state_machine.next_steps if self.state_machine else []
    
    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """Return full file index."""
        return self.indexer.file_index
    
    def __getattr__(self, name):
        """Return context value or None if not found (legacy support)."""
        if name in self.context:
            return self.context[name]
        return None
    
    def __bool__(self):
        """Return True if ADDR loaded successfully."""
        return len(self.content) > 0


def load_ADDR(docs_path: str = None) -> ADDR:
    """
    Load ADDR.md and return ADDR object with full state + index.
    
    Args:
        docs_path: Path to directory containing ADDR.md (default: docs/design doc viewer)
    
    Returns:
        ADDR object with state, index, and search capabilities
    """
    target_path = Path(docs_path) if docs_path else DOCS_PATH
    addr_path = target_path / "ADDR.md"
    
    if not addr_path.exists():
        return ADDR(address=str(addr_path))
    
    try:
        with open(addr_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return ADDR(address=str(addr_path), content=content)
    except Exception as e:
        print(f"[ADDR] Error loading: {e}")
        return ADDR(address=str(addr_path))


if __name__ == "__main__":
    addr = load_ADDR()
    print(f"ADDR loaded: {len(addr.content)} chars")
    print(f"Indexed files: {len(addr.get_indexed_files())}")
    print(f"Current session: {addr.get_current_session()['title'] if addr.get_current_session() else 'None'}")
    print(f"Next steps: {addr.get_next_steps()[:3]}")
    print(f"Search 'memory' results: {len(addr.search('memory'))}")