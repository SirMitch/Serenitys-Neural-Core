# SERVICE_MANUAL.md — AlphaChart/Serenity Maintenance & Operations Guide

**Date**: 2026-05-03  
**Session**: 30 (1 Sev Pass)  
**Mode**: NON-MICRO-LLM MODE  
**Status**: COMPLETE

## Executive Summary

Service manual for AlphaChart/Serenity system. Covers maintenance, deployment, monitoring, troubleshooting, and operational procedures. Integrated into ADDR system for searchable access via MCP tools.

## System Architecture Overview

### Core Components
- **AlphaChart Core**: `core/` (agents, memory, models, tools, vision, personality, proactive, adaptive, integration, mind, learning)
- **GUI Layer**: `ui/` (Streamlit app.py, predict.py, spatial HTML/JS)
- **Documentation**: `docs/` (design doc viewer, CHANGELOG, ADDR, LEARNING_LOG)
- **Data Layer**: `db/` (SQLite), `logs/` (charts, CSVs), `data/` (market data cache)
- **Virtual Environment**: `finrlx/` (Python packages, dependencies)

### Key Processes
- **Session Workflow**: Design Pass → Learning Protocol → Load ADDR → Execute Tasks → Cleanup
- **Learning Engine**: Background observer recording execution steps, classifying patterns (GOOD/BAD), injecting optimization hints
- **Memory Hierarchy**: 5-layer system (Active Context, Working Memory, Episodic/ChromaDB, Semantic Graph, Persistent/ADDR)
- **Test Suite**: 10-category modular framework (architecture designed, Phase1-4 implementation roadmap)

## Installation & Deployment

### Prerequisites
- **OS**: Windows 10/11 (tested), Linux/macOS (theoretical)
- **Python**: 3.11+ (finrlx venv)
- **Node.js**: For spatial UI (optional, HTML/JS runs in browser)
- **Ollama**: For local LLM (optional, falls back to rule-based)
- **DeepGram API**: For voice latency <500ms (optional, falls back to Web Speech API)

### Installation Steps
1. **Clone Repository**: `git clone <repo-url> AlphaChart`
2. **Set up Venv**: `python -m venv finrlx` (already present)
3. **Install Dependencies**: `pip install -r requirements.txt`
   - Key packages: streamlit, fastmcp, chromadb, langgraph, langchain, yfinance, plotly
4. **Install MCP Server**: `pip install fastmcp` (not mcp)
5. **Set Environment Variable**: `ALPHACHART_DOCS=docs/design doc viewer/`
6. **Run GUI**: `streamlit run ui/app.py --server.port 8501`
7. **Run MCP Server**: `python core/mcp/alphachat_mcp_server.py`

### Configuration
- **Streamlit Config**: `ui/.streamlit/config.toml` (theme, port, browser)
- **Watchlist**: `docs/watchlist.txt` (one ticker per line)
- **Logging**: `logs/` directory (auto-created, charts CSVs)
- **Backup**: `backups/` directory (manual or scripted)

## Monitoring & Health Checks

### System Health Indicators
- **MCP Server**: `http://localhost:8006/mcp/tools/list` (should return 6+ tools)
- **Streamlit GUI**: `http://localhost:8501` (should load dark theme)
- **Memory Layers**: Run `python test_memory_layers.py` (expect 9/9 PASS)
- **Integration**: Run `python test_new_modules_integration.py` (expect 3/3 PASS)
- **Context Window**: Monitor token usage (~70k limit, 70% trigger compaction)

### Logs & Artifacts
- **Session Logs**: `docs/design doc viewer/LEARNING_LOG.md` (session analysis, patterns)
- **Change Log**: `docs/CHANGELOG.md` + `docs/design doc viewer/CHANGELOG.md` (dual tracking)
- **State Machine**: `docs/design doc viewer/ADDR.md` (all sessions, phases, state)
- **Backups**: `backups/backup_YYYY-MM-DD_HH-MM-SS/` (full system snapshot)

### Alerting Rules
- **Context 70%**: Compaction protocol triggered (summarize to CURRENT_TASK.md)
- **Context 90%**: Alert user, suggest summarization
- **Test Failure**: Log to LEARNING_LOG.md, classify as BAD pattern
- **MCP Server Down**: Check PID, restart `python core/mcp/alphachat_mcp_server.py`
- **Import Error**: Verify fastmcp installed (not mcp), check __init__.py exports

## Maintenance Procedures

### Daily Tasks
- [ ] Check MCP server running (`tasklist | findstr python`)
- [ ] Review LEARNING_LOG.md for new BAD patterns
- [ ] Monitor context window usage (if long session)
- [ ] Verify backup directory not growing unbounded

### Weekly Tasks
- [ ] Run full test suite (`python -m pytest tests/ -v`)
- [ ] Review doc_registry.json for stale entries
- [ ] Update CURRENT_TASK.md with next session plan
- [ ] Prune old backups (keep last 3)

### Monthly Tasks
- [ ] Regenerate Serenity_Design_Catalog.json (update statistics)
- [ ] Review Test Registry (test_registry.json) for outdated tests
- [ ] Archive old sessions from ADDR.md (if >2000 lines)
- [ ] Update Serenity_Master_Design_Document.md (auto-sync from ADDR)

## Troubleshooting

### Common Issues & Fixes

#### MCP Server Fails to Start
**Symptom**: `ImportError: No module named 'fastmcp'`
**Fix**: `pip install fastmcp` (NOT `pip install mcp`)
**Verify**: `python -c "from fastmcp import FastMCP"`

#### Streamlit GUI Won't Load
**Symptom**: Port 8501 already in use
**Fix**: `streamlit run ui/app.py --server.port 8502` (or kill existing: `taskkill /F /PID <pid>`)
**Verify**: Browser open `http://localhost:8502`

#### Memory Layer Test Fails
**Symptom**: `test_memory_layers.py` returns <9/9 PASS
**Fix**: Run `python -m py_compile core/memory/*.py` (check syntax), verify ChromaDB installed
**Verify**: Re-run test, check specific failure in LEARNING_LOG.md

#### IOCache Not Working
**Symptom**: MCP tool calls always miss cache
**Fix**: Check `cache_key` not re-hashed (use directly as filename), verify D: SSD accessible
**Verify**: Call tool twice, check logs for "hit" vs "miss"

#### Context Window Overflow
**Symptom**: Session stops responding, token limit reached
**Fix**: Trigger compaction protocol (summarize to CURRENT_TASK.md), start fresh
**Verify**: Check token count in session output (~70k limit)

#### Windows Encoding Errors
**Symptom**: `UnicodeEncodeError: 'charmap' codec can't encode`
**Fix**: Use ASCII-only in markdown files, avoid emojis in bash output
**Verify**: Run `python -c "print('test')"` in bash tool (should not error)

## Backup & Recovery

### Backup Procedure
1. **Full Backup**: `robocopy /E /XD __pycache__ /XF *.bak *.tmp H:\projects\AlphaChart H:\projects\AlphaChart\backups\backup_<date>_<time>`
2. **Exclusions**: `__pycache__/`, `finrlx/`, `backups/`, `*.bak`, `*.tmp`
3. **Verify**: Check backup directory has all folders except exclusions

### Recovery Procedure
1. **Stop MCP Server + Streamlit**: Kill processes
2. **Restore from Backup**: Copy files from `backups/backup_<date>/` to `AlphaChart/`
3. **Reinstall Dependencies**: `pip install -r requirements.txt`
4. **Restart Services**: MCP server + Streamlit GUI
5. **Verify**: Run tests (9/9 + 3/3 PASS), check GUI loads

## Security & Access Control

### API Keys & Secrets
- **DeepGram API**: Store in `core/proactive/voice_deepgram.js` (already embedded, move to env var later)
- **Ollama**: Local only, no API key needed
- **Database**: SQLite local file (`db/alphachart_data.db`), no remote access

### Guardrails & Safety
- **Deterministic Safety Layer**: NC-1 to NC-15 hard limits (immutable code constants)
- **Guardian Agent**: Blast radius governance, safety checks before execution
- **Prompt Injection**: Test suite includes adversarial input tests (planned)
- **Data Leakage**: No sensitive data in logs/outputs (test suite validates)

## Performance Optimization

### Caching Strategy
- **IOCacheManager**: D: SSD cache for frequent file accesses (4 workers, TTL-based)
- **ChromaDB**: Episodic memory with hybrid search (PPR + semantic similarity)
- **MCP Server**: IOCache wired to alphachat_scan_market (verify hit/miss)

### Latency Targets
- **MCP Tool Call**: <4s (timeout enforced)
- **Voice Response**: <500ms (DeepGram Nova-2)
- **GUI Tab Switch**: <1s (Streamlit native)
- **Test Suite (full)**: <10 minutes (parallel execution planned)

## Integration Points

### ADDR System
- **Searchable**: `docs/design doc viewer/ADDR.py` (indexer + state machine + search)
- **Documents**: 32+ files registered in `doc_registry.json`
- **MCP Tools**: Access via `ALPHACHART_DOCS` env var → `docs/design doc viewer/`

### Test Suite
- **Registry**: `test_registry.json` (planned, Phase1 implementation)
- **Categories**: 10 (Unit, Integration, Agent, Reliability, Performance, Security, Drift, UX, Edge, Learning)
- **Execution**: Individual, Suite, Regression, Custom, Deterministic, Statistical

### Learning Module
- **Observer**: Background recording execution steps (mode, action, tools, tokens, result)
- **Pattern Store**: GOOD/BAD patterns in LEARNING_LOG.md (persisted in ADDR)
- **Optimization**: Inject hints into next execution plan based on past successes/failures

## Escalation & Support

### When to Escalate
- [ ] Test suite failure rate >5% (flaky tests)
- [ ] MCP server crashes repeatedly (>3 times/day)
- [ ] Context window overflows despite compaction
- [ ] Data corruption (database, ChromaDB, cache)
- [ ] Security breach suspected (prompt injection, unauthorized access)

### Support Contacts
- **Technical Issues**: Review LEARNING_LOG.md, ADDR.md, CHANGELOG.md
- **Design Questions**: Read Serenity_Master_Design_Document.md, Serenity_Design_Catalog.json
- **User Issues**: Refer to USER_MANUAL.md (next deliverable)

## Version & Change Tracking

### Current Version
- **AlphaChart**: v3.4 (Implementation-Ready)
- **Serenity**: v3.0 (Target Architecture, 98%+ mature)
- **Test Suite**: Architecture Complete (Phase1-4 roadmap ready)

### Change Log References
- **Detailed**: `docs/CHANGELOG.md` (root-level, user-facing)
- **Technical**: `docs/design doc viewer/CHANGELOG.md` (session-level, developer-facing)
- **State Machine**: `docs/design doc viewer/ADDR.md` (all sessions, phases, state)

---

*End of SERVICE_MANUAL.md — Session 30 (1 Sev Pass)*
*Next: Create USER_MANUAL.md, then STOP and wait for user input.*
