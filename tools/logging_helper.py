# tools/logging_helper.py
"""
Enterprise-grade logging with file + console output, debug support, structured formatting.
Logs to root\logs with timestamp-based files. Respects debug_mode flag.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import traceback

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    BRIGHT_WHITE = "\033[97m"


class Logger:
    """Centralized logger respecting debug_mode and log levels"""
    
    def __init__(self, log_dir: Path, debug_mode: bool = False):
        self.log_dir = log_dir
        self.debug_mode = debug_mode
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.log_dir = Path.home() / "neural_logs"
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / f"neural_ai_{self.timestamp}.log"
        self.error_file = self.log_dir / f"errors_{self.timestamp}.log"
        
        self._init_log_files()
    
    def _init_log_files(self):
        """Initialize log files with headers"""
        header = f"{'='*80}\nNeural AI Loader - Session Log\nStarted: {datetime.now().isoformat()}\nDebug: {self.debug_mode}\n{'='*80}\n"
        self._write_raw(self.log_file, header)
    
    def _write_raw(self, filepath: Path, message: str):
        """Write to file safely"""
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(message)
                if not message.endswith('\n'):
                    f.write('\n')
        except Exception:
            pass
    
    def _format_msg(self, level: str, module: str, msg: str) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        return f"[{ts}] [{level:7s}] [{module:18s}] {msg}"
    
    def debug(self, msg: str, module: str = "MAIN"):
        formatted = self._format_msg("DEBUG", module, msg)
        self._write_raw(self.log_file, formatted)
        if self.debug_mode:
            self._cprint(formatted, Colors.GRAY)
    
    def info(self, msg: str, module: str = "MAIN"):
        formatted = self._format_msg("INFO", module, msg)
        self._write_raw(self.log_file, formatted)
        self._cprint(formatted, Colors.CYAN)
    
    def warning(self, msg: str, module: str = "MAIN"):
        formatted = self._format_msg("WARN", module, msg)
        self._write_raw(self.log_file, formatted)
        self._cprint(formatted, Colors.YELLOW)
    
    def error(self, msg: str, module: str = "MAIN", exc_info: bool = False):
        formatted = self._format_msg("ERROR", module, msg)
        self._write_raw(self.log_file, formatted)
        self._write_raw(self.error_file, formatted)
        self._cprint(formatted, Colors.RED)
        if exc_info:
            tb = traceback.format_exc()
            self._write_raw(self.log_file, tb)
            self._write_raw(self.error_file, tb)
    
    def critical(self, msg: str, module: str = "MAIN"):
        formatted = self._format_msg("CRIT", module, msg)
        self._write_raw(self.log_file, formatted)
        self._write_raw(self.error_file, formatted)
        self._cprint(formatted, Colors.RED, bold=True)
    
    def section(self, title: str):
        msg = f"\n{'='*80}\n{title.center(80)}\n{'='*80}\n"
        self._write_raw(self.log_file, msg)
        self._cprint(msg, Colors.MAGENTA, bold=True)
    
    def _cprint(self, text: str, color=Colors.RESET, bold: bool = False):
        prefix = Colors.BOLD if bold else ""
        print(f"{prefix}{color}{text}{Colors.RESET}")
    
    def get_log_file(self) -> Path:
        return self.log_file
