# JARVIS-Level Memory System v3.0 — "CORTANA-PLUS" Design

**Date**: 2026-05-03  
**Status**: DESIGN COMPLETE — READY FOR IMPLEMENTATION  
**Objective**: Next-generation hierarchical memory surpassing current research (GAAMA, WorldDB, HiMem, ByteRover)  

---

## Executive Summary

Synthesizing 7 cutting-edge research papers + OpenHands capabilities into unified JARVIS-level memory architecture:

| Research Source | Key Innovation | Integrated? |
|---------------|-----------------|-------------|
| **GAAMA** (2026) | Concept-mediated graph + Personalized PageRank | ✅ Layer 3 |
| **Kumiho** (2026) | Graph-native cognitive memory + AGM belief revision | ✅ Layer 4 |
| **MemVerse** (2025) | Dual-path (parametric + retrieval) + multimodal | ✅ Layer 4/5 |
| **WorldDB** (2026) | Recursive worlds + content-addressed nodes | ✅ Layer 3 |
| **HiMem** (2026) | Topic-Aware Event-Surprise segmentation | ✅ Layer 2→3 |
| **FluxMem** (2026) | Adaptive structure selection (Linear/Graph/Hierarchical) | ✅ Layer 4 |
| **ByteRover** (2026) | Agent-native curation + Context Tree | ✅ Layer 3→5 |
| **OpenHands** (2026) | CodeActAgent + Docker sandbox + MCP tools | ✅ Integration |

---

## 1. HIERARCHICAL MEMORY ARCHITECTURE

### 1.1 Five-Layer Model (Enhanced from Current 4-Layer)

```
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 1: ACTIVE CONTEXT (≤2000 tokens, TTL=15 steps)          │
│ Purpose: Current micro-step state for immediate LLM consumption   │
│ Sources: ADDR pointers (lazy-loaded), last 3 tool results       │
│ Eviction: TTL-based, push to Layer 2 when full                  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓ (TTL prune)
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 2: WORKING MEMORY (Session, ≤50 entries, TTL=session)   │
│ Purpose: Task decomposition tree + cross-agent message bus        │
│ Sources: Layer 1 overflow, LangGraph agent state                │
│ Structure: HiMem dual-channel (Topic + Surprise segments)        │
│ Eviction: Session end → consolidate to Layer 3                    │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓ (session consolidation)
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 3: EPISODIC STORE (ChromaDB + Graph, persistent)        │
│ Purpose: Searchable episodic memories with semantic relationships  │
│ Structure: ByteRover Context Tree + GAAMA 4-node types          │
│   - Domain nodes (e.g., "Trading", "UserPreferences")           │
│   - Topic nodes (e.g., "Phase0Audit", "ScannerIntegration")    │
│   - Subtopic nodes (e.g., "WinRate78.9%", "MCP_Wiring")       │
│   - Entry nodes (actual memory content + metadata)                │
│                                                                 │
│ GAAMA Node Types:                                                │
│   - Episode: Raw interaction turns (preserved verbatim)          │
│   - Fact: LLM-extracted atomic facts (entity-relation triples)  │
│   - Reflection: Higher-order summaries across episodes           │
│   - Concept: Cross-cutting topics (e.g., "JARVIS_Level", "MCP")│
│                                                                 │
│ Retrieval: Hybrid (Personalized PageRank + semantic similarity)   │
│   - PPR with edge-type awareness (5 edge types from GAAMA)       │
│   - Cosine similarity for query embedding                       │
│   - Additive scoring: score = α·PPR + β·similarity             │
│ Storage: ChromaDB (embeddings) + NetworkX (graph structure)     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓ (monthly consolidation)
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 4: SEMANTIC GRAPH (Knowledge Graph, persistent)           │
│ Purpose: Structured entity relationships + factual knowledge      │
│ Structure: FluxMem adaptive selection + Kumiho belief revision   │
│   - Entities: Users, tickers, strategies, concepts             │
│   - Relations: Temporal-valid (valid_time_start, valid_time_end) │
│   - Typed edges: Kumiho-style with write-time handlers         │
│                                                                 │
│ Kumiho Edge Types (with executable semantics):                    │
│   - contains: Hierarchical containment                          │
│   - refers_to: Cross-world reference                           │
│   - supersedes: Closes validity period of target               │
│   - same_as: Stages merge proposal (no silent collapse)         │
│   - contradicts: Records conflict, preserves both sides         │
│   - implies: Derived relationship                              │
│   - instance_of / subtype_of: Taxonomic relations              │
│   - causes / precedes: Causal + temporal links                 │
│                                                                 │
│ FluxMem Adaptive Selection:                                      │
│   - Selector: 2-layer MLP (12-dim → 4-dim → 3-way)           │
│   - Structures: Linear, Graph, Hierarchical                    │
│   - BMM Gate: Beta Mixture Model for distribution-aware fusion  │
│   - Threshold: 0.6 compatibility posterior, min keep 1         │
│                                                                 │
│ MemVerse Parametric Memory:                                      │
│   - Fast path: Distilled neural representations (periodically)   │
│   - Triggered: When Layer 3 growth > threshold                 │
│   - Storage: Layer 5 (compressed parametric knowledge)          │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓ (quarterly compression)
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 5: PERSISTENT BACKBONE (ADDR + Compressed)              │
│ Purpose: Single source-of-truth + cross-session consistency     │
│ Components:                                                      │
│   - ADDR: Canonical state machine (design + continuation)       │
│   - Compressed History: gzip JSON on D: SSD cache              │
│   - Parametric Memory: Model-distilled facts (Layer 4 → 5)    │
│   - User Profile: Preferences, trust level, emotional history   │
│                                                                 │
│ ByteRover Adaptive Knowledge Lifecycle (AKL):                   │
│   - Importance scoring: (recency × access_freq × relevance)     │
│   - Maturity tiers: Raw → Processed → Verified → Canonical     │
│   - Recency decay: Exponential decay on stale entries          │
│   - Cross-session: User preference learning over time           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. CONTEXT EXTENSION TECHNIQUES

### 2.1 Problem: LLM Context Limits (2k-128k tokens)
### 2.2 Solution: Multi-Pronged Approach

| Technique | Layer | Implementation | Token Reduction |
|-----------|-------|-----------------|------------------|
| **Lazy Loading** | 1→5 | ADDR sections loaded on-demand via `load_ADDR(section)` | 90%+ |
| **Compressed History** | 2→5 | gzip JSON with high-signal extraction (≤500 chars/entry) | 80%+ |
| **Memory Offloading** | 1→2 | `MemoryOffloader` (already implemented, D: SSD cache) | 70%+ |
| **Hierarchical Retrieval** | 3→4 | Coarse-to-fine: Domain→Topic→Entry (ByteRover) | 85%+ |
| **Parametric Distillation** | 4→5 | Periodic knowledge distillation to model weights | 95%+ |
| **OpenHands Offload** | 1→ext | External agent handles memory queries in parallel | 60%+ |

### 2.3 Context Window Strategy (Per Micro-LLM Step)
```python
def get_context_for_step(step_type: str, max_tokens: int = 2000) -> dict:
    """Retrieve minimal viable context for current micro-step."""
    
    # 1. Layer 1: Active context (always loaded, ≤500 tokens)
    active = memory_offloader.get_active_context(max_keys=5)
    
    # 2. Lazy load from Layer 5: Only needed ADDR sections
    addr_sections = {
        'scanner': ['Phase0Audit', 'ScannerIntegration'],
        'order': ['OrderManager', 'PaperTrading'],
        'backtest': ['PerformanceMetrics', 'WalkForward']
    }.get(step_type, ['CurrentTask'])
    
    addr_context = {
        section: load_ADDR(section) for section in addr_sections
    }
    
    # 3. Layer 3: Semantic search (top 3 relevant memories)
    episodic = episodic_store.search_memories(
        query=step_type, n_results=3
    )
    
    # 4. Combine with token budget enforcement
    context = {
        'active': active,
        'addr': addr_context,
        'episodic': episodic[:3],
        'token_count': estimate_tokens(active) + estimate_tokens(addr_context)
    }
    
    # 5. If over budget, compress further
    if context['token_count'] > max_tokens:
        context['episodic'] = episodic[:1]
        context['addr'] = {list(addr_context.keys())[0]: list(addr_context.values())[0]}
    
    return context
```

---

## 3. OPENHANDS INTEGRATION

### 3.1 OpenHands as "External Memory Processor"

```python
class OpenHandsMemoryBridge:
    """Offloads memory operations to OpenHands CodeActAgent in Docker sandbox."""
    
    def __init__(self):
        self.oh_workspace = APIRemoteWorkspace(
            runtime_api_url="https://runtime.eval.all-hands.dev",
            runtime_api_key=os.getenv("OPENHANDS_API_KEY")
        )
        self.agent = get_default_agent(llm=llm, cli_mode=True)
    
    async def consolidate_memories(self, source_layer: int, target_layer: int):
        """Run memory consolidation in OpenHands sandbox."""
        
        conversation = Conversation(
            agent=self.agent, 
            workspace=self.oh_workspace
        )
        
        # Task: Read Layer 3 episodic, extract facts, write to Layer 4
        task = f"""
        Read episodic memories from ChromaDB (layer {source_layer}).
        Extract atomic facts and build knowledge graph.
        Write results to Layer 4 semantic graph.
        Update ADDR with consolidation timestamp.
        """
        
        conversation.send_message(task)
        conversation.run()
        
        # Retrieve results
        result = conversation.get_result()
        conversation.close()
        
        return result
    
    async def safe_backtest_execution(self, strategy_code: str, data: pd.DataFrame):
        """Execute backtest in OpenHands sandbox (isolated from main system)."""
        
        # Write strategy to temp file in sandbox
        conversation = Conversation(agent=self.agent, workspace=self.oh_workspace)
        
        conversation.send_message(f"""
        Write the following strategy code to /tmp/strategy.py:
        {strategy_code}
        
        Run backtest with provided data.
        Return Sharpe ratio, win rate, max drawdown.
        Do NOT modify main AlphaChart files.
        """)
        
        conversation.run()
        return conversation.get_result()
```

### 3.2 OpenHands Tool Bridge (MCP ↔ OpenHands)

```
AlphaChart MCP Server (6 tools) ←→ OpenHands Agent (CodeActAgent)
                                     ↓
                            Docker Sandbox (isolated execution)
                                     ↓
                            Safe strategy testing, memory ops
```

**Implementation**: Extend `core/mcp/alphachart_mcp_server.py` with OpenHands tools:
```python
@mcp.tool()
def openhands_consolidate_memories(layer_from: int, layer_to: int) -> dict:
    """Trigger OpenHands agent to consolidate memories between layers."""
    bridge = OpenHandsMemoryBridge()
    return await bridge.consolidate_memories(layer_from, layer_to)

@mcp.tool()
def openhands_safe_backtest(strategy_code: str, ticker: str) -> dict:
    """Run backtest in OpenHands sandbox (no risk to main system)."""
    bridge = OpenHandsMemoryBridge()
    data = DataFetcher().fetch(ticker, period="1y")
    return await bridge.safe_backtest_execution(strategy_code, data)
```

---

## 4. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-2) — CORE LAYERS
| Task | Research Source | Priority |
|------|----------------|----------|
| Implement Layer 3 Context Tree (ByteRover) | ByteRover | HIGH |
| Add GAAMA 4-node types to ChromaDB | GAAMA | HIGH |
| Implement Personalized PageRank retrieval | GAAMA | HIGH |
| Add Kumiho-style typed edges (5+ types) | Kumiho | MEDIUM |
| Write OpenHands bridge (basic) | OpenHands | HIGH |

### Phase 2: Intelligence (Weeks 3-4) — ADAPTIVE + PREDICTIVE
| Task | Research Source | Priority |
|------|----------------|----------|
| Implement FluxMem adaptive selector (MLP) | FluxMem | HIGH |
| Add HiMem dual-channel segmentation | HiMem | MEDIUM |
| Build MemVerse parametric memory distillation | MemVerse | MEDIUM |
| Integrate OpenHands for safe backtesting | OpenHands | HIGH |
| Add BMM gate for memory fusion | FluxMem | LOW |

### Phase 3: Consolidation (Weeks 5-6) — AUTONOMOUS OPERATIONS
| Task | Research Source | Priority |
|------|----------------|----------|
| Background consolidation (Layer 2→3 monthly) | GAAMA | HIGH |
| Kumiho belief revision (AGM postulates) | Kumiho | MEDIUM |
| WorldDB recursive world operations | WorldDB | LOW |
| OpenHands scheduled maintenance tasks | OpenHands | MEDIUM |
| ByteRover AKL (importance scoring) | ByteRover | HIGH |

### Phase 4: Multimodal (Weeks 7-8) — EXTEND TO ALL MODALITIES
| Task | Research Source | Priority |
|------|----------------|----------|
| MemVerse multimodal embeddings (text+image+audio) | MemVerse | MEDIUM |
| Vision memory (YOLO detections → episodic) | MemVerse | MEDIUM |
| Cross-modal retrieval (text query → image result) | MemVerse | LOW |
| OpenHands multimodal sandbox (screenshots) | OpenHands | LOW |

---

## 5. SUCCESS METRICS (Next-Gen Validation)

### Quantitative
- [ ] **Layer 3 Retrieval Accuracy**: >78.9% (beat GAAMA on LoCoMo-10)
- [ ] **Context Reduction**: <2000 tokens for 95% of micro-steps
- [ ] **Memory Consolidation Speed**: <5 min for 1000 episodic → 100 semantic facts
- [ ] **OpenHands Offload**: 60%+ reduction in main agent context load
- [ ] **Adaptive Structure Selection**: >85% appropriate structure choice (FluxMem MLP)

### Qualitative
- [ ] **"Feels like JARVIS"**: User reports memory recall matches intent
- [ ] **Proactive Recall**: System surfaces relevant memories before asked
- [ ] **Cross-Session Learning**: Preferences persist and improve over time
- [ ] **Safe Autonomy**: OpenHands sandbox prevents all main system corruption

---

## 6. ITERATIVE IMPROVEMENT LOOP

```
1. IMPLEMENT → 2. BENCHMARK (LoCoMo-10, LongMemEval-s) → 3. ANALYZE → 4. REDESIGN
        ↑________________________________________________________________↓
```

**Next Iteration Targets** (post-implementation):
1. Replace ChromaDB with WorldDB-style recursive world store
2. Add MemVerse-style multimodal embeddings (CLIP for images)
3. Implement Kumiho AGM belief revision for contradiction handling
4. Extend OpenHands bridge to multi-agent coordination (LangGraph + OpenHands)

---

## 7. FILE STRUCTURE (New Modules to Create)

```
core/memory/
├── episodic_store.py          (EXISTS — upgrade to GAAMA 4-node types)
├── semantic_graph.py          (NEW — Kumiho + FluxMem)
├── context_tree.py            (NEW — ByteRover hierarchical)
├── consolidation_engine.py    (NEW — GAAMA/HiMem pipelines)
├── parametric_distiller.py   (NEW — MemVerse fast path)
└── __init__.py               (UPDATE — export new modules)

core/integration/
├── openhands_bridge.py       (NEW — OpenHands MemoryBridge)
├── openhands_tools.py        (NEW — MCP tools for OpenHands)
└── __init__.py               (NEW — package init)

core/adaptive/
├── fluxmem_selector.py       (NEW — MLP structure selection)
├── himem_segmenter.py       (NEW — Dual-channel segmentation)
├── worlddb_store.py          (NEW — Recursive world operations)
└── __init__.py               (NEW — package init)
```

---

*End of JARVIS-Level Memory System v3.0 Design — Ready for Implementation*

**Next Step**: Begin Phase 1 implementation (Layer 3 Context Tree + GAAMA nodes + OpenHands bridge)
