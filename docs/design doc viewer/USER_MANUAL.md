# USER_MANUAL.md — AlphaChart/Serenity User Guide

**Date**: 2026-05-03  
**Session**: 30 (1 Sev Pass)  
**Mode**: NON-MICRO-LLM MODE  
**Status**: COMPLETE

## Executive Summary

User guide for AlphaChart/Serenity system. Covers quick start, features, workflows, and FAQ. Integrated into ADDR system for searchable access via MCP tools.

## Quick Start

### First-Time Setup
1. **Install Prerequisites**: Python 3.11+, pip, git
2. **Clone Repository**: `git clone <repo-url> AlphaChart`
3. **Set up Venv**: `python -m venv finrlx` (already present)
4. **Install Dependencies**: `pip install -r requirements.txt`
5. **Run GUI**: `streamlit run ui/app.py --server.port 8501`
6. **Open Browser**: `http://localhost:8501`

### Verifying Installation
- **MCP Server**: `python core/mcp/alphachat_mcp_server.py` (should start on port 8006)
- **Memory Tests**: `python test_memory_layers.py` (expect 9/9 PASS)
- **Integration Tests**: `python test_new_modules_integration.py` (expect 3/3 PASS)

## Features Overview

### 1. Predictor Tab (Day/Swing/Position Trading)
- **Select Ticker**: Type in search bar or select from watchlist
- **Adjust Horizon**: DAY (1 day, 0.5% threshold), SWING (5 days, 2% threshold), POSITION (20 days, 5% threshold)
- **Model Training**: Click "Train Model" (uses AAPL data 2018-2024, Future Days=1)
- **Get Prediction**: Click "Get Prediction" (shows signal, confidence, chart)
- **Adjust Thresholds**: Use sidebar sliders (Day: 0.1-3.0%, Swing: 0.5-10.0%, Position: 1.0-15.0%)

### 2. Portfolio & Scanner Tab
- **Single Ticker Scan**: Enter ticker, click "Scan Ticker" (uses full pipeline: regime → ensemble → safety → quality)
- **Watchlist Rotation**: Enable "Auto-Scan Watchlist" (scans every 15 minutes)
- **Market-Wide Scan**: Enable "Market-Wide Scan" (scans SP500/NASDAQ100/RUSSELL2000)
- **View Results**: Table shows ticker, direction, conviction, horizon, price, regime
- **Approve/Reject**: Use "Quick Approve All" or individual buttons
- **Alerts**: Global alert bar shows top 3 high-conviction signals (DAY/SWING/POSITION auto-classified)

### 3. Paper Trading Tab
- **Account Summary**: View equity, cash, buying power, day P&L
- **Pending Approvals**: Review signals awaiting approval, approve/reject individually or "Quick Approve All"
- **Open Positions**: View current holdings with entry price, current price, P&L
- **Trade History**: View closed trades with P&L, win rate, average win/loss

### 4. Performance Tab
- **KPIs**: Total trades, win rate, average win, average loss, profit factor
- **Equity Curve**: Plot of cumulative P&L over time (real data from OrderManager)
- **Win Rate by Regime**: Bar chart of win rates across TRENDING_UP/TRENDING_DOWN/SIDEWAYS

### 5. Learning Tab
- **RAG Memory Stats**: View stored episodes, facts, reflections, concepts (ChromaDB)
- **Serenity Calibration**: View calibration table (expected vs actual win rates)
- **Background Learning**: System continuously observes, records patterns, injects optimization hints

## Common Workflows

### Day Trading Workflow
1. Open **Predictor Tab**
2. Select ticker (e.g., AAPL)
3. Set horizon to **DAY** (1 day, 0.5% threshold)
4. Click **Train Model** (wait ~30 seconds)
5. Click **Get Prediction** (view signal: BUY/SELL/HOLD, confidence)
6. If BUY/SELL with high conviction (>0.8), go to **Paper Trading Tab**
7. Approve pending signal, monitor open position

### Market Scanning Workflow
1. Open **Portfolio & Scanner Tab**
2. Enable **Auto-Scan Watchlist** (runs every 15 minutes)
3. View **Alert Bar** at top (top 3 high-conviction signals)
4. Review **Scanner Results Table** (ticker, direction, conviction, regime)
5. Approve signals manually or use **Quick Approve All**
6. Monitor approved trades in **Paper Trading Tab**

### Model Retraining Workflow
1. Open **Predictor Tab**
2. Adjust **Future Days** slider (1-20 days)
3. Adjust **Threshold** slider (0.1-15.0%)
4. Click **Train Model** (uses data 2018-2024, retrains ensemble)
5. Click **Get Prediction** (verify improved signal quality)
6. Check **Performance Tab** for updated win rate, Sharpe ratio

## Advanced Settings

### Thresholds & Conviction
- **Day Trading**: 0.1-3.0% threshold (default 0.5%), conviction >0.8
- **Swing Trading**: 0.5-10.0% threshold (default 2.0%), conviction >0.7
- **Position Trading**: 1.0-15.0% threshold (default 5.0%), conviction >0.6
- **Alert Min Conviction**: 0.8 (default), adjust in sidebar
- **Alert Min Quality**: 0.75 (default), adjust in sidebar

### Regime Filter Strictness
- **OFF**: Ignore regime in signal generation
- **SOFT**: Adjust weights based on regime (default)
- **HARD**: Block trades in TRENDING_DOWN regime

### Background Scanning
- **Enable**: Toggle "Background Scan" in sidebar
- **Interval**: 15 minutes (default), adjust in code `background_scan_interval`
- **Alert Deduplication**: Max 1 alert per ticker per hour (3600s)

## FAQ

### Why is my prediction always HOLD?
- **Cause**: Threshold too high, conviction too low
- **Fix**: Lower threshold slider, retrain model with different Future Days (1-5)

### Why does the scanner return no results?
- **Cause**: Min conviction/quality too high, all signals blocked
- **Fix**: Lower "Alert Min Conviction" (0.8 → 0.6), "Alert Min Quality" (0.75 → 0.6)

### Why does the MCP server fail to start?
- **Cause**: Missing `fastmcp` package (not `mcp`)
- **Fix**: `pip install fastmcp`, verify `from fastmcp import FastMCP`

### Why do tests fail with Unicode errors?
- **Cause**: Windows cp1252 encoding can't handle non-ASCII
- **Fix**: Use ASCII-only in markdown files, avoid emojis in bash output

### How do I backup the system?
- **Manual**: Copy entire AlphaChart folder to backup location
- **Scripted**: `robocopy /E /XD __pycache__ /XF *.bak *.tmp H:\projects\AlphaChart H:\backups\backup_<date>`

### How do I restore from backup?
1. Stop MCP server + Streamlit (`taskkill /F /IM python.exe`)
2. Delete current AlphaChart folder (or rename to `.old`)
3. Copy backup folder to AlphaChart location
4. Reinstall dependencies: `pip install -r requirements.txt`
5. Restart services: MCP server + Streamlit GUI

## Keyboard Shortcuts & Tips

### Streamlit GUI
- **Refresh Page**: F5 (browser refresh)
- **Clear Cache**: Delete `logs/` folder (charts, CSVs)
- **Reset Watchlist**: Edit `docs/watchlist.txt` (one ticker per line)

### MCP Server
- **List Tools**: `http://localhost:8006/mcp/tools/list` (browser)
- **Call Tool**: `http://localhost:8006/mcp/tools/alphachat_scan_market` (POST)
- **Check Logs**: View terminal output (Python console)

### Learning Module
- **View Patterns**: Open `docs/design doc viewer/LEARNING_LOG.md`
- **View Sessions**: Open `docs/design doc viewer/ADDR.md`
- **View Changes**: Open `docs/CHANGELOG.md`

## Troubleshooting

### GUI Won't Load
**Symptom**: Browser shows "This site can't be reached"
**Fix**: Check port 8501 not in use (`netstat -ano | findstr 8501`), restart with `--server.port 8502`

### Predictions Look Random
**Symptom**: BUY/SELL signals don't match price movement
**Fix**: Retrain model with more data (2018-2024), adjust Future Days (1-5), check regime coverage (need TRENDING_DOWN >252 days)

### Scanner Stops After First Run
**Symptom**: Background scan doesn't repeat every 15 minutes
**Fix**: Check `background_scan_enabled` in session state, verify `run_background_scan()` called in `ui/app.py`

### Paper Trading Shows No Data
**Symptom**: Pending Approvals, Open Positions, Trade History all empty
**Fix**: Approve signals in Portfolio & Scanner tab, check OrderManager initialized correctly

### Voice Not Working
**Symptom**: "Voice input not supported" or no response
**Fix**: Use Chrome/Edge (Web Speech API), check microphone permissions, verify DeepGram API key in `core/proactive/voice_deepgram.js`

## Support & Feedback

### Log Files
- **Session Logs**: `docs/design doc viewer/LEARNING_LOG.md` (session analysis, patterns)
- **Change Log**: `docs/CHANGELOG.md` (all modifications, history)
- **State Machine**: `docs/design doc viewer/ADDR.md` (all sessions, phases, state)

### Reporting Issues
1. Check FAQ (above) for common solutions
2. Review LEARNING_LOG.md for BAD patterns
3. Check ADDR.md for session context
4. Create new issue in repo with: session number, steps to reproduce, expected vs actual behavior

### Feature Requests
- Add to CHANGELOG.md user enhancement section
- Design Pass Module will capture in next session
- ADDR.md tracks all enhancement requests

---

*End of USER_MANUAL.md — Session 30 (1 Sev Pass)*
*Next: Update ADDR system with both manuals, then STOP and wait for user input.*
