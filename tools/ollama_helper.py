# tools/ollama_helper.py
"""
Ollama service management with robust error handling and logging.
"""

import subprocess
import time
import sys
import requests
from logging_helper import Logger

logger: Logger = None

def set_logger(log_obj: Logger):
    global logger
    logger = log_obj

def _log(level: str, msg: str):
    if logger:
        getattr(logger, level)(msg, "OLLAMA")

def is_ollama_running(timeout: int = 5) -> bool:
    """Check if Ollama HTTP server is responsive"""
    try:
        response = requests.get(
            "http://localhost:11434",
            timeout=timeout
        )
        result = response.status_code == 200
        _log("debug", f"Ollama check: {'running' if result else 'not running'}")
        return result
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        _log("debug", "Ollama check timed out")
        return False
    except Exception as e:
        _log("debug", f"Ollama check error: {str(e)[:50]}")
        return False

def start_ollama_server() -> bool:
    """
    Start ollama serve detached (Windows-safe, no popup).
    Returns True if started successfully.
    """
    try:
        _log("info", "Starting Ollama server in background...")
        
        cmd = ["ollama", "serve"]
        kwargs = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        
        if sys.platform.startswith("win"):
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        
        subprocess.Popen(cmd, **kwargs)
        _log("debug", "Ollama process spawned")
        return True
    
    except FileNotFoundError:
        _log("error", "'ollama' not found in PATH. Install from https://ollama.com/download")
        return False
    except Exception as e:
        _log("error", f"Failed to start Ollama: {str(e)[:100]}")
        return False

def wait_for_ollama(timeout: int = 30, check_interval: int = 2) -> bool:
    """
    Poll Ollama until running or timeout.
    Returns True if ready, False if timeout.
    """
    _log("info", f"Waiting for Ollama (up to {timeout}s)...")
    
    start = time.time()
    attempts = 0
    
    while time.time() - start < timeout:
        attempts += 1
        if is_ollama_running(timeout=4):
            elapsed = time.time() - start
            _log("info", f"Ollama is ready (took {elapsed:.1f}s)")
            return True
        
        if attempts % 3 == 0:
            _log("debug", f"Still waiting... ({time.time() - start:.1f}s elapsed)")
        
        time.sleep(check_interval)
    
    _log("error", f"Timeout waiting for Ollama after {timeout}s")
    return False

def get_available_models() -> list:
    """
    Fetch list of available models from Ollama.
    Returns empty list if unavailable or error.
    """
    if not is_ollama_running():
        _log("warning", "Ollama not running; cannot fetch models")
        return []
    
    try:
        resp = requests.get(
            "http://localhost:11434/api/tags",
            timeout=10
        )
        
        if resp.status_code != 200:
            _log("error", f"Models API returned {resp.status_code}")
            return []
        
        data = resp.json()
        models = [m['name'] for m in data.get('models', [])]
        _log("info", f"Found {len(models)} models")
        return models
    
    except requests.Timeout:
        _log("error", "Models API request timed out")
        return []
    except Exception as e:
        _log("error", f"Failed to fetch models: {str(e)[:100]}")
        return []
