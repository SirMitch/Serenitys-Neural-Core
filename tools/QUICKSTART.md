# Neural AI Loader - Quick Start & Deployment

## What Was Fixed

Your original system was crashing after model selection due to **communication failures between modules**. This hardened version adds:

✓ **Comprehensive error handling** at every critical step  
✓ **Input validation** - all selections checked before proceeding  
✓ **Communication verification** - explicit checks between modules  
✓ **Graceful fallback** - if Docker fails, falls back to terminal  
✓ **Detailed logging** - easy to debug when things go wrong  

---

## Quick Start (5 minutes)

### 1. Backup Original Files

```batch
cd D:\OpenInturpter\Ollama
mkdir backup
copy *.py backup\
copy tools\*.py backup\
```

### 2. Deploy Hardened Files

Copy these files to your directories:

**In `D:\OpenInturpter\Ollama\`:**
- `neural_ai_loader.py` (main script)

**In `D:\OpenInturpter\Ollama\tools\`:**
- `system_info_helper.py`
- `ollama_helper.py`
- `configure_agent.py`
- `openhands_helper.py`
- `interpreter_helper.py`

**Keep existing files:**
- `gather_system_info.ps1` (unchanged)
- Any other files you need

### 3. Verify Setup

```batch
cd D:\OpenInturpter\Ollama
dir neural_ai_loader.py
dir tools\system_info_helper.py
```

### 4. Test System

```batch
python neural_ai_loader.py
```

Expected flow:
1. Gathers system info ✓
2. Prompts for backend (select 1 - Ollama)
3. Prompts for agent (select 1 or 2)
4. Starts/checks Ollama ✓
5. Lists available models
6. Prompts for model selection
7. Configures system ✓
8. Launches chat (terminal) or Docker (browser)

---

## Testing Individual Components

### Test System Info

```batch
python tools\system_info_helper.py --debug
```

Should show: OS, CPU cores, RAM, GPU, VRAM

**If fails:**
- Check PowerShell is in PATH: `powershell -V`
- Check `gather_system_info.ps1` exists
- Run PowerShell as Administrator once

### Test Ollama

```batch
python tools\ollama_helper.py --verbose
```

Should show:
- ✓ Docker available
- ✓ Ollama status
- ✓ Models found

**If fails:**
- Ensure Ollama installed: `ollama --version`
- Ensure Ollama running: `ollama serve` (in another terminal)
- Check port 11434: `netstat -an | findstr 11434`

### Test Configuration

```batch
python tools\configure_agent.py
```

Should output JSON with: ollama config, docker config, launch_mode

### Test Docker Integration

```batch
python tools\openhands_helper.py --verbose
```

Should show Docker checks and container startup

**If fails:**
- Ensure Docker Desktop running (Windows/Mac)
- Check: `docker ps`

### Test Interpreter

```batch
python tools\interpreter_helper.py --verbose
```

Should import Open Interpreter and warm up the model

**If fails:**
- Ensure Open Interpreter installed: `pip install open-interpreter`

### Test Complete System

```batch
python neural_ai_loader.py
```

Go through entire flow:
1. View system specs
2. Select Ollama backend
3. Select interpreter (terminal or Docker)
4. Select a model
5. See configuration
6. Chat or Docker launch

---

## Deployment Steps

### Option A: Drop-in Replacement (Recommended)

1. Backup originals (see above)
2. Copy new files to same directories
3. Run `python neural_ai_loader.py`

No changes needed to paths or imports.

### Option B: Fresh Install

1. Create `D:\OpenInturpter\Ollama\` directory
2. Copy all `.py` files there and to `tools\` subdirectory
3. Copy `gather_system_info.ps1` to `tools\`
4. Run `python neural_ai_loader.py`

### Option C: Integration with Existing Code

If you have other scripts that import these helpers:

**Old code:**
```python
from ollama_helper import is_ollama_running
from system_info_helper import get_system_info
```

**Still works!** All function signatures unchanged, just more robust.

---

## What Changed (Technical Details)

### system_info_helper.py
- ✓ Added timeout (30s max)
- ✓ Validate critical fields before returning
- ✓ Safe numeric conversion with defaults
- ✓ Better error messages

### ollama_helper.py
- ✓ Added verbose logging
- ✓ Health check before polling
- ✓ Proper error classification
- ✓ API response validation

### configure_agent.py
- ✓ Input validation (check dict structure)
- ✓ Bounds checking (cores, RAM, etc.)
- ✓ Fallback config if any step fails
- ✓ Model capability analysis

### openhands_helper.py
- ✓ Refactored as DockerManager class
- ✓ Two-level Docker checks
- ✓ Stale container cleanup
- ✓ Image pull validation
- ✓ Container wait loop

### interpreter_helper.py
- ✓ pkg_resources mock (Windows fix)
- ✓ Step-by-step configuration logging
- ✓ Pre-warm validation
- ✓ Chat loop resilience (error counter)
- ✓ Graceful shutdown

### neural_ai_loader.py
- ✓ Helper loading validation
- ✓ Input validation loops
- ✓ Configuration validation
- ✓ Docker fallback to terminal
- ✓ Comprehensive error handling

---

## Troubleshooting

### Script Hangs on "Gathering system information"

**Cause:** PowerShell timeout  
**Fix:** 
- Open PowerShell as Administrator
- Run any command once to initialize
- Try script again

### "Failed to retrieve system info"

**Cause:** gather_system_info.ps1 not found or not accessible  
**Fix:**
- Verify file exists: `dir tools\gather_system_info.ps1`
- Check permissions: Right-click → Properties → Security
- Try running script directly: `powershell -File tools\gather_system_info.ps1`

### "Ollama not responding"

**Cause:** Ollama server not running  
**Fix:**
- Start Ollama: `ollama serve` (in new terminal)
- Wait 10 seconds
- Run script again

### "No models available"

**Cause:** No models installed in Ollama  
**Fix:**
- Install a model: `ollama pull llama2`
- List models: `ollama list`
- Try script again

### "Docker not found" or "Docker daemon not running"

**Cause:** Docker not installed or not started  
**Fix:**
- Install Docker: https://docker.com/products/docker-desktop
- Start Docker Desktop (Windows/Mac)
- Try script again

### Script crashes after model selection

**This was the original bug.** Should be fixed now.

**If still happening:**
- Run with debug: Add `verbose=True` to helper calls in neural_ai_loader.py
- Check system info: `python tools\system_info_helper.py --debug`
- Check config: `python tools\configure_agent.py`

---

## Key Improvements in Action

### Before (Original)
```
→ Select model
✓ Model selected: llama2:latest
→ Running configuration wizard...
[CRASH - no error message]
```

### After (Hardened)
```
→ Select model
✓ Model selected: llama2:latest
→ Running configuration wizard...
[CONFIG] Backend: ollama
[CONFIG] Interpreter: open_interpreter
[CONFIG] Model: llama2:latest
[CONFIG] CPU Cores: 8
[CONFIG] RAM: 16 GB
[CONFIG] Ollama GPU layers: 8
[CONFIG] Ollama threads: 7
[CONFIG] Ollama context: 8192
[CONFIG] Docker memory: 8g
[CONFIG] Docker CPUs: 8
✓ Configuration generated successfully

→ Launching terminal session...
✓ Open Interpreter imported successfully
→ Configuring interpreter...
  Model: ollama/llama2:latest
  API Base: http://localhost:11434
✓ Interpreter configured

→ Warming up model...
✓ Model warmed up

SESSION READY
Model: llama2:latest

You: [ready for input]
```

---

## Performance Notes

### First Run
- System info gathering: 2-3 seconds
- Ollama startup: 5-15 seconds
- Model warm-up: 30 seconds to 3 minutes (depends on model size)
- Total: ~1-5 minutes first time

### Subsequent Runs
- System info gathering: 2 seconds
- Ollama already running: 0 seconds
- Model already loaded: 0 seconds
- Total: ~2 seconds to ready

---

## Monitoring & Logs

### Verbose Output

All helpers support `--verbose` or `--debug`:

```batch
python tools\ollama_helper.py --verbose
python tools\openhands_helper.py --verbose
python tools\interpreter_helper.py --verbose
```

### Docker Logs

Check OpenHands container:
```batch
docker logs neural-openhands
docker logs neural-openhands --follow  # Live tail
```

### Ollama Logs

Run in foreground to see logs:
```batch
ollama serve
```

### Port Checking

Verify ports are accessible:
```batch
netstat -an | findstr 11434  # Ollama
netstat -an | findstr 3000   # OpenHands
```

---

## Next Steps

1. **Deploy files** (see Quick Start above)
2. **Test individual components** (see Testing section)
3. **Run full system** `python neural_ai_loader.py`
4. **Check HARDENING_GUIDE.md** for detailed technical info
5. **Monitor first runs** and check logs if issues

---

## File Checklist

### Required Files (Must Have)

- [ ] `neural_ai_loader.py` - Main script
- [ ] `tools/system_info_helper.py` - System info gathering
- [ ] `tools/ollama_helper.py` - Ollama management
- [ ] `tools/configure_agent.py` - Configuration wizard
- [ ] `tools/openhands_helper.py` - Docker integration
- [ ] `tools/interpreter_helper.py` - LLM chat setup
- [ ] `tools/gather_system_info.ps1` - System info PowerShell

### Optional Files (For Reference)

- [ ] `HARDENING_GUIDE.md` - Detailed technical guide
- [ ] `docker_code_server_helper.py` - Code server (not used by main script)
- [ ] `list_models.py` - Standalone model lister

---

## Support

If issues persist:

1. **Check HARDENING_GUIDE.md** - Section "Debugging Guide"
2. **Run with verbose output** - Each helper supports `--verbose`
3. **Check Docker/Ollama logs** - Run in foreground to see errors
4. **Verify prerequisites:**
   - Ollama installed & running
   - Docker Desktop running (if using OpenHands)
   - PowerShell accessible
   - Internet connection (for Docker image pull)

---

## Version Info

- **Original System:** Neural AI Loader (crashed on configure_agent)
- **Hardened Version:** 2.0 (comprehensive error handling & fallbacks)
- **Date:** February 2026
- **Status:** Production-ready with debugging support

---

Good luck! Your system should now be robust and informative about any issues. 🚀

