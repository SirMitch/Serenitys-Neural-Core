# Test Suite Architecture — Modular Swiss-Army-Knife Testing Framework

**Date**: 2026-05-03  
**Session**: 29  
**Mode**: NON-MICRO-LLM MODE  
**Status**: Design Complete

## Executive Summary

Modular testing framework for Serenity/AlphaChart system. Self-contained, versioned test modules executable independently or composed into suites. Covers all system layers with automated runs, structured observability, and dynamic toolkit management via central Test Registry.

## Core Design Principles

- **Modularity & Reusability**: Every test is self-contained, versioned, executable independently or in suites
- **Extensibility**: New tests auto-generated for new capabilities/edge cases
- **Categorization**: Clear categories for rapid selection and execution
- **Automation-First**: Fully automated runs, scheduled regressions, on-demand targeted testing
- **Observability**: Structured logs, metrics, pass/fail results, artifacts, traceability
- **Dynamic Toolkit Management**: Central Test Registry with metadata, auto-discovery, composition

## Test Categories

### 1. Unit / Component Tests
- **Scope**: Individual functions, classes, modules
- **Examples**: 
  - `test_memory_layers.py` (9/9 PASS) — L1-L5 memory layers
  - `test_data_fetcher.py` — DataFetcher TTL caching, timeframe mapping
  - `test_regime_detector.py` — Regime enum, detect(), weights
  - `test_mcp_server.py` — FastMCP tool wiring, IOCache behavior

### 2. Integration & Workflow Tests
- **Scope**: Cross-module workflows, data pipelines
- **Examples**:
  - `test_new_modules_integration.py` (3/3 PASS) — L3→L5 pipeline
  - `test_langgraph_workflow.py` — 5-agent orchestration, checkpointing
  - `test_scanner_integration.py` — Scanner → Signal → Order pipeline

### 3. Agent Behavior & Reasoning Tests
- **Scope**: Agent decision quality, reasoning chains, handoff workflows
- **Examples**:
  - `test_planner_agent.py` — Task decomposition, plan generation
  - `test_executor_agent.py` — Tool orchestration, error recovery
  - `test_critic_agent.py` — Validation feedback, quality scoring
  - `test_guardian_agent.py` — Safety checks, blast radius governance

### 4. Reliability & Resilience Tests (Chaos, Failure Injection, Recovery)
- **Scope**: System behavior under failure, chaos testing, recovery paths
- **Examples**:
  - `test_mcp_server_failure.py` — Server crash, restart behavior
  - `test_io_cache_miss.py` — Cache miss cascades, fallback behavior
  - `test_agent_timeout.py` — Agent timeout, retry logic
  - Chaos: Kill random agent, verify system continues

### 5. Performance & Efficiency Tests
- **Scope**: Latency, throughput, token consumption, resource usage
- **Examples**:
  - `test_mcp_response_time.py` — Tool call latency (<4s threshold)
  - `test_token_efficiency.py` — Session token usage, compaction triggers
  - `test_cache_hit_rate.py` — IOCache effectiveness
  - `test_batch_operations.py` — Bulk tool call efficiency

### 6. Security & Guardrail Tests
- **Scope**: Prompt injection, unauthorized access, data leaks, malicious inputs
- **Examples**:
  - `test_prompt_injection.py` — Attempt injection via user inputs
  - `test_authz_checks.py` — Verify access controls on MCP tools
  - `test_data_leakage.py` — Ensure no sensitive data in logs/outputs
  - `test_guardrail_enforcement.py` — NC-1 to NC-15 hard limits

### 7. Drift Detection & Long-Term Stability Tests
- **Scope**: Model drift, concept drift, performance degradation over time
- **Examples**:
  - `test_model_drift.py` — Compare predictions across time windows
  - `test_foils_drift_detection.py` — Foils-style drift alerts
  - `test_memory_consistency.py` — Cross-layer memory synchronization
  - `test_long_running_session.py` — 24h+ stability test

### 8. User Experience & Interaction Quality Tests
- **Scope**: GUI responsiveness, output quality, user workflow smoothness
- **Examples**:
  - `test_gui_response_time.py` — Streamlit tab switch latency
  - `test_output_quality.py` — JARVIS-style response templates
  - `test_voice_latency.py` — Deepgram API response time (<500ms)
  - `test_spatial_ui_render.py` — Plotly chart rendering, MCP calls

### 9. Edge Case & Adversarial Tests
- **Scope**: Boundary conditions, adversarial inputs, unexpected scenarios
- **Examples**:
  - `test_windows_encoding.py` — ASCII-only output enforcement
  - `test_malformed_json.py` — LLM quality gate with bad JSON
  - `test_extreme_market_conditions.py` — Flash crash, black swan simulation
  - `test_adversarial_prompts.py` — Attempt to bypass safety layers

### 10. Self-Improvement & Learning Module Validation Tests
- **Scope**: Learning engine, pattern recognition, optimization hints
- **Examples**:
  - `test_learning_engine.py` — Execution Step Record, Flow Segment, Pattern Store
  - `test_pattern_classification.py` — GOOD/BAD pattern detection
  - `test_optimization_hints.py` — Next-pass hint injection
  - `test_session_learning.py` — Post-Session Learning & Improvement Protocol

## Central Test Registry

### Structure (test_registry.json)
```json
{
  "registry_metadata": {
    "name": "Serenity Test Registry",
    "version": "1.0",
    "last_updated": "2026-05-03",
    "total_tests": 50,
    "by_category": {
      "unit": 15,
      "integration": 8,
      "agent_behavior": 6,
      "reliability": 5,
      "performance": 4,
      "security": 5,
      "drift": 3,
      "ux": 4,
      "edge_case": 5,
      "learning": 8
    }
  },
  "tests": {
    "TEST_MEM_L1": {
      "file": "test_memory_layers.py::test_layer1_active_context",
      "category": "unit",
      "name": "ActiveContext MemoryOffloader Test",
      "description": "Verifies Layer 1 active context storage/retrieval",
      "prerequisites": ["core.mind.memory_offloader"],
      "expected_outcome": "PASS",
      "version": "1.0",
      "last_run": "2026-05-03",
      "success_rate": "100%",
      "avg_duration_ms": 150
    }
  }
}
```

### Auto-Registration
- On new test file creation: Auto-register in test_registry.json
- On test execution: Update last_run, success_rate, avg_duration_ms
- On test failure: Log to LEARNING_LOG.md for pattern analysis

## Execution Capabilities

### Run Modes
1. **Individual Test**: `python -m pytest test_memory_layers.py::test_layer1_active_context -v`
2. **Category Suite**: `python -m pytest --category=unit -v`
3. **Full Regression**: `python -m pytest tests/ -v`
4. **Custom Combination**: `python -m pytest --category=unit,integration --tag=fast -v`
5. **Deterministic**: Single run, exact assertion
6. **Statistical**: N trials (default 100), confidence intervals computed

### Pre/Post Conditions
- **Setup**: Fixture loading, mock injection, state initialization
- **Teardown**: State cleanup, mock reset, artifact preservation
- **Environment Isolation**: Each test runs in clean state (no cross-test contamination)

### Integration Points
- **Learning Module**: Failed tests → LEARNING_LOG.md pattern store
- **ADDR**: Test results indexed, searchable via `search` tool
- **CI/CD**: GitHub Actions (or similar) for scheduled regression
- **Failure Analysis**: Automatic root-cause extraction, linked to Post-Session Learning Protocol

## Documentation & Governance

### Test Specifications
- Each test file contains docstring: purpose, inputs, expected outputs, edge cases
- Complex tests have dedicated design doc in `docs/design doc viewer/` with ADDR cross-reference

### Usage Guidelines
- **Developer**: Run unit tests after every module change
- **CI Pipeline**: Run full regression on every push
- **Release**: Run all categories, 100% pass required for deployment
- **Learning Module**: Query registry for relevant tests, compose dynamic suite

### ADDR Integration
- All test documents registered in doc_registry.json with type "test"
- Test results logged to ADDR.md (Session entry)
- Test Registry itself queryable via ADDR search tool

## Implementation Roadmap

### Phase 1: Foundation (Session 29-30)
- [x] Design Test Suite Architecture (this document)
- [ ] Create test_registry.json with existing tests (9+3+6=18 tests)
- [ ] Create pytest configuration (pytest.ini, conftest.py)
- [ ] Implement test discovery and auto-registration

### Phase 2: Expansion (Session 31-33)
- [ ] Add Security & Guardrail tests (5 tests)
- [ ] Add Performance & Efficiency tests (4 tests)
- [ ] Add Drift Detection tests (3 tests)
- [ ] Add UX & Interaction tests (4 tests)

### Phase 3: Automation (Session 34-36)
- [ ] Implement scheduled regression via CI/CD
- [ ] Integrate with Learning Module (failure → pattern store)
- [ ] Build test result dashboard (Streamlit tab)

### Phase 4: Advanced (Session 37-40)
- [ ] Chaos testing framework (failure injection)
- [ ] Statistical testing engine (N trials, confidence intervals)
- [ ] Self-healing test repair (VIGIL-style)

## Success Criteria

- [ ] Test Registry contains 50+ tests across all 10 categories
- [ ] 100% of new features have corresponding tests within 1 session
- [ ] Full regression runs in <10 minutes (optimized via parallel execution)
- [ ] Test failure rate <5% (flaky tests fixed or quarantined)
- [ ] Learning Module uses test patterns to avoid BAD patterns
- [ ] Zero regression bugs reach production (all caught by test suite)

## Cross-References

- **ADDR**: `Test_Suite_Architecture.md` (this document)
- **Learning Module**: `LEARNING_LOG.md` — test failures → pattern store
- **Workflow Analysis**: `WORKFLOW_ANALYSIS.md` — test integration recommendations
- **CONTINUATION_PROMPT.md**: Test Suite added to session workflow

---

*End of Test Suite Architecture Design Document — Session 29*
