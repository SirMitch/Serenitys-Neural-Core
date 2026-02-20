# tools/system_info_helper.py
"""
System info extraction via PowerShell gather_system_info.ps1.
Uses root-relative paths and comprehensive error handling.
"""

import subprocess
from pathlib import Path
from logging_helper import Logger

logger: Logger = None  # Set by caller

def set_logger(log_obj: Logger):
    """Set global logger instance"""
    global logger
    logger = log_obj

def get_system_info(debug: bool = False) -> dict:
    """
    Call gather_system_info.ps1 and parse key=value output.
    Returns dict of system properties or empty dict on failure.
    """
    global logger
    if not logger:
        # Fallback if logger not set
        class DummyLogger:
            def debug(self, msg, module="SYSINFO"): print(msg)
            def error(self, msg, module="SYSINFO", exc_info=False): print(f"ERROR: {msg}")
            def warning(self, msg, module="SYSINFO"): print(f"WARN: {msg}")
        logger = DummyLogger()
    
    # Find gather_system_info.ps1 relative to this file
    tools_dir = Path(__file__).resolve().parent
    script_path = tools_dir / "gather_system_info.ps1"
    
    if not script_path.exists():
        logger.error(f"gather_system_info.ps1 not found at {script_path}", "SYSINFO")
        return {}
    
    try:
        logger.debug(f"Running system info script: {script_path}", "SYSINFO")
        
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(script_path)
        ]
        if debug:
            cmd.append("-DebugMode")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(
                f"PowerShell script failed (code {result.returncode}): {result.stderr[:200]}",
                "SYSINFO"
            )
            return {}
        
        output = result.stdout.strip()
        info = {}
        
        for line in output.splitlines():
            line = line.strip()
            if "=" not in line:
                continue
            try:
                key, value = line.split("=", 1)
                info[key.strip()] = value.strip()
                logger.debug(f"  {key.strip()}={value.strip()}", "SYSINFO")
            except ValueError:
                logger.warning(f"Could not parse line: {line}", "SYSINFO")
        
        if not info:
            logger.warning("No system info extracted from script", "SYSINFO")
            return {}
        
        logger.info(f"System info gathered: {len(info)} properties", "SYSINFO")
        return info
    
    except subprocess.TimeoutExpired:
        logger.error("System info script timed out (15s)", "SYSINFO")
        return {}
    except FileNotFoundError:
        logger.error("PowerShell not found in PATH", "SYSINFO")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", "SYSINFO", exc_info=True)
        return {}
