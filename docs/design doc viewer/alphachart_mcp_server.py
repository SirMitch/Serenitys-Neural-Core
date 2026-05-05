#!/usr/bin/env python3
"""
AlphaChart v3.4 — MCP Server for OpenCode
==========================================
Gives OpenCode precision read/search access to the full AlphaChart
design manual via the Model Context Protocol (stdio transport).

No external dependencies — pure Python 3.9+ stdlib only.

Usage (opencode config):
  {
    "mcpServers": {
      "alphachart": {
        "command": "python",
        "args": ["/path/to/alphachart_mcp_server.py"],
        "env": { "ALPHACHART_DOCS": "/path/to/your/docs/folder" }
      }
    }
  }
"""

import sys
import os
import re
import json
import threading
from pathlib import Path
from collections import defaultdict
from typing import Any

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
DOCS_DIR = Path(os.environ.get("ALPHACHART_DOCS", Path(__file__).parent))

DOC_REGISTRY = {
    "AC_00": {"file": "AC_00_Master_Orchestrator.md",       "title": "Master Orchestrator & System Integration"},
    "AC_01-04": {"file": "AC_01_04_Signal_Engines.md",      "title": "Signal Generation Engines (Ensemble · MTA · Regime · FinRL-X)"},
    "AC_05-08": {"file": "AC_05_08_Safety_Risk.md",         "title": "Safety, Quality & Risk (ML Factor · Safety Layer · LLM Gate · Sizing)"},
    "AC_09-11": {"file": "AC_09_11_Discovery_GUI.md",       "title": "Discovery, Scanner & GUI (Market Scanner · Portfolio · BIOS GUI)"},
    "AC_12-14": {"file": "AC_12_14_Learning_Orders_Backtest.md", "title": "Learning, Orders & Backtest (RAG · RLMF · Order Mgr · Phase 0)"},
    "SCANNER":  {"file": "AlphaChart_v3_4_Scanner_Mode_v2.md", "title": "Market-Wide Scanner Mode — Production"},
    "MAIN":     {"file": "AlphaChart_v3_4.md",              "title": "AlphaChart v3.4 Main Design Document"},
}

# ─── DOCUMENT INDEX ───────────────────────────────────────────────────────────
class ManualIndex:
    """
    In-memory index of all AlphaChart design documents.
    Built once at startup for O(1) doc access and fast full-text search.
    """

    def __init__(self):
        self.docs:     dict[str, str]              = {}   # id → raw text
        self.sections: dict[str, list[dict]]       = {}   # id → [{heading, level, body}]
        self.code_blocks: dict[str, list[dict]]    = {}   # id → [{lang, code, line}]
        self.index:    dict[str, list[dict]]       = defaultdict(list)  # word → [{doc, line, ctx}]
        self._load_all()
        self._build_index()

    # ── Loaders ───────────────────────────────────────────────────────────────

    def _load_all(self):
        for doc_id, meta in DOC_REGISTRY.items():
            path = DOCS_DIR / meta["file"]
            if path.exists():
                text = path.read_text(encoding="utf-8")
                self.docs[doc_id]        = text
                self.sections[doc_id]    = self._parse_sections(text)
                self.code_blocks[doc_id] = self._parse_code_blocks(text)
            else:
                self.docs[doc_id] = f"[File not found: {meta['file']}]"
                self.sections[doc_id]    = []
                self.code_blocks[doc_id] = []

    def _parse_sections(self, text: str) -> list[dict]:
        sections, current, body_lines = [], None, []
        for line in text.splitlines():
            m = re.match(r'^(#{1,4})\s+(.+)', line)
            if m:
                if current:
                    current["body"] = "\n".join(body_lines).strip()
                    sections.append(current)
                current    = {"heading": m.group(2).strip(),
                              "level":   len(m.group(1)),
                              "body":    ""}
                body_lines = []
            else:
                if current:
                    body_lines.append(line)
        if current:
            current["body"] = "\n".join(body_lines).strip()
            sections.append(current)
        return sections

    def _parse_code_blocks(self, text: str) -> list[dict]:
        blocks, in_block, lang, lines, start = [], False, "", [], 0
        for i, line in enumerate(text.splitlines(), 1):
            if line.startswith("```") and not in_block:
                in_block, lang, lines, start = True, line[3:].strip(), [], i
            elif line.startswith("```") and in_block:
                blocks.append({"lang": lang, "code": "\n".join(lines), "line": start})
                in_block = False
            elif in_block:
                lines.append(line)
        return blocks

    def _build_index(self):
        """Token-level inverted index with ±2 line context windows."""
        for doc_id, text in self.docs.items():
            lines = text.splitlines()
            for i, line in enumerate(lines):
                tokens = re.findall(r'\b\w{3,}\b', line.lower())
                for token in set(tokens):
                    ctx_start = max(0, i - 2)
                    ctx_end   = min(len(lines), i + 3)
                    context   = "\n".join(lines[ctx_start:ctx_end])
                    self.index[token].append({
                        "doc":     doc_id,
                        "line":    i + 1,
                        "context": context,
                        "excerpt": line.strip(),
                    })

    # ── Query Methods ─────────────────────────────────────────────────────────

    def search(self, query: str, top_n: int = 20,
               doc_filter: str = None) -> list[dict]:
        """
        Multi-token AND search. Returns ranked results with context.
        Each result represents a line matching ALL query tokens.
        """
        tokens = re.findall(r'\b\w{3,}\b', query.lower())
        if not tokens:
            return []

        # Per-token candidate sets: {(doc_id, line_num) → context}
        candidate_maps = []
        for token in tokens:
            hits = self.index.get(token, [])
            if doc_filter:
                hits = [h for h in hits if h["doc"] == doc_filter]
            m = {(h["doc"], h["line"]): h for h in hits}
            candidate_maps.append(m)

        if not candidate_maps:
            return []

        # AND: intersection across all token maps
        common_keys = set(candidate_maps[0].keys())
        for cm in candidate_maps[1:]:
            common_keys &= set(cm.keys())

        if not common_keys:
            # Fallback: OR search, rank by token hit count
            all_hits = defaultdict(int)
            all_data = {}
            for cm in candidate_maps:
                for key, val in cm.items():
                    all_hits[key] += 1
                    all_data[key] = val
            ranked = sorted(all_data.keys(),
                            key=lambda k: all_hits[k], reverse=True)
            results = [all_data[k] for k in ranked[:top_n]]
        else:
            results = [candidate_maps[0][k] for k in list(common_keys)[:top_n]]

        # Deduplicate by doc+excerpt and enrich
        seen, out = set(), []
        for r in results:
            key = (r["doc"], r["excerpt"][:60])
            if key not in seen:
                seen.add(key)
                r["doc_title"] = DOC_REGISTRY.get(r["doc"], {}).get("title", r["doc"])
                out.append(r)
        return out[:top_n]

    def get_section(self, doc_id: str, heading_query: str) -> dict | None:
        """Fuzzy heading match — returns best matching section."""
        sections = self.sections.get(doc_id.upper(), [])
        query    = heading_query.lower()
        best, best_score = None, 0
        for sec in sections:
            h = sec["heading"].lower()
            # Exact match wins
            if query == h:
                return sec
            # Score: shared tokens
            q_toks = set(query.split())
            h_toks = set(h.split())
            score  = len(q_toks & h_toks) / max(len(q_toks), 1)
            if score > best_score:
                best_score, best = score, sec
        return best if best_score > 0.3 else None

    def search_code(self, query: str, lang_filter: str = None) -> list[dict]:
        """Search within code blocks only. Returns blocks containing the query."""
        results = []
        q_lower = query.lower()
        for doc_id, blocks in self.code_blocks.items():
            for block in blocks:
                if lang_filter and block["lang"] not in (lang_filter, ""):
                    continue
                if q_lower in block["code"].lower():
                    # Find matching lines
                    match_lines = [l for l in block["code"].splitlines()
                                   if q_lower in l.lower()]
                    results.append({
                        "doc":      doc_id,
                        "doc_title":DOC_REGISTRY.get(doc_id, {}).get("title", doc_id),
                        "lang":     block["lang"] or "text",
                        "line":     block["line"],
                        "matches":  match_lines[:5],
                        "snippet":  block["code"][:600],
                    })
        return results

# ─── SINGLETON INDEX (built once at startup) ──────────────────────────────────
_index: ManualIndex | None = None
_index_lock = threading.Lock()

def get_index() -> ManualIndex:
    global _index
    if _index is None:
        with _index_lock:
            if _index is None:
                _index = ManualIndex()
    return _index

# ─── TOOL DEFINITIONS ─────────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "list_docs",
        "description": (
            "List all AlphaChart v3.4 design documents available in the manual. "
            "Returns document IDs, titles, and file names. Call this first to know what's available."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "read_doc",
        "description": (
            "Read the full content of an AlphaChart design document by its ID. "
            "Use list_docs to get valid IDs. Returns the full markdown text. "
            "For large docs, prefer get_section or search instead."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_id":    {"type": "string", "description": "Document ID e.g. 'AC_00', 'AC_01-04', 'SCANNER'"},
                "max_chars": {"type": "integer", "description": "Truncate to this many characters (default: no limit)", "default": 0},
            },
            "required": ["doc_id"],
        },
    },
    {
        "name": "get_toc",
        "description": (
            "Get the table of contents (all headings) for a specific document. "
            "Use this to understand a document's structure before reading sections."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document ID"},
            },
            "required": ["doc_id"],
        },
    },
    {
        "name": "get_section",
        "description": (
            "Get a specific section from a document by heading name. "
            "Uses fuzzy matching — partial heading text is fine. "
            "Returns the section heading and its full body content."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_id":  {"type": "string", "description": "Document ID"},
                "heading": {"type": "string", "description": "Section heading to find (partial match OK)"},
            },
            "required": ["doc_id", "heading"],
        },
    },
    {
        "name": "search",
        "description": (
            "Full-text search across ALL AlphaChart design documents. "
            "Returns ranked results with ±2 line context windows. "
            "Multi-word queries use AND logic (all terms must appear). "
            "Optionally filter by doc_id to search within one document."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query":      {"type": "string", "description": "Search terms e.g. 'conviction score ensemble weights'"},
                "doc_id":     {"type": "string", "description": "Optional: restrict search to one doc ID"},
                "top_n":      {"type": "integer", "description": "Max results to return (default: 15)", "default": 15},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_code",
        "description": (
            "Search within Python code blocks only across all documents. "
            "Ideal for finding class names, function signatures, constants, and implementation details. "
            "Returns the code block snippet and matching lines."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string", "description": "Code term to find e.g. 'EnsembleAggregator' or 'HARD_MAX_RISK_PCT'"},
                "lang_filter": {"type": "string", "description": "Optional language filter e.g. 'python'"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_principles",
        "description": (
            "Return the 10 Universal Design Principles that govern all AlphaChart modules. "
            "Quick reference — no need to read the full Master Orchestrator doc."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_hard_limits",
        "description": (
            "Return the complete Hard Safety Limit registry from alphachart/core/safety.py. "
            "These are immutable system constants. Quick reference for any risk/safety question."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_integration_contract",
        "description": (
            "Get the integration contract between two AlphaChart modules — "
            "what one module produces and what the next requires. "
            "Specify source and destination module IDs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_module": {"type": "string", "description": "Source module e.g. 'AC_02', 'LLM', 'Ensemble'"},
                "to_module":   {"type": "string", "description": "Destination module e.g. 'AC_01', 'Sizer', 'OrderManager'"},
            },
            "required": ["from_module", "to_module"],
        },
    },
]

# ─── TOOL HANDLERS ────────────────────────────────────────────────────────────
def handle_list_docs(_args: dict) -> str:
    idx = get_index()
    lines = ["# AlphaChart v3.4 — Available Documents\n"]
    for doc_id, meta in DOC_REGISTRY.items():
        loaded = doc_id in idx.docs and not idx.docs[doc_id].startswith("[File not found")
        status = "✓" if loaded else "✗ NOT FOUND"
        n_secs  = len(idx.sections.get(doc_id, []))
        n_code  = len(idx.code_blocks.get(doc_id, []))
        chars   = len(idx.docs.get(doc_id, ""))
        lines.append(
            f"**{doc_id}** {status}\n"
            f"  Title:    {meta['title']}\n"
            f"  File:     {meta['file']}\n"
            f"  Size:     {chars:,} chars | {n_secs} sections | {n_code} code blocks\n"
        )
    return "\n".join(lines)


def handle_read_doc(args: dict) -> str:
    doc_id   = args.get("doc_id", "").upper()
    max_ch   = int(args.get("max_chars", 0))
    idx      = get_index()
    if doc_id not in idx.docs:
        close = [k for k in idx.docs if doc_id in k or k in doc_id]
        hint  = f"\nDid you mean: {close}" if close else ""
        return f"Unknown doc_id '{doc_id}'.{hint}\nValid IDs: {list(DOC_REGISTRY.keys())}"
    text = idx.docs[doc_id]
    if max_ch and max_ch > 0:
        text = text[:max_ch] + (f"\n\n[...truncated at {max_ch} chars — "
                                 f"full doc is {len(idx.docs[doc_id]):,} chars]"
                                 if len(idx.docs[doc_id]) > max_ch else "")
    return text


def handle_get_toc(args: dict) -> str:
    doc_id = args.get("doc_id", "").upper()
    idx    = get_index()
    if doc_id not in idx.sections:
        return f"Unknown doc_id '{doc_id}'."
    secs = idx.sections[doc_id]
    if not secs:
        return f"No headings found in {doc_id}."
    meta  = DOC_REGISTRY.get(doc_id, {})
    lines = [f"# Table of Contents — {meta.get('title', doc_id)}\n"]
    for i, sec in enumerate(secs, 1):
        indent = "  " * (sec["level"] - 1)
        body_preview = sec["body"][:80].replace("\n"," ").strip()
        lines.append(f"{indent}{i}. **{sec['heading']}** (H{sec['level']})")
        if body_preview:
            lines.append(f"{indent}   _\"{body_preview}{'...' if len(sec['body'])>80 else ''}\"_")
    return "\n".join(lines)


def handle_get_section(args: dict) -> str:
    doc_id  = args.get("doc_id", "").upper()
    heading = args.get("heading", "")
    idx     = get_index()
    sec     = idx.get_section(doc_id, heading)
    if not sec:
        # Show available headings as hint
        available = [s["heading"] for s in idx.sections.get(doc_id, [])][:20]
        return (f"Section matching '{heading}' not found in {doc_id}.\n"
                f"Available headings:\n" +
                "\n".join(f"  - {h}" for h in available))
    return (f"## {sec['heading']} (H{sec['level']})\n\n"
            f"**Document:** {DOC_REGISTRY.get(doc_id,{}).get('title', doc_id)}\n\n"
            f"{sec['body']}")


def handle_search(args: dict) -> str:
    query      = args.get("query", "")
    doc_filter = args.get("doc_id", None)
    top_n      = int(args.get("top_n", 15))
    idx        = get_index()

    if doc_filter:
        doc_filter = doc_filter.upper()

    results = idx.search(query, top_n=top_n, doc_filter=doc_filter)
    if not results:
        return f"No results found for: **{query}**\nTry broader terms or remove the doc filter."

    lines = [f"# Search Results: \"{query}\"\n",
             f"Found **{len(results)}** result(s):\n"]
    for i, r in enumerate(results, 1):
        lines.append(
            f"---\n"
            f"**Result {i}** · `{r['doc']}` · Line {r['line']}\n"
            f"_{r['doc_title']}_\n\n"
            f"```\n{r['context']}\n```"
        )
    return "\n".join(lines)


def handle_search_code(args: dict) -> str:
    query       = args.get("query", "")
    lang_filter = args.get("lang_filter", None)
    idx         = get_index()
    results     = idx.search_code(query, lang_filter=lang_filter)

    if not results:
        return f"No code blocks found containing: **{query}**"

    lines = [f"# Code Search: \"{query}\"\n",
             f"Found **{len(results)}** code block(s):\n"]
    for i, r in enumerate(results, 1):
        matches_fmt = "\n".join(f"  {m.strip()}" for m in r["matches"])
        lines.append(
            f"---\n"
            f"**Block {i}** · `{r['doc']}` · Line {r['line']} · `{r['lang']}`\n"
            f"_{r['doc_title']}_\n\n"
            f"**Matching lines:**\n```\n{matches_fmt}\n```\n\n"
            f"**Snippet:**\n```{r['lang']}\n{r['snippet']}\n```"
        )
    return "\n".join(lines)


def handle_get_principles(_args: dict) -> str:
    return """# AlphaChart v3.4 — 10 Universal Design Principles
*(from AC_00 §7 — binding on every module)*

**PRINCIPLE 1 — NUMERICAL PIPELINE OWNS DIRECTION**
The ensemble (AC_01) makes all directional decisions. The LLM (AC_07) evaluates
quality only — never direction. No module may override a direction set by the ensemble.

**PRINCIPLE 2 — HARD LIMITS ARE IMMUTABLE CODE CONSTANTS**
All HARD_* constants live in alphachart/core/safety.py. Never in config, DBs, or settings.
No runtime path, slider, or API call can modify them.

**PRINCIPLE 3 — PHASE 0 IS THE UNCONDITIONAL GATE**
No model proceeds to paper trading without passing the 7-step Phase 0 audit (AC_14).
No exception. No bypass. No timeout overrides this gate.

**PRINCIPLE 4 — ISOLATION: ONE TICKER NEVER BLOCKS ANOTHER**
All per-ticker operations are wrapped in try/except. A failure on NVDA never
prevents AAPL from being processed.

**PRINCIPLE 5 — CHEAP LAYERS FIRST**
Order: static metadata → vectorized technical → ensemble → safety → LLM.
Expensive operations (LLM, FinRL-X) only run on candidates that cleared cheaper filters.

**PRINCIPLE 6 — AUDITABILITY OVER PERFORMANCE**
Every signal has a complete, reproducible audit trail. Every rejection has a reason code.
Every trade outcome is recorded and linked to the originating signal.

**PRINCIPLE 7 — STATE-LOCK PREVENTS RACE CONDITIONS**
No two concurrent operations may act on the same ticker simultaneously.
StateLock (AC_13) is the single authority for per-ticker locking.

**PRINCIPLE 8 — LLM FAILURES DEFAULT TO REJECTION**
Any LLM timeout, parse failure, or exception → automatic signal rejection.
There is no fallback approval path.

**PRINCIPLE 9 — RSI IS NEVER A SOLE SIGNAL**
RSI may only appear as one factor among multiple factors. Any signal whose conviction
derives primarily from RSI alone is blocked by the DeterministicSafetyFilter.

**PRINCIPLE 10 — TRENDING_DOWN DEMANDS ADDITIONAL SCRUTINY**
All LONG signals in a TRENDING_DOWN regime receive an automatic conviction penalty
and quality floor raise. See AC_03 and safety.py for exact parameters."""


def handle_get_hard_limits(_args: dict) -> str:
    return """# AlphaChart v3.4 — Hard Safety Limit Registry
*(alphachart/core/safety.py — IMMUTABLE)*

## Position-Level Limits
| Constant                       | Value    | Description                          |
|-------------------------------|----------|--------------------------------------|
| HARD_MAX_RISK_PCT             | 0.05     | 5% of portfolio per trade — absolute ceiling |
| HARD_MIN_STOP_LOSS_ATR_MULT   | 1.0      | Stop must be ≥ 1 ATR from entry      |
| HARD_MIN_RR_RATIO             | 1.0      | Minimum risk:reward ratio            |

## Portfolio-Level Limits
| Constant                       | Value    | Description                          |
|-------------------------------|----------|--------------------------------------|
| HARD_MAX_PORTFOLIO_DRAWDOWN   | 0.20     | 20% → full system halt               |
| HARD_MAX_CONCURRENT_TRADES    | 15       | Absolute cap on open positions        |
| HARD_MAX_SECTOR_CONCENTRATION | 0.40     | No sector > 40% of portfolio         |

## Signal Quality Limits
| Constant                       | Value    | Description                          |
|-------------------------------|----------|--------------------------------------|
| HARD_MIN_CONVICTION_FLOOR     | 0.50     | No signal below 50% conviction approved |
| HARD_MIN_QUALITY_FLOOR        | 0.50     | No signal below 50% LLM quality approved |

## Trading Environment Limits
| Constant                       | Value    | Description                          |
|-------------------------------|----------|--------------------------------------|
| HARD_MIN_LIQUIDITY_VOLUME     | 500,000  | Min avg daily volume for any signal  |
| HARD_EARNINGS_BLACKOUT_DAYS   | 2        | No entries within ±2 days of earnings |
| HARD_MAX_GAP_PCT              | 0.03     | No entries after >3% overnight gap   |
| HARD_MARKET_OPEN_BLACKOUT_MIN | 15       | No entries in first 15 min after open |

## Order Execution Limits
| Constant                       | Value    | Description                          |
|-------------------------------|----------|--------------------------------------|
| HARD_ORDER_TYPE               | "limit"  | All orders are limit orders          |
| HARD_AUTO_APPROVE_MAX_N       | 10       | Auto-approve cap (scanner)           |

## TRENDING_DOWN Remediation
| Constant                            | Value  | Description                     |
|------------------------------------|--------|---------------------------------|
| TREND_DOWN_LONG_CONVICTION_PENALTY | 0.30   | LONG conviction × 0.70          |
| TREND_DOWN_LONG_QUALITY_FLOOR_RAISE| 0.10   | Raise min quality by 10pp       |
| TREND_DOWN_SHORT_CONVICTION_BOOST  | 0.10   | SHORT conviction × 1.10         |
| TREND_DOWN_MAX_LONG_POSITION_PCT   | 0.02   | LONG positions capped at 2%     |"""


def handle_get_integration_contract(args: dict) -> str:
    from_m = args.get("from_module", "").upper()
    to_m   = args.get("to_module", "").upper()
    idx    = get_index()

    # Search the master orchestrator for the contract
    query   = f"{from_m} {to_m} produces requires contract"
    results = idx.search(query, top_n=8, doc_filter="AC_00")

    if not results:
        # Broader search
        results = idx.search(f"{from_m} {to_m}", top_n=8)

    if not results:
        return (f"No integration contract found for {from_m} → {to_m}.\n"
                f"Try: read_doc(doc_id='AC_00') and search for §5 Integration Contracts.")

    lines = [f"# Integration Contract: {from_m} → {to_m}\n",
             "*(Extracted from AC_00 §5 — Integration Contracts)*\n"]
    for r in results:
        lines.append(f"```\n{r['context']}\n```\n")

    lines.append("\n> For full contract details: get_section(doc_id='AC_00', heading='Integration Contracts')")
    return "\n".join(lines)


HANDLERS = {
    "list_docs":                handle_list_docs,
    "read_doc":                 handle_read_doc,
    "get_toc":                  handle_get_toc,
    "get_section":              handle_get_section,
    "search":                   handle_search,
    "search_code":              handle_search_code,
    "get_principles":           handle_get_principles,
    "get_hard_limits":          handle_get_hard_limits,
    "get_integration_contract": handle_get_integration_contract,
}

# ─── MCP STDIO SERVER ─────────────────────────────────────────────────────────
def send(msg: dict):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

def err(msg: str):
    sys.stderr.write(f"[alphachart-mcp] {msg}\n")
    sys.stderr.flush()

def make_error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id,
            "error": {"code": code, "message": message}}

def make_result(req_id, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}

def handle_request(req: dict) -> dict | None:
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params", {})

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    if method == "initialize":
        return make_result(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities":    {"tools": {}},
            "serverInfo":      {
                "name":    "alphachart-manual",
                "version": "3.4.0",
            },
        })

    if method == "initialized":
        err("Index building... (first request may be slow)")
        # Trigger index build in background
        threading.Thread(target=get_index, daemon=True).start()
        return None  # notification — no response

    if method == "ping":
        return make_result(req_id, {})

    # ── Tools ─────────────────────────────────────────────────────────────────
    if method == "tools/list":
        return make_result(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        if tool_name not in HANDLERS:
            return make_error(req_id, -32601,
                              f"Unknown tool: '{tool_name}'. "
                              f"Valid tools: {list(HANDLERS.keys())}")
        try:
            result_text = HANDLERS[tool_name](tool_args)
            return make_result(req_id, {
                "content": [{"type": "text", "text": result_text}],
                "isError": False,
            })
        except Exception as e:
            err(f"Tool '{tool_name}' error: {e}")
            return make_result(req_id, {
                "content": [{"type": "text",
                             "text": f"Tool error: {type(e).__name__}: {e}"}],
                "isError": True,
            })

    # ── Resources (minimal stubs) ──────────────────────────────────────────────
    if method == "resources/list":
        return make_result(req_id, {"resources": []})

    if method == "prompts/list":
        return make_result(req_id, {"prompts": []})

    # Unknown method
    return make_error(req_id, -32601, f"Method not found: {method}")


def main():
    err(f"AlphaChart v3.4 MCP Server starting — docs: {DOCS_DIR}")
    err(f"Loaded {len(DOC_REGISTRY)} document registrations")

    # Warm up index in background so first search is fast
    threading.Thread(target=get_index, daemon=True).start()

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            req      = json.loads(raw_line)
            response = handle_request(req)
            if response is not None:
                send(response)
        except json.JSONDecodeError as e:
            send({"jsonrpc": "2.0", "id": None,
                  "error": {"code": -32700, "message": f"Parse error: {e}"}})
        except Exception as e:
            err(f"Unhandled error: {e}")
            send({"jsonrpc": "2.0", "id": None,
                  "error": {"code": -32603, "message": f"Internal error: {e}"}})


if __name__ == "__main__":
    main()
