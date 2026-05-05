"""
AlphaChart v3.4 — Manual Viewer
Run with: streamlit run alphachart_manual_viewer.py
"""

import streamlit as st
import re
from pathlib import Path

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AlphaChart v3.4 — Manual",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── DOCUMENT REGISTRY ────────────────────────────────────────────────────────
DOCS = [
    {
        "id": "AC_00",
        "title": "Master Orchestrator",
        "subtitle": "System Integration & Architecture",
        "file": "AC_00_Master_Orchestrator.md",
        "tag": "CANONICAL",
        "tag_color": "#f0a500",
        "icon": "🏛",
        "domain": "System-Wide",
    },
    {
        "id": "AC_01–04",
        "title": "Signal Generation Engines",
        "subtitle": "Ensemble · Multi-TF · Regime · FinRL-X",
        "file": "AC_01_04_Signal_Engines.md",
        "tag": "SIGNAL",
        "tag_color": "#7c5cbf",
        "icon": "⚡",
        "domain": "Signal Generation",
    },
    {
        "id": "AC_05–08",
        "title": "Safety, Quality & Risk",
        "subtitle": "ML Factor · Safety Layer · LLM Gate · Position Sizing",
        "file": "AC_05_08_Safety_Risk.md",
        "tag": "SAFETY",
        "tag_color": "#c0392b",
        "icon": "🛡",
        "domain": "Safety / Risk",
    },
    {
        "id": "AC_09–11",
        "title": "Discovery, Scanning & GUI",
        "subtitle": "Market Scanner · Portfolio Scanner · BIOS GUI",
        "file": "AC_09_11_Discovery_GUI.md",
        "tag": "INTERFACE",
        "tag_color": "#1a7a4a",
        "icon": "🔍",
        "domain": "Discovery / UI",
    },
    {
        "id": "AC_12–14",
        "title": "Learning, Orders & Backtest",
        "subtitle": "RAG Memory · RLMF · Order Manager · Phase 0 Audit",
        "file": "AC_12_14_Learning_Orders_Backtest.md",
        "tag": "LEARNING",
        "tag_color": "#1565c0",
        "icon": "🧠",
        "domain": "Learning / Execution / Validation",
    },
    {
        "id": "AC_09-EXT",
        "title": "Scanner Mode — Production",
        "subtitle": "Market-Wide Scanner v2 (Supplemental)",
        "file": "AlphaChart_v3_4_Scanner_Mode_v2.md",
        "tag": "SUPPLEMENTAL",
        "tag_color": "#2e7d6e",
        "icon": "📡",
        "domain": "Discovery",
    },
    {
        "id": "v3.4",
        "title": "v3.4 Main Design Document",
        "subtitle": "Complete System Overview",
        "file": "AlphaChart_v3_4.md",
        "tag": "REFERENCE",
        "tag_color": "#555",
        "icon": "📄",
        "domain": "Reference",
    },
]

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Base */
    .main { background: #0d1117; }
    .block-container { padding: 2rem 2.5rem 4rem 2.5rem; max-width: 1000px; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #111827; }
    section[data-testid="stSidebar"] .block-container { padding: 1.2rem 1rem; }

    /* Typography */
    h1, h2, h3, h4 { color: #e6edf3 !important; letter-spacing: -0.02em; }
    p, li          { color: #c9d1d9; line-height: 1.75; }
    code           { background: #161b22 !important; color: #79c0ff !important;
                     padding: 2px 6px; border-radius: 4px; font-size: 0.875em; }
    pre code       { background: transparent !important; color: #c9d1d9 !important;
                     padding: 0; }
    pre            { background: #161b22 !important; border: 1px solid #21262d;
                     border-radius: 8px; padding: 1.2rem !important;
                     overflow-x: auto; }

    /* Tables */
    table          { border-collapse: collapse; width: 100%; margin: 1rem 0; }
    th             { background: #161b22; color: #e6edf3; padding: 8px 12px;
                     text-align: left; border: 1px solid #21262d;
                     font-size: 0.85em; font-weight: 600; letter-spacing: 0.04em;
                     text-transform: uppercase; }
    td             { padding: 8px 12px; border: 1px solid #21262d;
                     color: #c9d1d9; font-size: 0.9em; }
    tr:nth-child(even) td { background: #0d1117; }
    tr:nth-child(odd)  td { background: #111827; }

    /* Blockquotes */
    blockquote     { border-left: 3px solid #f0a500; margin: 1rem 0;
                     padding: 0.8rem 1.2rem; background: #1c1a13;
                     border-radius: 0 6px 6px 0; }
    blockquote p   { color: #e3c07a; margin: 0; }

    /* Document card (sidebar) */
    .doc-card      { border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;
                     cursor: pointer; border: 1px solid transparent;
                     transition: all 0.15s ease; }
    .doc-card:hover{ border-color: #30363d; background: #161b22; }
    .doc-card.active { border-color: #388bfd; background: #0d2044; }

    /* Tag chips */
    .tag-chip      { font-size: 10px; font-weight: 700; padding: 2px 8px;
                     border-radius: 10px; letter-spacing: 0.08em;
                     display: inline-block; margin-bottom: 4px; }

    /* Section divider */
    hr             { border-color: #21262d !important; margin: 2rem 0 !important; }

    /* Search highlight */
    mark           { background: #3d3000; color: #f0d060; padding: 1px 2px;
                     border-radius: 2px; }

    /* TOC */
    .toc-entry     { color: #8b949e; font-size: 0.85em; padding: 2px 0;
                     cursor: pointer; display: block;
                     text-decoration: none; }
    .toc-entry:hover { color: #58a6ff; }
    .toc-h2        { padding-left: 0; font-weight: 600; color: #c9d1d9; }
    .toc-h3        { padding-left: 1rem; }
    .toc-h4        { padding-left: 1.8rem; font-size: 0.8em; }

    /* Reading progress bar */
    .progress-bar  { height: 3px; background: linear-gradient(90deg, #388bfd, #58a6ff);
                     border-radius: 2px; margin-bottom: 1.5rem; }

    /* Module header banner */
    .module-banner { border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem;
                     border: 1px solid #21262d; }

    /* Stats row */
    .stat-box      { background: #161b22; border: 1px solid #21262d;
                     border-radius: 8px; padding: 10px 14px; text-align: center; }
    .stat-val      { font-size: 1.4em; font-weight: 700; color: #e6edf3;
                     display: block; }
    .stat-lbl      { font-size: 0.75em; color: #8b949e; text-transform: uppercase;
                     letter-spacing: 0.06em; }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_doc(filename: str) -> str:
    """Load markdown file content from the same directory as this script."""
    base = Path(__file__).parent
    for p in [base / filename, Path(".") / filename]:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return f"# File Not Found\n\nCould not locate `{filename}`.\n\nMake sure all AlphaChart `.md` files are in the same directory as this viewer."

def extract_toc(content: str) -> list[dict]:
    """Extract heading hierarchy from markdown."""
    toc = []
    for line in content.splitlines():
        m = re.match(r'^(#{2,4})\s+(.+)', line)
        if m:
            level = len(m.group(1))
            text  = re.sub(r'[*_`]', '', m.group(2)).strip()
            anchor = re.sub(r'[^a-z0-9-]', '', text.lower().replace(' ', '-'))
            toc.append({"level": level, "text": text, "anchor": anchor})
    return toc

def highlight_search(content: str, query: str) -> str:
    """Wrap search matches in <mark> tags."""
    if not query or len(query) < 2:
        return content
    escaped = re.escape(query)
    return re.sub(f'({escaped})', r'<mark>\1</mark>', content, flags=re.IGNORECASE)

def count_stats(content: str) -> dict:
    words    = len(content.split())
    lines    = len(content.splitlines())
    h2       = len(re.findall(r'^## ', content, re.MULTILINE))
    code_blk = len(re.findall(r'```', content)) // 2
    tables   = len(re.findall(r'^\|', content, re.MULTILINE))
    read_min = max(1, words // 200)
    return {"words": words, "sections": h2, "code_blocks": code_blk,
            "table_rows": tables, "read_min": read_min}

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "active_doc" not in st.session_state:
    st.session_state.active_doc = 0
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "font_size" not in st.session_state:
    st.session_state.font_size = 15

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem 0 1.2rem 0;">
        <div style="font-size: 1.5em; font-weight: 800; color: #e6edf3;
                    letter-spacing: -0.03em;">
            📘 AlphaChart
        </div>
        <div style="font-size: 0.75em; color: #8b949e; letter-spacing: 0.06em;
                    text-transform: uppercase;">
            v3.4 Design Manual
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Search
    search = st.text_input(
        "🔍 Search",
        value=st.session_state.search_query,
        placeholder="Search across documents…",
        label_visibility="collapsed",
    )
    st.session_state.search_query = search

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Document list
    st.markdown(
        "<div style='font-size:10px; color:#8b949e; text-transform:uppercase;"
        " letter-spacing:0.08em; margin-bottom:8px;'>Documents</div>",
        unsafe_allow_html=True
    )

    for i, doc in enumerate(DOCS):
        is_active = st.session_state.active_doc == i
        
        if st.button(
            f"{doc['icon']}  {doc['title']}",
            key=f"nav_{i}",
            use_container_width=True,
            help=doc["subtitle"],
        ):
            st.session_state.active_doc = i
            st.rerun()

        # Fixed subtitle (no backslash in f-string)
        subtitle = doc['subtitle']
        display_text = subtitle[:45] + "…" if len(subtitle) > 45 else subtitle
        st.markdown(
            f"<div style='font-size:10px; color:#8b949e; margin:-8px 0 6px 4px; "
            f"padding-left:4px;'>{display_text}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Reading options
    st.markdown(
        "<div style='font-size:10px; color:#8b949e; text-transform:uppercase;"
        " letter-spacing:0.08em; margin-bottom:6px;'>Display</div>",
        unsafe_allow_html=True
    )
    font_sz = st.slider("Font size (px)", 12, 20,
                         st.session_state.font_size, 1,
                         label_visibility="collapsed")
    st.session_state.font_size = font_sz
    st.caption(f"Font: {font_sz}px")

    # Apply font size
    st.markdown(f"""
    <style>
        .block-container p, .block-container li,
        .block-container td {{ font-size: {font_sz}px; }}
        .block-container code {{ font-size: {font_sz - 2}px; }}
    </style>
    """, unsafe_allow_html=True)

# ─── MAIN CONTENT ──────────────────────────────────────────────────────────────
doc      = DOCS[st.session_state.active_doc]
content  = load_doc(doc["file"])
stats    = count_stats(content)
toc      = extract_toc(content)
query    = st.session_state.search_query

# ── Header Banner ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background: linear-gradient(135deg, #111827 0%, #0d1117 100%);
            border: 1px solid #21262d; border-radius: 10px;
            padding: 1.2rem 1.5rem; margin-bottom: 1rem;">
    <div style="display:flex; align-items:center; gap: 12px; flex-wrap:wrap;">
        <span style="font-size: 2em; line-height:1;">{doc['icon']}</span>
        <div style="flex:1;">
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                <span style="font-size: 0.7em; font-weight: 700; color: #8b949e;
                             letter-spacing: 0.1em;">{doc['id']}</span>
                <span style="background:{doc['tag_color']}22; color:{doc['tag_color']};
                             font-size:0.65em; font-weight:700; padding:2px 8px;
                             border-radius:10px; letter-spacing:0.06em;">
                    {doc['tag']}
                </span>
            </div>
            <div style="font-size: 1.3em; font-weight: 800; color: #e6edf3;
                        letter-spacing: -0.02em; margin: 2px 0 2px 0;">
                {doc['title']}
            </div>
            <div style="font-size: 0.85em; color: #8b949e;">{doc['subtitle']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Stats row ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
for col, label, value in [
    (c1, "Words",        f"{stats['words']:,}"),
    (c2, "Sections",     str(stats['sections'])),
    (c3, "Code Blocks",  str(stats['code_blocks'])),
    (c4, "Read Time",    f"~{stats['read_min']} min"),
    (c5, "Domain",       doc['domain'][:12]),
]:
    col.markdown(f"""
    <div class="stat-box">
        <span class="stat-val">{value}</span>
        <span class="stat-lbl">{label}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── Search Results Bar ──────────────────────────────────────────────────────────
if query and len(query) >= 2:
    matches = len(re.findall(re.escape(query), content, re.IGNORECASE))
    if matches > 0:
        st.success(f"🔍 **{matches}** match{'es' if matches != 1 else ''} for **\"{query}\"** in this document")
    else:
        st.warning(f"No matches for **\"{query}\"** in this document — try another term or switch documents.")

# ── Main layout: TOC + Content ─────────────────────────────────────────────────
if toc:
    col_toc, col_main = st.columns([1, 3.5])
else:
    col_main = st.container()
    col_toc  = None

# Table of Contents panel
if col_toc and toc:
    with col_toc:
        st.markdown(
            "<div style='font-size:10px; color:#8b949e; text-transform:uppercase;"
            " letter-spacing:0.08em; margin-bottom:8px; font-weight:700;'>"
            "Contents</div>",
            unsafe_allow_html=True
        )
        toc_html = ""
        for entry in toc:
            indent = {2: 0, 3: 12, 4: 22}.get(entry["level"], 0)
            size   = {2: "0.83em", 3: "0.78em", 4: "0.73em"}.get(entry["level"], "0.8em")
            weight = "600" if entry["level"] == 2 else "400"
            color  = "#c9d1d9" if entry["level"] == 2 else "#8b949e"
            text   = entry["text"][:38] + ("…" if len(entry["text"]) > 38 else "")
            toc_html += (
                f"<a href='#{entry['anchor']}' "
                f"style='display:block; padding: 3px 0 3px {indent}px; "
                f"color:{color}; font-size:{size}; font-weight:{weight}; "
                f"text-decoration:none; line-height:1.4; "
                f"border-left: 2px solid transparent; "
                f"padding-left: {indent + 8}px;'>"
                f"{text}</a>"
            )
        st.markdown(
            f"<div style='position:sticky; top:1rem; max-height:80vh;"
            f" overflow-y:auto; padding-right:4px;'>{toc_html}</div>",
            unsafe_allow_html=True
        )

# Main reading pane
with col_main:
    if query and len(query) >= 2:
        highlighted = highlight_search(content, query)
        st.markdown(highlighted, unsafe_allow_html=True)
    else:
        st.markdown(str(content), unsafe_allow_html=True)

# ── Document Navigator (bottom) ─────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='font-size:11px; color:#8b949e; text-align:center;"
    " margin-bottom:8px; letter-spacing:0.05em;'>"
    "NAVIGATE DOCUMENTS</div>",
    unsafe_allow_html=True
)
nav_cols = st.columns(len(DOCS))
for i, (col, d) in enumerate(zip(nav_cols, DOCS)):
    is_cur = i == st.session_state.active_doc
    bdr    = f"border-bottom: 2px solid {d['tag_color']}" if is_cur else "border-bottom: 2px solid transparent"
    col.markdown(
        f"<div style='text-align:center; padding:6px 2px; {bdr}; cursor:pointer;'>"
        f"<div style='font-size:1.2em;'>{d['icon']}</div>"
        f"<div style='font-size:9px; color:{'#e6edf3' if is_cur else '#8b949e'};"
        f" letter-spacing:0.04em;'>{d['id']}</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    if not is_cur and col.button("", key=f"bot_{i}", help=d["title"],
                                 use_container_width=True, label_visibility="collapsed"):
        st.session_state.active_doc = i
        st.rerun()

# Keyboard hint
st.markdown(
    "<div style='text-align:center; font-size:10px; color:#484f58; margin-top:1rem;'>"
    "AlphaChart v3.4 Design Manual · 15 Documents · 5 Files"
    "</div>",
    unsafe_allow_html=True
)