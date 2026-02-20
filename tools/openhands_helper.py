# tools/openhands_helper.py
"""
OpenHands Docker launcher with full config support, error handling, and logging.
Dynamically resolves workspace paths and state directories.
"""

import subprocess
import time
import os
from pathlib import Path
from logging_helper import Logger

logger: Logger = None

def set_logger(log_obj: Logger):
    global logger
    logger = log_obj

def _log(level: str, msg: str):
    if logger:
        getattr(logger, level)(msg, "OPENHANDS")

def _docker_available() -> bool:
    """Check if Docker is installed and responding"""
    try:
        subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            check=True,
            timeout=5
        )
        _log("debug", "Docker is available")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        _log("warning", "Docker not available or not responding")
        return False

def _container_running(name: str) -> bool:
    """Check if container is actively running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        running = name in result.stdout
        _log("debug", f"Container {name}: {'running' if running else 'not running'}")
        return running
    except Exception as e:
        _log("debug", f"Container check failed: {str(e)[:50]}")
        return False

def _container_exists(name: str) -> bool:
    """Check if container exists (stopped or running)"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        exists = name in result.stdout
        _log("debug", f"Container {name}: {'exists' if exists else 'does not exist'}")
        return exists
    except Exception as e:
        _log("debug", f"Container exists check failed: {str(e)[:50]}")
        return False

def _wait_for_container(name: str, timeout: int = 45) -> bool:
    """Poll until container is running"""
    _log("info", f"Waiting for container {name} (up to {timeout}s)...")
    start = time.time()
    attempts = 0
    
    while time.time() - start < timeout:
        attempts += 1
        try:
            if _container_running(name):
                elapsed = time.time() - start
                _log("info", f"Container ready in {elapsed:.1f}s")
                return True
        except Exception:
            pass
        
        if attempts % 10 == 0:
            _log("debug", f"Still waiting ({time.time() - start:.1f}s)...")
        
        time.sleep(1)
    
    _log("error", f"Container {name} did not start within {timeout}s")
    return False

def launch_openhands_docker(model_name: str, docker_config: dict = None) -> tuple:
    """
    Launch OpenHands in Docker with full config support.
    
    Args:
        model_name: Model to load in OpenHands
        docker_config: Optional dict with:
            - memory_limit (str): e.g., "4g", "8g"
            - cpu_limit (int): number of CPUs
            - vision_enabled (bool): enable vision support
    
    Returns:
        (success: bool, url: str or None, message: str)
    """
    
    container_name = "neural-openhands"
    image_name = "ghcr.io/all-hands-ai/openhands:main"
    url = "http://localhost:3000"
    
    # Safe config defaults
    if not docker_config:
        docker_config = {}
    
    memory_limit = str(docker_config.get("memory_limit", "4g"))
    cpu_limit = int(docker_config.get("cpu_limit", 4))
    vision_enabled = bool(docker_config.get("vision_enabled", False))
    
    _log("info", f"Launching OpenHands: model={model_name}, mem={memory_limit}, cpu={cpu_limit}")
    
    # Check Docker
    if not _docker_available():
        msg = "Docker not found or not running. Start Docker Desktop."
        _log("error", msg)
        return False, None, msg
    
    # Already running
    if _container_running(container_name):
        msg = f"OpenHands already running → {url}"
        _log("info", msg)
        return True, url, msg
    
    # Remove stopped container
    if _container_exists(container_name):
        _log("debug", f"Removing stopped container {container_name}")
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
        except Exception as e:
            msg = f"Failed to remove old container: {str(e)}"
            _log("error", msg)
            return False, None, msg
    
    # Ensure image exists
    _log("debug", "Checking for Docker image...")
    try:
        image_check = subprocess.run(
            ["docker", "images", "-q", image_name],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        
        if not image_check.stdout.strip():
            _log("info", f"Image not found; pulling {image_name}...")
            pull = subprocess.run(
                ["docker", "pull", image_name],
                capture_output=True,
                text=True,
                timeout=300
            )
            if pull.returncode != 0:
                msg = f"Failed to pull image: {pull.stderr[:100]}"
                _log("error", msg)
                return False, None, msg
            _log("info", "Image pulled successfully")
    
    except subprocess.TimeoutExpired:
        msg = "Image pull timed out (network issue?)"
        _log("error", msg)
        return False, None, msg
    except Exception as e:
        msg = f"Image check failed: {str(e)}"
        _log("error", msg)
        return False, None, msg
    
    # State directory
    user_profile = os.environ.get("USERPROFILE", "")
    if not user_profile:
        msg = "USERPROFILE not set"
        _log("error", msg)
        return False, None, msg
    
    state_path = os.path.join(user_profile, ".openhands-state")
    try:
        Path(state_path).mkdir(parents=True, exist_ok=True)
        _log("debug", f"State directory ready: {state_path}")
    except Exception as e:
        msg = f"Failed to create state dir: {str(e)}"
        _log("error", msg)
        return False, None, msg
    
    # Find workspace path (try multiple locations)
    workspace_paths = [
        "D:\\OpenInturpter",
        os.path.join(os.path.expanduser("~"), "OpenInterpreter"),
        str(Path.cwd()),
    ]
    
    workspace_path = None
    for path in workspace_paths:
        if os.path.exists(path):
            workspace_path = path
            _log("debug", f"Found workspace: {workspace_path}")
            break
    
    if not workspace_path:
        _log("warning", f"Workspace not found in common locations; using {workspace_paths[2]}")
        workspace_path = workspace_paths[2]
    
    # Build and launch
    _log("debug", "Building docker run command...")
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "-p", "3000:3000",
        "-m", memory_limit,
        "--cpus", str(cpu_limit),
        "-v", f"{state_path}:/root/.openhands-state",
        "-v", f"{workspace_path}:/workspace",
        "--add-host=host.docker.internal:host-gateway",
        "-e", f"LLM_MODEL={model_name}",
        image_name
    ]
    
    _log("debug", f"Docker command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        
        if result.returncode != 0:
            msg = f"Docker run failed: {result.stderr[:150]}"
            _log("error", msg)
            return False, None, msg
        
        container_id = result.stdout.strip()[:12]
        _log("info", f"Container created: {container_id}")
    
    except subprocess.TimeoutExpired:
        msg = "Docker run timed out"
        _log("error", msg)
        return False, None, msg
    except Exception as e:
        msg = f"Docker run exception: {str(e)}"
        _log("error", msg)
        return False, None, msg
    
    # Wait for startup
    if not _wait_for_container(container_name, timeout=45):
        msg = "Container failed to start (check Docker Desktop logs)"
        _log("error", msg)
        return False, None, msg
    
    msg = f"OpenHands launched successfully → {url}"
    _log("info", msg)
    return True, url, msg
