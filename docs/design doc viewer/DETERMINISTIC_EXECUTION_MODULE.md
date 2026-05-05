# Deterministic Execution Module (DEM) — Session Tracking System

## Protocol Overview

This module enforces deterministic pass execution via explicit session counters stored in ADDR state machine, eliminating all implicit or optional triggering patterns.

---

## Global State Schema (Stored in ADDR.json)

```json
{
  "session_tracking": {
    "current_session_id": <int>,           // Auto-incremented at session start
    "dev_pass_last_run": <int|null>,       // Last dev_pass execution
    "learning_pass_last_run": <int|null>,  // Last learning_pass execution
    "learning_collect_buffer": []          // Accumulates session data
  }
}
```

---

## Session Increment Rules (Applied at Each Session Start)

1. `session_id += 1`
2. If missing from logs, reconstruct from recent ADDR.md entries
3. Default to `last_known + 1` if reconstruction fails

---

## Pass Definitions & Triggers

### LEARNING COLLECTION (Every Session — ALWAYS TRIGGERS)

- **Trigger**: Automatic on every session start
- **Execution Requirements**:
  - Append to learning_collect_buffer:
    - Decisions made in this session
    - Errors encountered during execution
    - Inefficiencies observed
    - Tool performance issues
    - User corrections/intent signals
- **Storage Location**: 
  - Primary: ADDR.json → `session_tracking.learning_collect_buffer[]`
  - Secondary: LEARNING_LOG.md (on-demand analysis)

### DEV PASS (Every 2 Sessions Minimum)

- **Trigger Condition**: `(session_id - dev_pass_last_run) >= 2` OR `dev_pass_last_run is null`
- **Execution Requirements**:
  - Research architectural gaps and system improvements
  - Expand design docs per CURRENT_TASK.md priorities
  - Update ADDR documentation with next-phase planning
  - Scan CHANGELOG.md for user enhancement requests
- **Post-Execution**:
  - `dev_pass_last_run = session_id`

### LEARNING PASS (Every 3 Sessions Minimum)

- **Trigger Condition**: 
  - `(session_id - learning_pass_last_run) >= 3` AND 
  - `len(learning_collect_buffer) > 0`
- **Precondition**: learning_collect_buffer NOT empty
- **Execution Requirements**:
  - Analyze: session logs + buffer data + system behavior patterns
  - Produce: optimization insights, failure pattern detection, workflow improvements
  - Update memory/system per analysis findings
- **Post-Execution**:
  - `learning_pass_last_run = session_id`
  - `learning_collect_buffer = []`

---

## Execution Order (STRICT)

At each session:

1. Increment session_id
2. Run Learning Collection (ALWAYS)
3. Execute User Request (if provided)
4. Evaluate triggers:
   - DEV PASS: if `(session_id - dev_pass_last_run) >= 2` EXECUTE
   - LEARNING PASS: if `trigger_condition_met` EXECUTE
5. Apply triggered passes AFTER user request completion
6. Failsafe validation: verify state consistency

---

## Failsafe Logic (NON-NEGOTIABLE)

### If Pass Fails to Trigger

- **Action**: Treat as critical logic failure
- **Immediate Response**:
  - Recompute counters from ADDR logs
  - Force trigger if threshold exceeded
  - Log: "CRITICAL: Missed DEV/LEARNING pass at session {N}"

### If State Missing/Corrupted

- **Reconstruction Path**:
  1. Parse recent ADDR.md entries for last dev_pass/learning_pass
  2. Extract session_id from latest entry
  3. Default missing counters to sensible values:
     - If both null → `dev_pass_last_run = 0`, `learning_pass_last_run = 0`
  - Resume without blocking execution

### If Multiple Passes Trigger Simultaneously

- **Execution Order Priority**:
  1. DEV PASS (architectural work first)
  2. LEARNING PASS (analysis after architectural update)

### If Loop/Starvation Detected

- **Actions**:
  - Force execution of overdue pass immediately
  - Reset counters if threshold exceeded for same cycle
  - Log: "LOOP DETECTED: Forced execution at session {N}"
  - Non-negotiable constraint: no skipped passes allowed

---

## FailSafe Enforcement Checklist

After each triggers evaluation:

- ✅ Session ID incremented from previous state (or reconstructed)
- ✅ Learning Collection executed (buffer populated with session data)
- ✅ DEV PASS triggered if `(session_id - dev_pass_last_run) >= 2`
- ✅ LEARNING PASS triggered if `(session_id - learning_pass_last_run) >= 3` AND buffer not empty
- ✅ Failsafe validation ran: counters recomputed, missing state reconstructed
- ✅ Multiple pass triggers handled in correct order (DEV → LEARNING)

---

## State Reconstruction Protocol (ADDR Logs Priority)

If `ADDR.json` state is missing/corrupted:

1. Scan `docs/design doc viewer/ADDR.md` for last dev_pass/learning_pass entries
2. Find nearest session ID with [x] marker for dev_pass or learning_pass
3. Set corresponding counter to that session_id OR 0 (if none found)
4. Reconstruct session_id from latest ADDR.md entry
5. Compute buffer accumulation: `N * avg_buffer_size` where N = sessions since last clear
6. Continue execution without blocking

---

## END STATE

A fully autonomous execution loop where:

- Research/design evolves continuously (DEV PASS, every 2 sessions)
- Every session contributes to learning via collection (ALWAYS)
- Periodic deep learning refines system architecture (LEARNING PASS, every 3 sessions)
- No drift detected — state persists deterministically
- No missed cycles — counter thresholds enforced strictly

---

## Next Session (Session 34) Actions

1. Load ADDR State Machine (ADDR.json + ADDR.md for latest entry)
2. Increment session_id from 33 → 34
3. Execute Learning Collection (append buffer with session 33 data)
4. Check triggers:
   - DEV PASS: `(34 - null) >= 2` → TRUE → EXECUTE IMMEDIATELY
   - LEARNING PASS: `(34 - null) >= 3` → TRUE (if buffer has data) → CHECK BUFFER, THEN IF MET → EXECUTE
5. Apply execution order if both triggered: DEV PASS → LEARNING PASS
