## GUARDIAN_AGENT MICRO-MODE DESIGN DOCUMENT — Session 35

Source Code: core/agents/guardian_agent.py (406 lines)

---

### 1\. Overview
**Purpose**: Safety/compliance governance with atomic validation micro-steps  
**Mode**: Dual-execution — Micro-LLM iterative checks + Standard single-step fallback

### 2\. Integration Summary (Session 35)
✅ Token tracking added to per-check budget management (20k tokens)  
✅ Convergence detection integrated (keyword-based early termination at 3 iterations)  
✅ Stats interface exposes micro-mode status and execution counts  
✅ Guardrail rules enforced via JARVIS blast radius document  

### 3\. Execution Flow
`
[Action] → [MicroLLMManager] → [Atomic Check #1: Write Access?]?
    ↓ converged? YES/NO    ↓ continue iteration? YES/NO
[Result Aggregation] → [SecurityCheck output]
`

### 4\. Agent Integration Points
- **ExecutorAgent**: Guardian check before action execution
- **PlannerAgent**: Convergence validation — safety-approved plans only  
- **ResearcherAgent**: Data source compliance — allowed APIs only
- **CriticAgent**: Validation feedback loop — reject unsafe findings

### 5\. Governance Stats Interface
`python
stats = {
    "total_checks": len(self.check_history),
    "is_micro_llm_mode": True,
    "steps_executed_so_far": step_counter,
    "token_budget_remaining": context_tokens_remaining,
    "latest_check_result": {"approved": ..., "risk_level": ...}
}
`

---

End of GUARDIAN_MICRO_MODE design doc — Task #1 Complete.
