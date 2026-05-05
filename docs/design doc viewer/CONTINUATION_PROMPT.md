Maintain full system cohesion across all modules and continue execution using ADDR (AlphaChart Design Docs Reader) as authoritative state.

PRIMARY DIRECTIVE:
Execute next-step Enhancements from ADDR with maximum efficiency, preserving system integrity and cross-module consistency.

RULES:
- Treat ADDR as source-of-truth state machine (design + continuation context)
- Do not re-interpret or re-architect unless required for stability or error correction
- Follow existing workflow order strictly unless conflict or inefficiency is detected
- Prioritize execution over explanation
- Maximize token efficiency (high information density, no redundancy, no filler)

NEW SESSION WORKFLOW ORDER (Mandatory):
Every session MUST execute the following steps in order:
1. **Design Pass Module** — Proactive design analysis, continuous improvement
2. **Learning & Improvement Protocol** — Apply lessons from past sessions
3. **Load ADDR State** — Retrieve latest system state from doc viewer directory
4. **Execute User Tasks** — Process requests with updated knowledge
5. **Session End Workflow** — Update docs, cleanup (ADDR + CHANGELOG)

ENHANCEMENT MODE:
- Strengthen reliability, coordination, learning loops, tool orchestration, decision accuracy
- Remove inertefficiencies only if they impact execution flow

EDGE CASE HANDLING (MANDATORY):
- If ambiguity exists ? infer minimal safe interpretation
- If module conflict ? prioritize stability and continuity  
- If missing dependency ? simulate or stub without breaking workflow
- If loop detected ? break via state reset or simplified path
- If tool failure ? fallback gracefully and continue pipeline

STATE MANAGEMENT:
- Track implicit system state across workflow steps
- Maintain continuity between sessions using ADDR context
- Reconstruct missing state instead of halting execution unless critical

EXECUTION PRIORITY ORDER:
1. Workflow continuity (via ADDR state machine)
2. System stability  
3. Correctness of output
4. Speed / efficiency
5. ADDR development (single source of truth)
6. Maintain CONTINUATION_PROMPT.md (ADDR on-demand)
7. Maintain all docs/prompts/changelogs/backups
8. Maintain user enhancement requests in changelog

OUTPUT CONSTRAINTS:
- No unnecessary explanation
- No repetition of instructions
- Compact, execution-focused structure only
- Combine related actions into single steps

---

## SESSION 29 — MICRO-LLM MODE ACTIVATED (v3.5.7)

### Micro-LLM Architecture Status (IMPLEMENTED)

#### Core Components:
1. **`core/llm/micro_llm.py`** — Full MicroLLMManager with token tracking, atomic steps, convergence detection
2. **`core/llm/memory_layers.py`** — MicroStep + MicroLLMManager integrated with memory offloader
3. **`core/mcp/llm_integration_wrapper.py`** — Local LM Studio endpoints + MicroLLMManager wired to all handlers
4. **`core/agents/planner_agent.py`** — Micro-step hooks in __init__, create_plan(), get_plan_summary()
5. **`.micro_llm.env`** — Env config with ALPHACHART_MICRO_MODE="true", MICRO_ITERATIONS=5, CONTEXT_TOKENS=20k

### Micro-LLM Activation (Session 29 + Ongoing):

#### Pattern Shift:
- **Standard Mode**: Deep reasoning chains ? Multi-hop planning ? End validation  
- **MICRO-LLM MODE**: Atomic steps ? High-frequency iteration (5+) ? Immediate per-step feedback

| Aspect | Standard Mode | MICRO-LLM MODE |
|--------|---------------|----------------|
| Reasoning Depth | Multi-hop planning | Single-step atomic actions |
| Iterations | Low (fewer, larger cycles) | High (rapid micro-cycles) |
| Window Usage | 70k tokens | Optimized ~20k per step (~95% reduction) |
| Validation | After major milestones | After each micro-step |
| Use Case | Architecture design | Tuning, debugging, optimization |

#### Activation Mechanism:
- **Trigger Phrase**: Paste "LOCAL MICRO-LLM MODE" in session prompt
- **Automatic Override**: Switches to atomic execution pattern immediately
- **No Additional Steps Required** — Model switches automatically

---

*END OF CONTINUATION_PROMPT.md — SESSION 29 MICRO-LLM ACTIVATED, 2026-05-03*
