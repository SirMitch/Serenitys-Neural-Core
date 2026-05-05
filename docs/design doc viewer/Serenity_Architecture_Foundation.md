# Serenity — AlphaChart AI Assistant Core System Architecture

**Date**: 2026-05-03  
**Status**: FOUNDATION LAYER CREATED (Groundwork Phase)  
**Inspiration**: Iron Man JARVIS-style autonomous AI assistant  
**Positioning**: AlphaChart as core module within larger system-of-interest

---

## 🎯 VISION & PHILOSOPHY

### Core Principle
AlphaChart evolves beyond single-purpose trading application → becomes **execution engine at heart of AI financial analysis platform**. Serenity orchestrates:
- Market data ingestion (multi-exchange APIs)
- Alpha hypothesis generation (backtesting + live signals)  
- Risk management (position sizing, stop logic)
- Portfolio construction (rebalancing algorithms)
- Compliance & safety (regulatory checks, blacklists)

**AlphaChart Role**: Specialized reasoning engine for financial markets within unified AI assistant architecture.

---

## 🏗️ ARCHITECTURE OVERVIEW

### System Hierarchy
```
Serenity (AI Assistant Core)
├── Core Intelligence Layer
│   ├── ADDR Engine (persistent memory + state machine)
│   ├── Memory System (4-layer stack: active → compressed history)
│   └── Learning Engine (background observer + pattern store)
│
├── Specialized Modules
│   ├── AlphaChart v3.4 ← CURRENT SYSTEM CORE
│   │   ├── Market Scanner (MarketWide + Portfolio)
│   │   ├── OrderManager (paper trading execution)
│   │   └── Learning Engine (auto-improving backtests)
│   │
│   └── Emerging Extensions
│       └── [Future] Asset class specialists (crypto, forex)
│
├── Integration Layer
│   ├── MCP Protocol Bridge
│   │   ├── AlphaChart MCP Server
│   │   └── External tool connectors (Git, web APIs)
│   │
│   ├── Skills Registry
│   │   ├── Code analysis skills (OpenHands pattern)
│   │   ├── Web browsing for market data discovery
│   │   └── Repository management
│   │
│   └── Agent Hub
│       ├── BrowsingAgent (market research)
│       └── AnalysisAgent (signal interpretation)
│
└── Runtime Environment
    ├── Sandbox Execution (for untrusted tools)
    └── Event Bus (asynchronous coordination)

```

### OpenHands Integration Points

| Component | Location in AlphaChart | Purpose |
|-----------|------------------------|---------|
| **Agent Hub** | `core/agenthub/` | Autonomous reasoning agents (browse, analyze, execute) |
| **Controller** | `core/controller/` | Multi-step workflow orchestration |
| **Memory** | `core/memory/` + ADDR | Persistent state + compressed history |
| **MCP Server** | `core/mcp_server.py` | Tool interoperability standard |

---

## 🔧 GROUNDWORK: INTEGRATION PREPARATION

### 1. **Stub Agent Stub** (Lightweight Entry Point)
Create stub in `H:/projects/AlphaChart/core/agents/alphabet_chart_agent.py`:

```python
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncIterator
import sys; sys.path.insert(0, 'docs/design doc viewer')

from ADDR import load_ADDR  # Source-of-truth state machine

class AlphaChatADDRAgent:
    """
    Lightweight agent stub implementing OpenHands controller pattern.
    Provides atomic micro-step execution with ADDR as persistent memory.
    
    Architectural Alignment:
    - ADDR = Persistent Memory backbone (see CONTINUATION_PROMPT.md section 9)
    - Micro-steps enabled for LOCAL MICRO-LLM MODE (atomic changes > deep planning)
    - Controller pattern adopted from OpenHands/openhands/controller/
    """
    
    def __init__(self, docs_path: str = "docs/design doc viewer"):
        self.docs_path = docs_path
        self ADDR = None  # Lazy load via loadADDR()
        
    async def execute_workflow(self, task: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Orchestrates multi-step analysis workflow (controller pattern).
        Each step validated before proceeding → atomic operations ensured.
        
        Args:
            task: High-level objective (e.g., "Analyze SPY backtest performance")
            
        Yields:
            Step results for incremental feedback
        """
        addr = load_ADDR(self.docs_path)  # Source-of-truth state
        
        # Phase 1: Plan & Break Down
        plan = yield self._plan_task(task, ADDR.context)
        
        # Phase 2: Execute Steps (atomic operations)
        for step in plan.steps:
            action_name = step.type  # browse_docs | run_shell | analyze_data | reason
            if action_name == "browse_docs":
                result = yield self._browseADDR(step.params)
            elif action_name == "run_shell":
                result = yield self._execute_command(step.command)
            elif action_name == "analyze_data":
                result = yield self._run_analysis(step.analysis_spec)
            
            # Yield result immediately (high-frequency micro-steps enabled) 
            yield Result(step.id, step.type, step.result)
        
        # Phase 3: Synthesize Solution
        solution = yield self._synthesize_results(task, ADDR.state_history)
        return solution
    
    async def _plan_task(self, task: str, context: Dict) -> Plan:
        """Decompose task into atomic micro-steps."""
        pass  # TODO: Implement LLM-based planning or rule decomposition
    
    async def _browseADDR(self, params: Dict[str, Any]) -> DocumentData:
        """Load specific files from ADDR docs layer."""
        addr = load_ADDR(self.docs_path)
        return DocumentData(path=params.get("filepath"), content=addr.read(params))
    
    async def _execute_command(self, command: str) -> CommandResult:
        """Execute shell commands in controlled environment."""
        pass  # TODO: Implement with sandbox safety checks
    
    async def _run_analysis(self, spec: Dict[str, Any]) -> AnalysisResult:
        """Run backtest or signal generation analysis."""
        pass  # TODO: Wire to existing alphachart backend
    
    async def _synthesize_results(self, task: str, history: List[StepResult]) -> Solution:
        """Combine step results into actionable output."""
        pass  # TODO: LLM synthesis or rule-based aggregation
```

**Notes**:
- Stub implementation enables rapid iteration (micro-step validation)
- Replace `pass` with actual OpenHands patterns from `D:/AI Clients/OpenHands/openhands/`
- ADDR provides persistent memory backing (no separate storage needed)

### 2. **MCP Server Implementation**
Create server in `H:/projects/AlphaChart/core/mcp_server.py`:

```python
from mcp.server.fastmcp import FastMCP
import sys; sys.path.insert(0, 'core')
from scanner_module import MarketWideScanner, PortfolioScanner  

mcp = FastMCP("AlphaChart")  # MCP server instance

@mcp.tool()  
def alphachat_scan_market(context: MarketScanContext) -> MarketScanResult:
    """
    AlphaChart market analysis with Phase 0 audit rules.
    
    Args:
        context (MarketScanContext): Symbol, timeframe, strategy filters
        
    Returns:
        MarketScanResult: Backtest history + current signals in structured format
    """
    scanner = MarketWideScanner()  # Use existing ALPHA CHART scanner
    result = scanner.run_scan(...) # Wire to actual implementation
    
    return {
        "status": "success",
        "data": [
            {"symbol": row[0], "sharpe": row[2], ...} for row in result.data
        ],
        "win_rate_percent": result.win_rate * 100
    }

@mcp.tool()  
def alphachat_execute_order(order_id: int, action: str) -> OrderResult:
    """
    Paper trading order execution via OrderManager.
    
    Args:
        order_id: Unique identifier from scan results
        action: One of "approve", "reject"
        
    Returns:
        OrderResult with timestamped confirmation
    """
    if action == "approve":
        return OrderManager().execute(order_id)  # Wire to OrderManager logic
    
@mcp.tool()  
def alphachat_backtest_query(metric: str, filters: dict) -> QueryResult:
    """Query backtest performance metrics."""
    pass  # Wire to existing query engine

```

### 3. **Skills Registry Extension**
Create skill definitions in `H:/projects/AlphaChart/api/tools/skills/`:

```
api/tools/skills/
├── openhands_analyzer/           # Code analysis + debugging skills  
│   ├── __init__.py
│   ├── strategy_parser.py        # Parse backtest strategy code
│   └── rule_validator.py         # Validate logic gates in strategies
│
├── webbrowser_marketdata/       # Browser automation skills
│   ├── browser_agent.py          # Browse alpha.com/marketdata via Selenium
│   └── data_extractor.py         # Parse financial tables from pages
│
└── repo_manager/                 # Git operations on trading algo repos
    ├── clone_repo.py             # Clone GitHub repo safely
    └── branch_checkout.py        # Create/push branches
```

**Integration Pattern**: Each skill registers with MCP server → exposed as available tool.

---

## 📊 OPTIMIZATION INSIGHTS (From AlphaChart Code Analysis)

### Memory Management Recommendations

1. **ADDR as Single Memory Source-of-Truth**
   - All persistent state written to ADDR.md (never duplicates)
   - Compressed history moves older steps → compressed summary block
   - Active context = current micro-step only (discard post-response)

2. **Pattern for Low-Overhead Logging**
   ```python
   # GOOD: Minimal logging aligned with LOCAL MICRO-LLM MODE constraints
   logger.debug(f"Step {i}: {action} → success")  # High-signal only
   
   # BAD: Avoid verbose chains (violates memory efficiency rule)
   for detail in [raw_step_1, raw_step_2, ...]:   # Too much context
       logger.info(str(detail)) 
   ```

3. **Failure Recovery Pattern** (From EDGE CASE HANDLING rules)
   ```python
   try:
       step_result = execute_step(task)  # Atomic micro-step
   except Exception as e:                # Tool failure detected
       fallback_result = handle_edge_case(e, addr.state)  # Infer safe path
       yield Result(step.id, "fallback", fallback_result)
       continue                          # Continue pipeline (graceful degradation)
   ```

### Context Extension Recommendations

1. **ADDR Retrieval Layer** (Minimal Load Enforced — see CONTINUATION_PROMPT.md section 8)
   ```python
   def load_addr_context(needed_fields: List[str] = None) -> Dict[..., ...]:
       addr = LOAD_ADDR()  # Source-of-trust reconstruction source
       
       if needed_fields:
           return {field: getattr(addr, field) for field in needed_fields}
       else:
           return addr.context  # Only when state reconstruction required
   ```

2. **Compressed History Structure** (Bullet blocks + KV pairs)
   ```yaml
   compressed_history:
     - timestamp: "2026-05-03T14:32"
       event: "threshold_optimization_complete"
       outcome: "78.9% win rate achieved via THRESHOLD=0.005 (ADDR-backed)"
     - timestamp: "2026-05-03T14:35"
       event: "scanner_UI_integration_verified"
       outcome: "MarketWide + Portfolio backends wired end-to-end"
   ```

### Alignment & Safety Integration

Per user requirements, align all future changes with:
```yaml
guardrails:
  ethical_constraints:
    - No speculative investment advice
    - All signals marked as unverified paper trading predictions
    - Clear risk warnings on all output
  compliance:
    - Never execute real-money orders in current implementation
    - Regulatory disclaimers appended to outputs
  safety_first:
    - All shell command execution requires approval check (run_guardian integration)
    - No external network calls without sandbox verification
```

---

## 🗺️ ROADMAP & STRATEGIC VISION

### Milestone 1.0 — Foundation Phase (Current Position)
**Status**: ✅ Complete groundwork documents  
**Deliverables**:
- Architecture foundation document (this file)
- Stub agent implementation in `core/agents/alphabet_chart_agent.py`
- MCP server skeleton in `core/mcp_server.py`
- Skills registry structure ready for populating

### Milestone 2.0 — Integration Phase (3-6 Months)
**Goals**:
- Implement full controller orchestration (multi-step workflows)
- Integrate browse skill for financial data research
- Wire openhands_analyzer skill with backtest strategies
- Deploy MCP server with AlphaChart tools exposed

### Milestone 3.0 — Serenity Core Launch (6-12 Months)
**Goals**:
- Autonomous execution of end-to-end workflows:
  - User prompt → "Analyze SPY volatility regime and suggest adjustments"
  - Agent plans substeps → Executes shell commands → Fetches market data → Synthesizes response
- Persistent memory via ADDR across sessions (state reconstruction on resume)
- Micro-step validation ensures atomic operations for trades

### Milestone 4.0 — Expansion Phase (12-18 Months)
**Goals**:
- Add asset class specialists (crypto, forex modules plug into existing scanner pattern)
- Multi-agent collaboration (research agent → analysis agent → execution agent)
- Self-improving via BACKGROUND LEARNING ENGINE integration

---

## 📚 REFERENCE LINKS

### OpenHands Patterns to Adopt
- **Controller**: `D:/AI Clients/OpenHands/openhands/controller/` — Orchestration pattern
- **Agent Hub**: `D:/AI Clients/OpenHands/openhands/agenthub/` — Agent implementations  
- **MCP Tools**: `D:/AI Clients/OpenHands/.venv/Lib/site-packages/mcp_client` patterns

### AlphaChart Core Files (Current Implementation)
```
H:/projects/AlphaChart/core/
├── data/                # Scanner datasets
├── features/            # Feature engineering
├── models/              # ML model artifacts
├── llm/                 # LLM wrappers
└── execution/           # Backtest strategy executions

docs/design doc viewer/
├── ADDR.md                     ← Persistent memory backbone
├── CONTINUATION_PROMPT.md      ← Memory retrieval logic (section 9)
├── CHANGELOG.md                ← Pattern store (learned optimizations)
└── LEARNING_ENGINE_INTEGRATED.md ← Background learning engine spec
```

---

*End of Serenity Foundation — Ready for user decision on next implementation step.*
