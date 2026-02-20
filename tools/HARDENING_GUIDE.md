# Neural AI Loader - Hardening Guide

## Executive Summary

This document outlines the comprehensive hardening pass applied to the Neural AI Loader system. The original system was crashing after model selection, likely due to communication failures between modules and missing error handling. All files have been rebuilt with:

1. **Robust error handling** - try/except blocks at all critical junctures
2. **Input validation** - all user inputs and inter-module data checked
3. **Communication verification** - explicit checks for subprocess/API responses
4. **Fallback strategies** - graceful degradation when features unavailable
5. **Enhanced logging** - verbose modes for debugging
6. **Type safety** - safe type conversions with defaults

---

## File-by-File Changes

### 1. system_info_helper.py

**Problems Fixed:**
- PowerShell script execution could fail silently
- No validation of retrieved system info
- Parsing errors not caught
- Numeric conversions unsafe

**Key Improvements:**
```python
✓ Timeout protection (30s max)
✓ Detailed error reporting (exit code, stderr, output)
✓ Parse validation - checks for required keys
✓ Safe numeric conversion - fallback defaults
✓ Graceful handling when PowerShell unavailable
✓ Debug mode for troubleshooting
```

**Testing:**
```bash
python system_info_helper.py --debug
```

**Expected Output:**
```
[DEBUG] Running: powershell ...
[DEBUG] System info parsed successfully
[DEBUG] Keys retrieved: CPU_CORES, RAM_GB, ...
✓ System Info Retrieved:
  CPU_CORES: 8
  RAM_GB: 16
  ...
```

---

### 2. ollama_helper.py

**Problems Fixed:**
- No retry logic when Ollama starts slowly
- Unclear connection errors
- `get_available_models()` fails silently
- No distinction between "not running" and "not responding"

**Key Improvements:**
```python
✓ Health check with timeout (4-5s)
✓ Startup with background process management
✓ Polling with configurable retry (default 30s, 2s intervals)
✓ Detailed verbose logging at each step
✓ Proper error classification (ConnectionError vs Timeout)
✓ API response validation
```

**Critical Functions:**

`is_ollama_running(timeout=5, verbose=False)`
- Returns bool (True = 200 response)
- Tries GET http://localhost:11434
- Returns False on any error (connection, timeout, non-200)

`start_ollama_server(verbose=False)`
- Windows: DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP
- Unix: start_new_session=True
- Returns True if process launched (doesn't verify it started)

`wait_for_ollama(timeout=30, check_interval=2, verbose=False)`
- Polls until is_ollama_running() returns True
- Timeout default: 30s
- Check interval default: 2s

`get_available_models(verbose=False)`
- Requires is_ollama_running() = True first
- Fetches from /api/tags endpoint
- Returns list of model names
- Empty list on any error (safe fallback)

**Testing:**
```bash
python ollama_helper.py --verbose
```

---

### 3. configure_agent.py

**Problems Fixed:**
- No validation of input dictionaries
- Unsafe type conversions (could crash on unexpected types)
- No bounds checking on numeric values (negative cores, etc.)
- Silent failures → returned invalid config

**Key Improvements:**
```python
✓ Input validation - check dict structure, not None
✓ Safe numeric conversion - safe_int(value, default, min_val, max_val)
✓ Bounds checking - CPU cores 1-256, RAM 1-1024 GB, etc.
✓ Model analysis - parse capabilities from name
✓ Fallback config - returns safe defaults if any step fails
✓ Verbose logging - show each calculation step
```

**Configuration Logic:**

**Ollama Tuning:**
- GPU layers: `min(80, vram_mb // 256)` (aim for 256MB/layer)
- Threads: `max(2, cpu_cores - 1)`
- Context: 2048→4096→8192→16384 based on RAM
- Vision models: minimum 4096 context

**Docker Configuration:**
- Memory: `max(4, ram_gb // 2)` (half system RAM, min 4GB)
- CPUs: `min(cpu_cores, 16)` (practical limit)
- Vision flag: detected from model name

**Testing:**
```python
python configure_agent.py
# or in Python:
from configure_agent import configure_agent
config = configure_agent(backend, interpreter, model, system_info, verbose=True)
```

---

### 4. openhands_helper.py

**Problems Fixed:**
- Docker daemon check insufficient
- No cleanup of stale containers
- Image pull timeout possible
- Container startup not validated
- Windows path handling fragile

**Key Improvements:**
```python
✓ DockerManager class - encapsulates all Docker operations
✓ Two-level Docker checks:
  - docker_available() - is docker command accessible
  - docker_daemon_running() - is daemon actually running
✓ Stale container cleanup - removes old instances
✓ Image pull validation - checks if image exists first
✓ Container wait loop - validates container actually starts
✓ Windows-safe paths - uses USERPROFILE env var
✓ Network host gateway - allows container→host communication
```

**Docker Operation Sequence:**
1. Check Docker installed & daemon running
2. Check if container already running (success if yes)
3. Remove any stale container
4. Ensure image available (pull if missing)
5. Prepare volumes & environment
6. Launch container with configuration
7. Wait up to 30s for container to start

**Critical Function:**
```python
launch_openhands_docker(
    model_name: str,
    docker_config: dict = None,
    verbose: bool = False
) -> (bool, str|None, str)
```

Returns: `(success, url_or_none, message)`

**Testing:**
```bash
python openhands_helper.py --verbose
```

**Example Output:**
```
→ Checking Docker installation...
✓ Docker is installed
✓ Docker daemon is running
✓ Container already running
OpenHands already running → http://localhost:3000
```

---

### 5. interpreter_helper.py

**Problems Fixed:**
- Import failures not caught (pkg_resources)
- Configuration errors silent
- No pre-warm validation
- Chat loop crashes on connection loss
- No error counting / early exit

**Key Improvements:**
```python
✓ pkg_resources mock - prevent Windows import errors
✓ Configuration step-by-step - validate each setting
✓ Pre-warm with timeout - catch cold-start issues
✓ Chat loop resilience:
  - Catches ConnectionError (Ollama down)
  - Catches TimeoutError (model overloaded)
  - Counts consecutive errors (exit after 3)
  - Continues on non-fatal errors
✓ Graceful exits - Ctrl+C, EOF, exit commands
✓ Message tracking - logs session statistics
```

**Setup Function:**
```python
setup_interpreter(
    selected_model: str,
    api_base: str = "http://localhost:11434",
    api_key: str = "fake_key",
    context_window: int = 8000,
    max_tokens: int = 2000,
    verbose: bool = False
) -> interpreter | None
```

Returns: Configured interpreter or None if setup fails

**Chat Loop Resilience:**
```
User input → Validate → Send to interpreter
  ├─ Success → Reset error counter
  ├─ Connection error → Increment counter, suggest fix
  ├─ Timeout error → Increment counter, suggest model issue
  ├─ Other error → Increment counter, show traceback (verbose)
  └─ 3 consecutive errors → Exit loop
```

**Testing:**
```bash
python interpreter_helper.py --verbose
```

---

### 6. neural_ai_loader.py (Main Script)

**Problems Fixed:**
- No validation that helpers loaded
- Selection input not validated
- Error in configure_agent → crash
- No fallback if Docker fails
- No comprehensive error handling

**Key Improvements:**
```python
✓ Helper loading validation - checks all imports succeed
✓ Input validation loop - won't proceed until valid selection
✓ System info validation - exits if critical data missing
✓ Configuration validation - checks output not None
✓ Docker fallback - if Docker launch fails, try terminal
✓ Comprehensive try/except - catches all critical errors
✓ Graceful shutdown - Ctrl+C handled cleanly
✓ Full traceback on critical errors
```

**Execution Flow:**
```
1. Load helpers (validate all imports)
2. Gather system info (exit if critical fields missing)
3. Select backend (loop until valid choice)
4. Select interpreter (loop until valid choice)
5. Check Ollama running (start if needed)
6. Load available models (exit if none)
7. Select model (loop until valid)
8. Configure agent (validate config returned)
9. Launch:
   - If terminal: setup_interpreter → run_chat_loop
   - If browser: launch_openhands_docker
     - Success: open in browser
     - Failure: fallback to terminal
```

**Testing Complete System:**
```bash
cd D:\OpenInturpter\Ollama
python neural_ai_loader.py
```

---

## Communication Verification

### Module → Module Communication

All inter-module calls now include validation:

**system_info_helper → main:**
- Returns dict with required keys or None
- Main checks: `if system_info: ... else: sys.exit(1)`

**ollama_helper → main:**
- `is_ollama_running()` → bool (always valid)
- `get_available_models()` → list (safe, empty if error)
- `wait_for_ollama()` → bool (True/False, no exceptions)

**configure_agent → main:**
- Returns dict with all required keys
- Fallback dict returned if ANY step fails
- Main checks: `if not config: sys.exit(1)`

**openhands_helper → main:**
- Returns tuple: (bool, str|None, str)
- Main unpacks and checks bool before using url

**interpreter_helper → main:**
- `setup_interpreter()` → object|None
- Main checks: `if interpreter_instance is None: sys.exit(1)`
- `run_chat_loop()` → None (side-effect only)

### Subprocess Communication

**PowerShell calls:**
```python
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=30,
    check=False  # Don't raise on non-zero exit
)

if result.returncode != 0:
    # Handle error
if not result.stdout.strip():
    # Handle no output
```

**Docker calls:**
```python
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=60
)

if result.returncode != 0:
    # Handle error
if "container_name" in result.stdout:
    # Check succeeded
```

**Ollama API calls:**
```python
try:
    response = requests.get(url, timeout=8)
    if response.status_code != 200:
        # Handle non-200
    data = response.json()
    # Validate data structure
except requests.RequestException as e:
    # Handle connection/timeout
except (ValueError, KeyError) as e:
    # Handle JSON parse error
```

---

## Debugging Guide

### Enable Verbose Logging

**For individual helpers:**
```bash
python system_info_helper.py --debug
python ollama_helper.py --verbose
python openhands_helper.py --verbose
python interpreter_helper.py --verbose
```

**In main script (modification needed):**
```python
# Add verbose=True to helper calls:
system_info = helpers["get_system_info"](debug=True)
# etc.
```

### Common Failure Points

**1. PowerShell System Info**
```
Symptom: "Failed to retrieve system info"
Check:
- PowerShell in PATH: powershell -V
- gather_system_info.ps1 exists
- Windows permission to run PowerShell scripts
Fix: Run PowerShell as Administrator once, then retry
```

**2. Ollama Not Responding**
```
Symptom: "Ollama failed to start within 30s"
Check:
- Ollama installed: ollama --version
- Port 11434 not blocked: netstat -an | findstr 11434
- No other process using port
Fix: 
- Manually start: ollama serve
- Check firewall rules
- Restart Docker Desktop (if on Docker)
```

**3. Models Not Found**
```
Symptom: "No models available"
Check:
- Ollama running: curl http://localhost:11434
- Models installed: ollama list
Fix: Pull a model: ollama pull llama2
```

**4. Docker Not Available**
```
Symptom: "Docker not found" or "Docker daemon not running"
Check:
- Docker installed: docker --version
- Docker Desktop running (Windows/Mac)
- Docker daemon running (Linux): systemctl status docker
Fix: Install Docker or start Docker Desktop
```

**5. Configure Agent Fails**
```
Symptom: "Configuration failed"
Check:
- System info gathered correctly
- Selected model is valid string
- No None values in selections
Fix: Check system_info output, retry model selection
```

---

## Performance Tuning

### Ollama Tuning (configure_agent.py)

**GPU Layers:**
- Formula: `min(80, vram_mb // 256)`
- Adjust divisor for different VRAM:
  - 128: more layers, less VRAM per layer (slower)
  - 512: fewer layers, more VRAM per layer (faster)

**Threads:**
- Formula: `cpu_cores - 1`
- Increase if CPU not at 100% (more parallelism)
- Decrease if context overflow (fewer threads = less memory)

**Context Size:**
- Start at 4096, increase if you have RAM
- Vision models: minimum 4096
- Large models (70B): consider 8192 limit

### Docker Tuning (openhands_helper.py)

**Memory Limit:**
- Current: half of system RAM (min 4GB)
- Increase for heavy workloads
- Cap at 75% system RAM (leave 25% for host)

**CPU Limit:**
- Current: all cores (capped at 16)
- Reduce if host performance affected
- Minimum 2 cores recommended

---

## Testing Checklist

- [ ] Run `python system_info_helper.py --debug` → verify all fields
- [ ] Run `python ollama_helper.py --verbose` → verify startup/models
- [ ] Run `python configure_agent.py` → verify config structure
- [ ] Run `python openhands_helper.py --verbose` → verify Docker integration
- [ ] Run `python interpreter_helper.py --verbose` → verify LLM setup
- [ ] Run full `python neural_ai_loader.py` → end-to-end test
  - Select backend (Ollama)
  - Select interpreter (both options)
  - Select model
  - Verify configuration
  - Test chat loop (if terminal)
  - Test Docker launch (if browser)

---

## Deployment

1. **Backup original files:**
   ```bash
   cd D:\OpenInturpter\Ollama\tools
   for %%f in (*.py) do copy %%f %%f.backup
   ```

2. **Copy hardened files:**
   ```bash
   copy neural_ai_loader.py D:\OpenInturpter\Ollama\
   copy system_info_helper.py D:\OpenInturpter\Ollama\tools\
   copy ollama_helper.py D:\OpenInturpter\Ollama\tools\
   copy configure_agent.py D:\OpenInturpter\Ollama\tools\
   copy openhands_helper.py D:\OpenInturpter\Ollama\tools\
   copy interpreter_helper.py D:\OpenInturpter\Ollama\tools\
   ```

3. **Verify gather_system_info.ps1 exists:**
   ```bash
   dir D:\OpenInturpter\Ollama\tools\gather_system_info.ps1
   ```

4. **Test:**
   ```bash
   cd D:\OpenInturpter\Ollama
   python neural_ai_loader.py
   ```

---

## Summary of Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| PowerShell timeout | Hangs on sys info | Added 30s timeout + error handling |
| Type safety | Crashes on unexpected types | Added safe_int(), type checks |
| Silent failures | Hard to debug | Added detailed error messages + verbose modes |
| Missing validation | Invalid config passes through | Added input validation + fallback configs |
| Docker daemon check | Assumes Docker running | Added two-level check (installed + running) |
| Stale containers | Port conflicts | Added automatic cleanup of old containers |
| Connection errors | Chat loop crashes | Added ConnectionError handling + error counter |
| Model selection crash | Exits after model pick | Fixed configure_agent → returns valid dict always |
| No fallback | Docker fail = total fail | Added terminal fallback for OpenHands |
| Communication unclear | Which module failed? | Added detailed logging at each step |

---

## What to Monitor

After deployment, monitor these areas:

1. **System Info Gathering** - Verify reported specs match actual
2. **Ollama Startup** - Note time to become ready (should be <20s)
3. **Model Loading** - Track VRAM usage vs predicted
4. **Docker Startup** - Verify OpenHands launches in <30s
5. **Chat Performance** - Monitor response latency, error rate

---

## Future Improvements

1. **Persistent Configuration** - Save settings between runs
2. **Connection Pooling** - Reuse HTTP connections
3. **Resource Monitoring** - Real-time VRAM/CPU display
4. **Model Versioning** - Track which version loaded
5. **Web UI** - Replace terminal menu with browser-based setup
6. **Metrics Export** - Prometheus/Grafana integration

---

## Support

For issues:
1. Run helpers with `--verbose` or `--debug`
2. Check Docker logs: `docker logs neural-openhands`
3. Check Ollama logs: `ollama serve` (in foreground)
4. Verify ports: `netstat -an | findstr 11434` (Ollama) / `3000` (OpenHands)

