#!/usr/bin/env python3
"""
Neural AI Loader - Enterprise-grade main launcher with integrated documentation viewer
Features: logging, debug mode, navigation system, dynamic paths, integrated help system
"""

import sys
import shutil
from pathlib import Path
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION - Paths, logging, imports
# ═══════════════════════════════════════════════════════════════════════════

# Get script root (where neural_ai_loader.py is)
SCRIPT_ROOT = Path(__file__).resolve().parent
TOOLS_DIR = SCRIPT_ROOT / "tools"
LOGS_DIR = SCRIPT_ROOT / "logs"
DOCS_DIR = SCRIPT_ROOT / "docs"

# Add tools to path
sys.path.insert(0, str(TOOLS_DIR))

# Import core modules
try:
    from logging_helper import Logger, Colors
    from nav_helper import NavState, NavigationError
except ImportError as e:
    print(f"FATAL: Could not import core helpers: {e}")
    sys.exit(1)

# Initialize logging first
logger = None

def init_logger(debug_mode: bool):
    """Initialize global logger"""
    global logger
    logger = Logger(LOGS_DIR, debug_mode=debug_mode)
    logger.section("Neural AI Loader - Session Start")
    logger.info(f"Script root: {SCRIPT_ROOT}", "MAIN")
    logger.info(f"Tools dir: {TOOLS_DIR}", "MAIN")
    logger.info(f"Logs dir: {LOGS_DIR}", "MAIN")
    logger.info(f"Docs dir: {DOCS_DIR}", "MAIN")
    logger.info(f"Debug mode: {debug_mode}", "MAIN")

# Now import other helpers
try:
    from ollama_helper import (
        is_ollama_running,
        start_ollama_server,
        wait_for_ollama,
        get_available_models,
        set_logger as set_ollama_logger
    )
    from interpreter_helper import (
        setup_interpreter,
        run_chat_loop,
        set_logger as set_interpreter_logger
    )
    from system_info_helper import get_system_info, set_logger as set_sysinfo_logger
    from openhands_helper import launch_openhands_docker, set_logger as set_openhands_logger
    from configure_agent import configure_agent, set_logger as set_config_logger
    from doc_viewer import show_doc_viewer, get_documentation_summary, set_logger as set_docviewer_logger
except ImportError as e:
    print(f"FATAL: Could not import helpers: {e}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# Colors & Utilities
# ═══════════════════════════════════════════════════════════════════════════

def cprint(text: str, color=Colors.RESET, bold: bool = False):
    """Print colored text"""
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Colors.RESET}")

def print_centered_header(text: str, char: str = "=", color=Colors.MAGENTA):
    """Print centered header"""
    try:
        width = shutil.get_terminal_size().columns
    except Exception:
        width = 80
    
    title = f" {text} "
    padding = max(0, (width - len(title)) // 2)
    separator = char * width
    
    cprint("", color)
    cprint(separator, color)
    cprint(" " * padding + title, color, bold=True)
    cprint(separator, color)

# ═══════════════════════════════════════════════════════════════════════════
# Model Helpers
# ═══════════════════════════════════════════════════════════════════════════

def get_model_family(name: str) -> str:
    """Classify model by family"""
    name = name.lower()
    if any(x in name for x in ["llama", "llama3", "llama-3"]): return "Llama"
    if "gemma" in name: return "Gemma"
    if "mistral" in name or "mixtral" in name: return "Mistral"
    if "qwen" in name: return "Qwen"
    if "phi" in name: return "Phi"
    if "deepseek" in name: return "DeepSeek"
    if "codestral" in name: return "Codestral"
    if "command" in name: return "Command R"
    return "Other"

def get_model_capability(name: str) -> str:
    """Detect model capability (text/vision/image-gen)"""
    name = name.lower()
    if any(x in name for x in ["llava", "vision", "moondream", "bakllava", "vl"]):
        return "Text + Vision"
    if any(x in name for x in ["stable-diffusion", "sd", "flux", "image", "sdxl"]):
        return "Image Generation"
    return "Text-Only"

def is_large_model(name: str) -> bool:
    """Check if model is large (70B+)"""
    name = name.lower()
    return any(x in name for x in [":70b", ":405b", ":130b", "8x22b"])

# ═══════════════════════════════════════════════════════════════════════════
# Main Flow
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main application flow with navigation and integrated documentation"""
    
    global logger
    
    # ─────────────────────────────────────────────────────────────────────
    # Debug Mode Selection
    # ─────────────────────────────────────────────────────────────────────
    
    print_centered_header("Neural AI Loader", color=Colors.CYAN)
    cprint("Enable debug mode? (y/n): ", Colors.YELLOW, bold=True)
    
    try:
        debug_resp = input().strip().lower()
        debug_mode = debug_resp in ["y", "yes"]
    except KeyboardInterrupt:
        cprint("Interrupted", Colors.RED)
        sys.exit(0)
    
    # Initialize logger
    init_logger(debug_mode)
    
    # Set logger for all helpers
    set_ollama_logger(logger)
    set_sysinfo_logger(logger)
    set_interpreter_logger(logger)
    set_openhands_logger(logger)
    set_config_logger(logger)
    set_docviewer_logger(logger)
    
    # Display header with debug tag if enabled
    debug_tag = " (debug)" if debug_mode else ""
    
    nav = NavState()
    system_info = None
    selected_backend = None
    selected_interpreter = None
    models = None
    selected_model = None
    config = None
    
    try:
        # ─────────────────────────────────────────────────────────────────────
        # MAIN MENU LOOP
        # ─────────────────────────────────────────────────────────────────────
        
        while True:
            
            # HOME SCREEN
            if nav.current() == "HOME":
                print_centered_header(f"Neural AI Loader{debug_tag}", color=Colors.CYAN)
                print()
                cprint("Main Menu:", Colors.YELLOW, bold=True)
                print()
                cprint("  1) Start AI Session (New Run)", Colors.BRIGHT_WHITE)
                doc_status = get_documentation_summary(SCRIPT_ROOT)
                cprint(f"  2) Documentation & Help ({doc_status})", Colors.BRIGHT_WHITE)
                cprint("  3) Quit", Colors.YELLOW)
                print()
                
                try:
                    choice = input(f"{Colors.YELLOW}Select option (1-3): {Colors.RESET}").strip()
                    
                    if choice == "1":
                        nav.push("SYSINFO")
                        logger.info("User selected: Start AI Session", "MAIN")
                    elif choice == "2":
                        nav.push("DOCS")
                        logger.info("User selected: Documentation", "MAIN")
                    elif choice == "3":
                        logger.info("User quit from main menu", "MAIN")
                        cprint("\n✓ Goodbye!", Colors.GREEN)
                        sys.exit(0)
                    else:
                        cprint("Invalid choice", Colors.YELLOW)
                        input("Press Enter to continue...")
                
                except KeyboardInterrupt:
                    logger.info("User interrupted main menu", "MAIN")
                    cprint("\n✗ Interrupted", Colors.RED)
                    sys.exit(0)
                except Exception as e:
                    logger.error(f"Menu error: {str(e)}", "MAIN")
                    cprint(f"Error: {str(e)}", Colors.RED)
                    input("Press Enter to continue...")
            
            # ─────────────────────────────────────────────────────────────────────
            # DOCUMENTATION VIEWER
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "DOCS":
                logger.section("Documentation Viewer")
                result = show_doc_viewer(SCRIPT_ROOT)
                
                if result == "exit":
                    logger.info("User quit from documentation", "MAIN")
                    cprint("\n✓ Goodbye!", Colors.GREEN)
                    sys.exit(0)
                elif result == "back":
                    nav.pop()
            
            # ─────────────────────────────────────────────────────────────────────
            # SYSTEM INFO GATHERING
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "SYSINFO":
                print_centered_header(f"Neural AI Loader{debug_tag}", color=Colors.CYAN)
                
                cprint("\nGathering system information... ", Colors.CYAN, bold=True)
                system_info = get_system_info(debug=debug_mode)
                
                if not system_info:
                    logger.error("No system info gathered; using defaults", "MAIN")
                    system_info = {}
                
                cprint("✓", Colors.GREEN)
                cprint("\nSystem Specs:", Colors.BRIGHT_WHITE, bold=True)
                
                os_ver = system_info.get("OS_VERSION", "N/A")
                cpu_name = system_info.get("CPU_NAME", "N/A")
                cpu_cores = system_info.get("CPU_CORES", "N/A")
                ram_gb = system_info.get("RAM_GB", "N/A")
                gpu_name = system_info.get("GPU_NAME", "N/A")
                vram_total = system_info.get("VRAM_TOTAL_MB", "N/A")
                
                cprint(f"  OS:   {os_ver}", Colors.GREEN)
                cprint(f"  CPU:  {cpu_name} ({cpu_cores} cores)", Colors.GREEN)
                cprint(f"  RAM:  {ram_gb} GB", Colors.GREEN)
                
                if gpu_name != "N/A":
                    cprint(f"  GPU:  {gpu_name}", Colors.GREEN)
                    if vram_total != "N/A":
                        cprint(f"  VRAM: {vram_total} MB", Colors.GREEN)
                
                logger.info(f"System: OS={os_ver}, CPU={cpu_cores}c, RAM={ram_gb}GB", "MAIN")
                
                cprint("\n  M) Back to Main Menu", Colors.YELLOW)
                print()
                
                try:
                    choice = input(f"{Colors.YELLOW}Press Enter to continue or M for menu: {Colors.RESET}").strip().upper()
                    if choice == "M":
                        nav.home()
                    else:
                        nav.push("BACKEND")
                except KeyboardInterrupt:
                    nav.home()
            
            # ─────────────────────────────────────────────────────────────────────
            # BACKEND SELECTION
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "BACKEND":
                backends = [
                    {"id": "ollama", "name": "Ollama (default)", "enabled": True},
                    {"id": "lmstudio", "name": "LM Studio (Unavailable)", "enabled": False},
                ]
                
                cprint("\nSelect backend service:", Colors.YELLOW, bold=True)
                for i, b in enumerate(backends, 1):
                    color = Colors.BRIGHT_WHITE if b["enabled"] else Colors.GRAY
                    cprint(f"  {i}) {b['name']}", color)
                
                cprint("\n  M) Main Menu", Colors.YELLOW)
                print()
                
                selected_backend = None
                while selected_backend is None:
                    choice = input(f"{Colors.YELLOW}Enter number or M (default=1): {Colors.RESET}").strip() or "1"
                    
                    if choice.upper() == "M":
                        logger.info("User returned to main menu", "MAIN")
                        nav.home()
                        break
                    
                    try:
                        idx = int(choice) - 1
                        if backends[idx]["enabled"]:
                            selected_backend = backends[idx]
                            logger.info(f"Selected backend: {selected_backend['name']}", "MAIN")
                            cprint(f"✓ {selected_backend['name']}", Colors.GREEN)
                        else:
                            cprint("Not available.", Colors.YELLOW)
                    except (ValueError, IndexError):
                        cprint("Invalid choice.", Colors.YELLOW)
                
                if selected_backend is None:
                    continue
                
                if selected_backend["id"] != "ollama":
                    logger.error("Only Ollama backend implemented", "MAIN")
                    cprint("✗ Backend not implemented", Colors.RED)
                    nav.home()
                    continue
                
                nav.push("INTERPRETER")
            
            # ─────────────────────────────────────────────────────────────────────
            # INTERPRETER SELECTION
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "INTERPRETER":
                interpreters = [
                    {"id": "open_interpreter", "name": "Open Interpreter (default)", "enabled": True},
                    {"id": "openhands", "name": "OpenHands (Docker - File/Web/Vision Agent)", "enabled": True},
                ]
                
                cprint("\nSelect AI agent type:", Colors.YELLOW, bold=True)
                for i, t in enumerate(interpreters, 1):
                    color = Colors.BRIGHT_WHITE if t["enabled"] else Colors.GRAY
                    cprint(f"  {i}) {t['name']}", color)
                
                cprint("\n  B) Back", Colors.YELLOW)
                cprint("  M) Main Menu", Colors.YELLOW)
                print()
                
                selected_interpreter = None
                while selected_interpreter is None:
                    choice = input(f"{Colors.YELLOW}Enter number or option (default=1): {Colors.RESET}").strip() or "1"
                    
                    if choice.upper() == "M":
                        nav.home()
                        break
                    elif choice.upper() == "B":
                        nav.pop()
                        break
                    
                    try:
                        idx = int(choice) - 1
                        if interpreters[idx]["enabled"]:
                            selected_interpreter = interpreters[idx]
                            logger.info(f"Selected interpreter: {selected_interpreter['name']}", "MAIN")
                            cprint(f"✓ {selected_interpreter['name']}", Colors.GREEN)
                        else:
                            cprint("Not available.", Colors.YELLOW)
                    except (ValueError, IndexError):
                        cprint("Invalid choice.", Colors.YELLOW)
                
                if selected_interpreter is None:
                    continue
                
                nav.push("OLLAMA_CHECK")
            
            # ─────────────────────────────────────────────────────────────────────
            # OLLAMA SETUP
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "OLLAMA_CHECK":
                cprint("\n→ Checking Ollama server... ", Colors.CYAN, bold=True)
                if not is_ollama_running(timeout=4):
                    cprint("not detected", Colors.YELLOW)
                    logger.warning("Ollama not running; attempting start", "MAIN")
                    if not start_ollama_server():
                        logger.error("Failed to start Ollama", "MAIN")
                        cprint("✗ Could not start Ollama", Colors.RED)
                        cprint("  Make sure Ollama is installed: https://ollama.com/download", Colors.YELLOW)
                        input("Press Enter to return to main menu...")
                        nav.home()
                        continue
                    
                    if not wait_for_ollama(timeout=30):
                        logger.error("Ollama startup timeout", "MAIN")
                        cprint("✗ Ollama startup timeout", Colors.RED)
                        input("Press Enter to return to main menu...")
                        nav.home()
                        continue
                else:
                    cprint("✓ Already running", Colors.GREEN)
                    logger.info("Ollama is running", "MAIN")
                
                nav.push("MODEL_LOAD")
            
            # ─────────────────────────────────────────────────────────────────────
            # MODEL FETCHING
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "MODEL_LOAD":
                cprint("\n→ Loading available models... ", Colors.CYAN, bold=True)
                models = get_available_models()
                
                if not models:
                    logger.error("No models available", "MAIN")
                    cprint("none found", Colors.RED)
                    cprint("\nYou need to install a model first:", Colors.YELLOW)
                    cprint("  1. Open terminal/PowerShell", Colors.YELLOW)
                    cprint("  2. Run: ollama pull llama2", Colors.YELLOW)
                    cprint("  3. Try again", Colors.YELLOW)
                    input("\nPress Enter to return to main menu...")
                    nav.home()
                    continue
                
                cprint(f"✓ {len(models)} models found", Colors.GREEN)
                logger.info(f"Found {len(models)} models", "MAIN")
                
                nav.push("MODEL_SELECT")
            
            # ─────────────────────────────────────────────────────────────────────
            # MODEL SELECTION
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "MODEL_SELECT":
                print_centered_header("MODEL SELECTION", char="-", color=Colors.MAGENTA)
                
                grouped = defaultdict(list)
                for name in models:
                    grouped[get_model_family(name)].append(name)
                
                model_map = {}
                index = 1
                
                for family, items in sorted(grouped.items()):
                    cprint(f" ── {family} ──", Colors.CYAN, bold=True)
                    for name in sorted(items):
                        label = ""
                        cap = get_model_capability(name)
                        if cap != "Text-Only":
                            label = f" [{cap}]"
                        warn = " (Large)" if is_large_model(name) else ""
                        cprint(f"  {index}) {name}{label}{warn}", Colors.BRIGHT_WHITE)
                        model_map[index] = name
                        index += 1
                    print()
                
                cprint("  B) Back", Colors.YELLOW)
                cprint("  M) Main Menu", Colors.YELLOW)
                cprint("  Q) Quit", Colors.YELLOW)
                print()
                
                selected_model = None
                while selected_model is None:
                    choice = input(f"{Colors.YELLOW}Enter number or option: {Colors.RESET}").strip()
                    
                    if choice.upper() == "M":
                        nav.home()
                        break
                    elif choice.upper() == "B":
                        nav.pop()
                        break
                    elif choice.upper() == "Q":
                        logger.info("User quit during model selection", "MAIN")
                        sys.exit(0)
                    
                    try:
                        idx = int(choice)
                        if idx in model_map:
                            selected_model = model_map[idx]
                            logger.info(f"Selected model: {selected_model}", "MAIN")
                            cprint(f"✓ Model selected: {selected_model}", Colors.GREEN, bold=True)
                        else:
                            cprint("Invalid choice.", Colors.YELLOW)
                    except ValueError:
                        cprint("Invalid choice.", Colors.YELLOW)
                
                if selected_model is None:
                    continue
                
                nav.push("CONFIG")
            
            # ─────────────────────────────────────────────────────────────────────
            # CONFIGURATION
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "CONFIG":
                cprint("\n→ Generating configuration...", Colors.CYAN)
                config = configure_agent(
                    selected_backend,
                    selected_interpreter,
                    selected_model,
                    system_info
                )
                
                if not config:
                    logger.error("Configuration generation failed", "MAIN")
                    cprint("✗ Configuration failed", Colors.RED)
                    nav.home()
                    continue
                
                cprint("✓ Configuration complete", Colors.GREEN)
                logger.info(f"Config: {config['launch_mode']}", "MAIN")
                
                nav.push("LAUNCH")
            
            # ─────────────────────────────────────────────────────────────────────
            # LAUNCH
            # ─────────────────────────────────────────────────────────────────────
            
            elif nav.current() == "LAUNCH":
                if config["launch_mode"] == "terminal":
                    logger.section("Launching Terminal Session")
                    cprint("\nLaunching terminal session...", Colors.CYAN)
                    
                    interpreter = setup_interpreter(
                        config["model"],
                        runtime_config=config["ollama"]
                    )
                    
                    if not interpreter:
                        logger.error("Interpreter setup failed", "MAIN")
                        cprint("✗ Interpreter setup failed", Colors.RED)
                        input("Press Enter to return to main menu...")
                        nav.home()
                        continue
                    
                    print_centered_header("SESSION READY", char="-", color=Colors.GREEN)
                    cprint(f"Model: {config['model']}", Colors.CYAN)
                    logger.info("Session ready", "MAIN")
                    
                    run_chat_loop(interpreter)
                    nav.home()
                
                elif config["launch_mode"] == "browser":
                    logger.section("Launching OpenHands Browser UI")
                    cprint("\nLaunching OpenHands (browser UI)...", Colors.CYAN)
                    
                    success, url, message = launch_openhands_docker(
                        config["model"],
                        docker_config=config["docker"]
                    )
                    
                    if success:
                        cprint("✓ OpenHands ready!", Colors.GREEN, bold=True)
                        cprint(f"→ {message}", Colors.BRIGHT_WHITE)
                        logger.info(f"OpenHands launched: {url}", "MAIN")
                        
                        import webbrowser
                        try:
                            webbrowser.open(url)
                            logger.debug("Browser opened", "MAIN")
                        except Exception as e:
                            logger.warning(f"Could not open browser: {str(e)[:50]}", "MAIN")
                            cprint(f"Note: Open {url} in your browser manually", Colors.YELLOW)
                        
                        cprint("\nPress Ctrl+C when done or Enter to return to menu...", Colors.YELLOW)
                        try:
                            input()
                        except KeyboardInterrupt:
                            pass
                    else:
                        logger.warning(f"OpenHands launch failed: {message}", "MAIN")
                        cprint(f"✗ Launch failed: {message}", Colors.RED)
                        cprint("\nFalling back to terminal...", Colors.YELLOW)
                        
                        interpreter = setup_interpreter(
                            config["model"],
                            runtime_config=config["ollama"]
                        )
                        
                        if interpreter:
                            print_centered_header("SESSION READY (Fallback)", char="-", color=Colors.GREEN)
                            cprint(f"Model: {config['model']}", Colors.CYAN)
                            logger.info("Fallback to terminal", "MAIN")
                            run_chat_loop(interpreter)
                    
                    nav.home()
        
        logger.section("Session Complete")
        cprint("\n✓ Session ended gracefully", Colors.GREEN)
    
    except KeyboardInterrupt:
        logger.warning("User interrupted (Ctrl+C)", "MAIN")
        cprint("\n\n✗ Interrupted by user", Colors.YELLOW)
        sys.exit(0)
    
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", "MAIN")
        cprint(f"\n✗ CRITICAL ERROR: {str(e)[:100]}", Colors.RED, bold=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
