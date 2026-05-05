# tools/configure_agent.py
"""
Central configuration wizard with system info validation and smart defaults.
"""

from logging_helper import Logger

logger: Logger = None

def set_logger(log_obj: Logger):
    global logger
    logger = log_obj

def _log(level: str, msg: str):
    if logger:
        getattr(logger, level)(msg, "CONFIG")

def configure_agent(selected_backend: dict, selected_interpreter: dict, selected_model: str, system_info: dict) -> dict:
    """
    Central configuration wizard.
    
    Args:
        selected_backend: Backend config dict
        selected_interpreter: Interpreter config dict
        selected_model: Model name string
        system_info: System properties dict
    
    Returns:
        Safe configuration dictionary for execution
    """
    
    _log("info", f"Configuring: {selected_interpreter['name']} + {selected_model}")
    
    try:
        # Validate inputs
        if not system_info:
            _log("warning", "No system info provided; using defaults")
            system_info = {}
        
        if not selected_model:
            _log("error", "No model selected")
            return _get_safe_fallback(selected_backend, selected_interpreter, selected_model)
        
        # Safe conversion
        def to_int(value, default=0, min_val=0, max_val=None):
            try:
                result = int(value)
                if min_val is not None:
                    result = max(result, min_val)
                if max_val is not None:
                    result = min(result, max_val)
                return result
            except (ValueError, TypeError):
                return default
        
        vram_total = to_int(system_info.get("VRAM_TOTAL_MB", 0), min_val=0)
        vram_free = to_int(system_info.get("VRAM_FREE_MB", 0), min_val=0)
        ram_total = to_int(system_info.get("RAM_GB", 8), default=8, min_val=4)
        cpu_cores = to_int(system_info.get("CPU_CORES", 4), default=4, min_val=1, max_val=64)
        
        _log("debug", f"System: RAM={ram_total}GB, CPU={cpu_cores}, VRAM={vram_total}MB")
        
        # Model analysis
        model_lower = selected_model.lower()
        is_large = any(x in model_lower for x in [":70b", ":405b", ":130b", "8x22b"])
        is_vision = any(x in model_lower for x in ["vision", "llava", "moondream", "vl"])
        
        _log("debug", f"Model: large={is_large}, vision={is_vision}")
        
        # Ollama tuning
        if vram_total > 0:
            gpu_layers = min(80, max(8, vram_total // 256))
        else:
            gpu_layers = 0
        
        num_threads = max(2, cpu_cores - 1)
        
        # Context size based on RAM
        context_size = 4096
        if ram_total >= 32:
            context_size = 8192
        if ram_total >= 64:
            context_size = 16384
        
        ollama_config = {
            "gpu_layers": gpu_layers,
            "num_threads": num_threads,
            "context_size": context_size
        }
        
        _log("debug", f"Ollama config: gpu_layers={gpu_layers}, threads={num_threads}, context={context_size}")
        
        # Docker config
        docker_memory = max(4, ram_total // 2)
        docker_config = {
            "memory_limit": f"{docker_memory}g",
            "cpu_limit": max(2, cpu_cores - 1),
            "vision_enabled": is_vision
        }
        
        _log("debug", f"Docker config: mem={docker_memory}g, cpus={docker_config['cpu_limit']}, vision={is_vision}")
        
        # Launch mode
        launch_mode = "browser" if selected_interpreter["id"] == "openhands" else "terminal"
        
        # Build final config
        config = {
            "backend": selected_backend["id"],
            "interpreter": selected_interpreter["id"],
            "model": selected_model,
            "ollama": ollama_config,
            "docker": docker_config,
            "launch_mode": launch_mode
        }
        
        _log("info", f"Configuration complete: launch_mode={launch_mode}")
        return config
    
    except Exception as e:
        _log("error", f"Configuration error: {str(e)}", exc_info=True)
        return _get_safe_fallback(selected_backend, selected_interpreter, selected_model)

def _get_safe_fallback(selected_backend: dict, selected_interpreter: dict, selected_model: str) -> dict:
    """Return safe default config when configuration fails"""
    _log("info", "Using safe fallback configuration")
    return {
        "backend": selected_backend.get("id", "ollama"),
        "interpreter": selected_interpreter.get("id", "open_interpreter"),
        "model": selected_model or "llama2",
        "ollama": {
            "gpu_layers": 0,
            "num_threads": 4,
            "context_size": 4096
        },
        "docker": {
            "memory_limit": "4g",
            "cpu_limit": 2,
            "vision_enabled": False
        },
        "launch_mode": "terminal"
    }
