# Workflow Analysis (Previous Session)

## Key Insights
- MCP server grew to 22 tools; syntax errors fixed (missing commas in dict literals)
- Phase 0 Backtest Audit failed: win rate 32% < 60%, Sharpe -0.42, regime coverage insufficient
- Scanner integration complete but end-to-end verification pending
- CHANGELOG automation added; backup location centralized to `docs/archive/backups/`
- SESSION_STATE populated on search/read_doc (partial completion)

## Recommendations for Efficiency/Speed/Cost
1. **Reduce redundant tool calls**: Batch MCP tool calls where possible (e.g., read multiple doc sections in one call)
2. **Streamline patch workflow**: Auto‑trigger `build_design_doc` after `apply_patch` to keep design docs current
3. **Index optimization**: Pre‑compute search indices offline; avoid re‑indexing on every `read_doc`
4. **Token reduction**: Truncate long outputs (e.g., `search` results) to essential fields only

## Edge Cases & Mitigations
- **Backup dir missing**: Now handled by `BACKUP_DIR.mkdir(parents=True, exist_ok=True)`
- **CHANGELOG write contention**: Append‑only mode; no locking (acceptable for single‑user)
- **Broken link cascade**: `scan_links` tool exists but not automated; add to `apply_patch` pipeline
- **SESSION_STATE overflow**: Limit history length (e.g., keep last 10 queries)

## ADDR‑GUI Integration Architecture
- **Tab layout**: Add "Docs" tab to Streamlit GUI with three panels:
  - Left: document index (from `doc_registry.json`)
  - Center: document viewer with section navigation
  - Right: context‑aware search bar (calls `search` tool)
- **Unified interface**: Merge ADDR’s indexed access with GUI’s output panels (scanner results, backtest stats)
- **Implementation**: Use Streamlit’s `st.expander` for document tree; `st.markdown` for rendering

## Documentation Expansion Plan
1. **User Manual**: Create `USER_MANUAL.md`, register in `DOC_REGISTRY`, index with ADDR
2. **Service Manual**: Create `SERVICE_MANUAL.md` (maintenance, deployment), same treatment
3. **Maintenance**: Add `add_doc` tool calls to CI pipeline (or `apply_patch` trigger) to auto‑register new `.md` files
4. **Access**: Both manuals searchable via `search` tool; GUI tab provides direct links

## Next Steps (from this analysis)
- Implement `build_design_doc` tool to auto‑generate `AlphaChart_design.md`
- Add broken‑link scan to `apply_patch` pipeline
- Verify scanner end‑to‑end via `run.bat`
- Retrain model to pass Phase 0 Backtest Audit
