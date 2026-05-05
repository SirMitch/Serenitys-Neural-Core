# tools/interpreter_helper.py
"""
Open Interpreter setup, configuration, and chat loop.
Supports runtime config overrides (gpu_layers, context_size, etc).
"""

import sys
import types
from logging_helper import Logger

logger: Logger = None

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    BRIGHT_WHITE = "\033[97m"

def set_logger(log_obj: Logger):
    global logger
    logger = log_obj

def _log(level: str, msg: str):
    if logger:
        getattr(logger, level)(msg, "INTERPRETER")

def cprint(text: str, color=Colors.RESET, bold: bool = False):
    """Colored console print"""
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Colors.RESET}")

def setup_interpreter(selected_model: str, runtime_config: dict = None, api_base: str = "http://localhost:11434"):
    """
    Import, configure, and pre-warm Open Interpreter.
    
    Args:
        selected_model: Model name (e.g., "llama2")
        runtime_config: Optional dict with keys:
            - gpu_layers (int): Number of GPU layers
            - num_threads (int): Thread count
            - context_size (int): Context window size
        api_base: Ollama API endpoint
    
    Returns:
        Configured interpreter instance or None on failure.
    """
    
    if not runtime_config:
        runtime_config = {}
    
    _log("info", f"Setting up interpreter for model: {selected_model}")
    
    # Fix pkg_resources (common Windows issue)
    try:
        import pkg_resources
    except ImportError:
        _log("debug", "Mocking pkg_resources...")
        pkg_resources = types.ModuleType('pkg_resources')
        pkg_resources.__file__ = 'mock'
        pkg_resources.get_distribution = lambda x: type('Dist', (), {'version': '1.0.0'})()
        sys.modules['pkg_resources'] = pkg_resources
    
    # Import interpreter
    try:
        from interpreter import interpreter
        _log("info", "Open Interpreter imported successfully")
        cprint("✓ Open Interpreter imported", Colors.GREEN, bold=True)
    except ImportError as e:
        _log("error", f"Failed to import interpreter: {str(e)[:100]}")
        cprint(f"✗ Open Interpreter not installed: {str(e)[:50]}", Colors.RED, bold=True)
        return None
    except Exception as e:
        _log("error", f"Unexpected error importing: {str(e)}", exc_info=True)
        cprint(f"✗ Error: {str(e)[:50]}", Colors.RED, bold=True)
        return None
    
    try:
        # Configure
        interpreter.offline = True
        interpreter.disable_telemetry = True
        interpreter.llm.model = f"ollama/{selected_model}"
        interpreter.llm.api_base = api_base
        interpreter.llm.api_key = "fake_key"
        
        # Apply runtime config
        context_size = runtime_config.get("context_size", 8000)
        interpreter.llm.context_window = context_size
        interpreter.llm.max_tokens = min(2000, context_size // 4)
        
        _log("debug", f"Config: context={context_size}, max_tokens={interpreter.llm.max_tokens}")
        
        # Pre-warm
        cprint("\nWarming up model (first response may take 5-30s)...", Colors.YELLOW, bold=True)
        _log("info", "Pre-warming model with test request...")
        
        try:
            dummy_response = interpreter.chat("hi", display=False)
            _log("info", "Model warmed up successfully")
            cprint("✓ Model warmed up", Colors.GREEN)
        except Exception as e:
            _log("warning", f"Warm-up skipped: {str(e)[:80]}")
            cprint(f"⚠ Warm-up failed (will retry on first use): {str(e)[:40]}", Colors.YELLOW)
        
        return interpreter
    
    except Exception as e:
        _log("error", f"Configuration failed: {str(e)}", exc_info=True)
        cprint(f"✗ Configuration error: {str(e)[:50]}", Colors.RED, bold=True)
        return None

def run_chat_loop(interpreter_instance):
    """
    Run interactive chat loop.
    Supports 'back' to return to menu, 'exit'/'quit' to close.
    """
    
    if not interpreter_instance:
        _log("error", "Interpreter instance is None")
        cprint("✗ Interpreter not available", Colors.RED)
        return False
    
    _log("info", "Starting chat loop")
    cprint("\n" + "="*70, Colors.CYAN)
    cprint("Chat Session Started. Type 'exit', 'quit', or 'back' to exit.", Colors.CYAN)
    cprint("="*70 + "\n", Colors.CYAN)
    
    try:
        while True:
            try:
                user_input = input(f"{Colors.YELLOW}You:{Colors.RESET} ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    _log("info", "User exited chat")
                    cprint("Goodbye!", Colors.CYAN)
                    return True
                
                if user_input.lower() == 'back':
                    _log("info", "User requested back")
                    return False  # Signal caller to handle back
                
                _log("debug", f"User input: {user_input[:50]}")
                
                try:
                    response = interpreter_instance.chat(user_input, display=True)
                    _log("debug", "Response generated")
                except Exception as e:
                    _log("error", f"Chat error: {str(e)[:100]}")
                    cprint(f"✗ Error: {str(e)[:60]}", Colors.RED)
                    cprint("Trying again...", Colors.YELLOW)
            
            except KeyboardInterrupt:
                _log("info", "User interrupted (Ctrl+C)")
                cprint("\nGoodbye!", Colors.CYAN)
                return True
            
            except EOFError:
                _log("info", "EOF received")
                return True
            
            except Exception as e:
                _log("error", f"Chat loop error: {str(e)}", exc_info=True)
                cprint(f"✗ Error: {str(e)[:60]}", Colors.RED)
    
    except Exception as e:
        _log("critical", f"Chat loop crashed: {str(e)}", exc_info=True)
        cprint(f"✗ Critical error: {str(e)[:60]}", Colors.RED, bold=True)
        return True
