# Quick Start Guide - Neural AI Loader (Hardened)

## Installation (5 minutes)

### Step 1: Organize Files
```
C:\YourPath\ProjectRoot\
├── neural_ai_loader.py              ← Main launcher
└── tools\
    ├── logging_helper.py
    ├── nav_helper.py
    ├── system_info_helper.py
    ├── ollama_helper.py
    ├── interpreter_helper.py
    ├── openhands_helper.py
    ├── configure_agent.py
    └── gather_system_info.ps1
```

The `logs\` directory will be created automatically.

### Step 2: Run
```bash
cd C:\YourPath\ProjectRoot
python neural_ai_loader.py
```

### Step 3: Answer Prompts
```
Enable debug mode? (y/n): n
```

Choose your backend, interpreter, and model.

Done! Logs are in `ProjectRoot\logs\`

---

## Debug Mode

### Enable Debug (Verbose Logging)
```bash
python neural_ai_loader.py
Enable debug mode? (y/n): y
```

**What you see:**
- Program header: `Neural AI Loader (debug)`
- DEBUG messages in terminal (like "Ollama check: running")
- All logs in `logs\neural_ai_*.log`
- All errors in `logs\errors_*.log`

### Disable Debug (Production)
```bash
python neural_ai_loader.py
Enable debug mode? (y/n): n
```

**What you see:**
- Program header: `Neural AI Loader`
- No DEBUG messages in terminal
- INFO/WARN/ERROR/CRITICAL shown
- Logs still written to `logs\` (including DEBUG level)

---

## File Structure

### Main Launcher
**neural_ai_loader.py** (500 lines)
- Entry point with full flow control
- Debug mode selection
- System info gathering
- Backend/interpreter selection
- Ollama management
- Model selection with grouping
- Launch terminal or OpenHands

### Core Logging
**logging_helper.py** (100 lines)
- `Logger` class with file + console output
- Respects debug_mode flag
- Timestamps, module names, colored output
- Safe file writing (no crashes)

### Navigation (Optional)
**nav_helper.py** (30 lines)
- `NavState` class for menu history
- Helper for future back/home implementation
- Not currently used in main flow

### System Detection
**system_info_helper.py** (80 lines)
- PowerShell script wrapper (root-relative)
- Timeout handling (15s)
- Safe parsing with error recovery
- Logging integration

### Backend Services
**ollama_helper.py** (120 lines)
- Start/stop Ollama
- Poll for readiness
- Fetch available models
- All with timeout + logging

### User Interface
**interpreter_helper.py** (140 lines)
- Setup Open Interpreter
- Apply runtime_config (gpu_layers, context_size)
- Pre-warm model
- Chat loop with 'back' support

### Docker Integration
**openhands_helper.py** (180 lines)
- Docker availability check
- Image pulling (300s timeout)
- Container lifecycle
- Workspace path detection
- Full docker_config support

### Configuration
**configure_agent.py** (100 lines)
- Analyze system specs
- Calculate Ollama settings
- Calculate Docker settings
- Safe fallback config
- All with logging

### System Info Collection
**gather_system_info.ps1** (80 lines)
- PowerShell script (unchanged)
- Gathers: OS, CPU, RAM, GPU/VRAM
- Key=value output for Python parsing
- Supports -DebugMode flag

---

## Crash Root Causes (Fixed)

### 1. Hard-Coded Paths
**Was:** `D:\\OpenInturpter` hard-coded everywhere
**Now:** Dynamic resolution from script root

**Fix in:** neural_ai_loader.py, openhands_helper.py
```python
SCRIPT_ROOT = Path(__file__).resolve().parent
TOOLS_DIR = SCRIPT_ROOT / "tools"
```

### 2. Missing Parameters
**Was:** runtime_config passed but ignored
**Now:** Properly applied in setup_interpreter

**Fix in:** interpreter_helper.py
```python
context_size = runtime_config.get("context_size", 8000)
interpreter.llm.context_window = context_size
```

### 3. No Timeout Handling
**Was:** Subprocess calls could hang forever
**Now:** All calls have timeouts

**Fix in:** all helpers (ollama, system_info, openhands)
```python
subprocess.run(..., timeout=15)
```

### 4. Silent Failures
**Was:** Exceptions swallowed, no error visibility
**Now:** All exceptions logged + displayed

**Fix in:** logging_helper.py
```python
logger.error(msg, module, exc_info=True)
```

### 5. No Path Validation
**Was:** Workspace paths hard-coded
**Now:** Multiple fallback paths tried

**Fix in:** openhands_helper.py
```python
workspace_paths = [
    "D:\\OpenInturpter",
    os.path.join(os.path.expanduser("~"), "OpenInterpreter"),
    str(Path.cwd()),
]
```

---

## Log Files

### Example: `logs\neural_ai_20250219_143022.log`
```
================================================================================
Neural AI Loader - Session Log
Started: 2025-02-19T14:30:22.123456
Debug: True
================================================================================

[14:30:23] [INFO   ] [MAIN                 ] Script root: C:\Project
[14:30:23] [INFO   ] [MAIN                 ] Tools dir: C:\Project\tools
[14:30:23] [DEBUG  ] [SYSINFO             ] Running system info script: ...
[14:30:24] [INFO   ] [SYSINFO             ] System info gathered: 9 properties
[14:30:24] [INFO   ] [MAIN                 ] System: OS=Windows 10, CPU=8c, RAM=16GB
[14:30:24] [DEBUG  ] [OLLAMA              ] Ollama check: running
[14:30:25] [INFO   ] [OLLAMA              ] Found 3 models
[14:30:26] [INFO   ] [MAIN                 ] Selected model: llama2
[14:30:26] [INFO   ] [CONFIG              ] Configuring: Open Interpreter + llama2
[14:30:27] [INFO   ] [INTERPRETER         ] Setting up interpreter for model: llama2
[14:30:28] [INFO   ] [SESSION READY]
```

### Example: `logs\errors_20250219_143022.log`
```
[14:30:45] [ERROR  ] [OPENHANDS          ] Failed to pull image: ...
[14:30:46] [ERROR  ] [OPENHANDS          ] Docker run failed: container already exists
```

---

## Troubleshooting

### "Docker not found or not running"
- Check Docker Desktop is running
- On Windows: Start Docker Desktop app

### "Ollama failed to start"
- Download from https://ollama.com/download
- Ensure ollama command is in PATH
- Enable debug mode to see startup logs

### "No models found"
- Run: `ollama list`
- Pull a model: `ollama pull llama2`

### "Timeout waiting for Ollama"
- Ollama is slow on first startup
- Add more RAM or close other apps
- Check logs for details

### Program "just closes" (was original issue)
- This is now prevented by:
  1. Exception catching at all levels
  2. Logging before exits
  3. Graceful fallback configs
- Check logs\ for crash details

### "gather_system_info.ps1 not found"
- Verify file is in `tools\` directory
- Check path is correct (should be root-relative)
- Run with debug mode to see exact path

### "PowerShell not found"
- Windows includes PowerShell by default
- Check PATH: `powershell -Version`

### "AttributeError: 'NoneType'" in chat
- Interpreter setup failed (see logs)
- Check Ollama is running
- Try with smaller model

---

## Performance Tips

1. **First Run:** Model warming takes 5-30s (normal)
2. **GPU:** Configure gpu_layers in ollama config
3. **Memory:** Increase context_size if you have 32GB+ RAM
4. **Timeout:** Increase timeout values in helpers if slow network

---

## File Permission Issues (Windows)

If you get "Access Denied" errors:
1. Run PowerShell as Administrator
2. Check `logs\` directory is writable
3. Ensure `tools\` files are readable

---

## Next Steps

1. Review IMPLEMENTATION_SUMMARY.md for all changes
2. Check logs\ after first run to verify logging works
3. Enable debug mode and review DEBUG output
4. Test with different models/interpreters
5. Test Ctrl+C interrupt handling
6. Verify workspace path detection in logs

---

## Support

All failures are logged to:
- `logs\neural_ai_YYYYMMDD_HHMMSS.log` (full)
- `logs\errors_YYYYMMDD_HHMMSS.log` (errors only)

Enable debug mode for maximum visibility of internal operations.
