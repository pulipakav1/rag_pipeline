import os

import streamlit as st
import requests

st.set_page_config(
    page_title="RAG Intelligence",
    page_icon="⬡",
    layout="wide",
)

API_BASE = os.environ.get("RAG_API_BASE", "http://127.0.0.1:8000").rstrip("/")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg: #0c0c14;
    --surface: #13131f;
    --border: #1f1f35;
    --accent: #6366f1;
    --accent2: #8b5cf6;
    --text: #e8e8f0;
    --muted: #5a5a7a;
    --green: #22c55e;
    --red: #ef4444;
}

* { box-sizing: border-box; }

html { font-size: 20px !important; }

body, .stApp, [class*="css"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 20px !important;
}

#MainMenu, footer, header { visibility: hidden !important; }

.main .block-container {
    max-width: min(92vw, 1280px) !important;
    padding: 2rem 2.5rem 2.5rem !important;
    margin: 0 auto !important;
}

section[data-testid="stSidebar"] {
    background: #09090f !important;
    border-right: 1px solid var(--border) !important;
    min-width: 300px !important;
}
section[data-testid="stSidebar"] > div {
    padding: 1.75rem 1.35rem !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    font-size: 1.02rem !important;
    color: #b8b8d4 !important;
}
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
    font-size: 1.02rem !important;
}

.sb-head {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    color: var(--muted) !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    padding-bottom: 0.6rem !important;
    border-bottom: 1px solid var(--border) !important;
    margin: 1.4rem 0 1rem !important;
}

.stat-row { display: flex; gap: 10px; margin-bottom: 1rem; }
.stat-card {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.stat-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem !important;
    font-weight: 600;
    color: var(--accent);
    line-height: 1;
}
.stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem !important;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 4px;
}

.app-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2.5rem;
}
.hex-logo {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
    flex-shrink: 0;
}
.app-title {
    font-size: 1.85rem !important;
    font-weight: 700;
    color: var(--text);
    line-height: 1.2;
}
.app-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem !important;
    color: var(--muted);
    margin-top: 3px;
}
.status-badge {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 8px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem !important;
    font-weight: 500;
}
.dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.on  { background: var(--green); box-shadow: 0 0 10px var(--green); }
.off { background: var(--red);   box-shadow: 0 0 10px var(--red); }

.chat { display: flex; flex-direction: column; gap: 2rem; margin-bottom: 2rem; }

.user-msg { display: flex; justify-content: flex-end; }
.user-bubble {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: #fff;
    padding: 1.1rem 1.4rem;
    border-radius: 20px 20px 5px 20px;
    max-width: 65%;
    font-size: 1.05rem !important;
    line-height: 1.6;
    box-shadow: 0 8px 30px rgba(99,102,241,0.4);
}

.bot-msg { display: flex; gap: 14px; align-items: flex-start; }
.bot-hex {
    width: 38px; height: 38px; flex-shrink: 0; margin-top: 4px;
    background: var(--surface);
    clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
    border: 1px solid #2a2a50;
}
.bot-bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    color: #d8d8f0;
    padding: 1.1rem 1.4rem;
    border-radius: 5px 20px 20px 20px;
    max-width: 72%;
    font-size: 1.05rem !important;
    line-height: 1.75;
}

.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem !important;
    background: #0f0f22;
    border: 1px solid #252550;
    color: var(--accent);
    padding: 4px 12px;
    border-radius: 6px;
}

.eval {
    margin-top: 14px;
    background: #0e0e1e;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 18px;
}
.eval-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem !important;
    color: var(--muted);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.eval-row { display: flex; align-items: center; gap: 14px; margin-bottom: 10px; }
.eval-lbl { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem !important; color: #7070a0; width: 170px; flex-shrink: 0; }
.bar-bg   { flex: 1; height: 6px; background: #1a1a30; border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 3px; transition: width 1s; }
.eval-score { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem !important; width: 42px; text-align: right; flex-shrink: 0; font-weight: 600; }

.tokens {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem !important;
    color: #5c5c78;
    text-align: right;
    margin-top: 8px;
}

.empty { text-align: center; padding: 6rem 2rem; }
.empty-hex { font-size: 4rem; margin-bottom: 1.2rem; opacity: 0.2; }
.empty-text { font-family: 'JetBrains Mono', monospace; font-size: 1.15rem !important; color: #4a4a6a; }

div[data-testid="stForm"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 1rem 1.25rem !important;
    align-items: center !important;
}

.stTextInput > label { display: none !important; }

div[data-testid="stForm"] [data-baseweb="input"] {
    background: #1a1a2a !important;
    background-color: #1a1a2a !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    min-height: 3rem !important;
}
div[data-testid="stForm"] [data-baseweb="base-input"] {
    background: transparent !important;
    background-color: transparent !important;
}

div[data-testid="stForm"] .stTextInput input,
div[data-testid="stForm"] input[type="text"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    color: #e8e8f0 !important;
    -webkit-text-fill-color: #e8e8f0 !important;
    caret-color: #e8e8f0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.125rem !important;
    line-height: 1.45 !important;
    padding: 0.65rem 1rem !important;
    min-height: 2.75rem !important;
    height: auto !important;
    box-shadow: none !important;
}
div[data-testid="stForm"] .stTextInput input:focus,
div[data-testid="stForm"] input[type="text"]:focus {
    outline: none !important;
    box-shadow: none !important;
}
div[data-testid="stForm"] .stTextInput input::placeholder,
div[data-testid="stForm"] input[type="text"]::placeholder {
    color: #6b6b8a !important;
    -webkit-text-fill-color: #6b6b8a !important;
    opacity: 1 !important;
}

div[data-testid="stForm"] button,
div[data-testid="stForm"] .stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    background-image: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    padding: 0.7rem 1.75rem !important;
    min-height: 2.75rem !important;
    height: auto !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.4) !important;
    transition: opacity 0.2s, transform 0.2s !important;
    white-space: nowrap !important;
}
div[data-testid="stForm"] button:hover,
div[data-testid="stForm"] .stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
    color: #ffffff !important;
}

section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.02rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1rem !important;
    height: auto !important;
}

.stSlider { padding: 0 !important; }
.stSlider [data-baseweb="slider"] { margin-top: 0.5rem !important; }

.stToggle { margin: 0.5rem 0 !important; }

.stTextArea > label { display: none !important; }
.stTextArea textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.9rem !important;
    resize: vertical !important;
}

section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 0.8rem !important;
    height: auto !important;
}

hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.2rem 0 !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #2a2a45; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


def check_health():
    try:
        return requests.get(f"{API_BASE}/health", timeout=2).status_code == 200
    except:
        return False

def get_stats():
    try:
        r = requests.get(f"{API_BASE}/stats", timeout=3)
        return r.json() if r.ok else {}
    except:
        return {}

def query_api(q, k, ev):
    r = requests.post(f"{API_BASE}/query", json={"question": q, "top_k": k, "evaluate": ev}, timeout=60)
    r.raise_for_status(); return r.json()

def ingest_api(text, src):
    r = requests.post(f"{API_BASE}/ingest/text", json={"text": text, "source_name": src}, timeout=30)
    r.raise_for_status(); return r.json()

def sc(s):
    if s >= 0.8: return "#22c55e"
    if s >= 0.6: return "#eab308"
    if s >= 0.4: return "#f97316"
    return "#ef4444"

def eval_html(metrics, overall):
    rows = ""
    for lbl, key in [("Faithfulness","faithfulness"),("Answer Relevance","relevance"),("Retrieval Precision","retrieval_precision")]:
        s = metrics.get(key, {}).get("score", 0)
        c = sc(s)
        rows += f'<div class="eval-row"><span class="eval-lbl">{lbl}</span><div class="bar-bg"><div class="bar-fill" style="width:{int(s*100)}%;background:{c}"></div></div><span class="eval-score" style="color:{c}">{s:.2f}</span></div>'
    oc = sc(overall)
    return f'<div class="eval"><div class="eval-title">⬡ Eval Scores</div>{rows}<div style="border-top:1px solid #1a1a2e;margin-top:10px;padding-top:10px"><div class="eval-row"><span class="eval-lbl" style="color:#9090c0;font-weight:600">Overall</span><div class="bar-bg"><div class="bar-fill" style="width:{int(overall*100)}%;background:{oc}"></div></div><span class="eval-score" style="color:{oc}">{overall:.2f}</span></div></div></div>'


for k, v in [("messages",[]),("tokens",0),("queries",0)]:
    if k not in st.session_state: st.session_state[k] = v


with st.sidebar:
    st.markdown('<div class="sb-head">Configuration</div>', unsafe_allow_html=True)
    top_k    = st.slider("Top-K chunks", 1, 10, 5)
    evaluate = st.toggle("Run eval pipeline", value=False)

    st.markdown('<div class="sb-head">System Stats</div>', unsafe_allow_html=True)
    stats = get_stats()
    online = check_health()

    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-card"><div class="stat-num">{stats.get("total_chunks","—")}</div><div class="stat-label">Chunks</div></div>
      <div class="stat-card"><div class="stat-num">{st.session_state.queries}</div><div class="stat-label">Queries</div></div>
    </div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#3a3a5a;line-height:2">
    Tokens used: {st.session_state.tokens:,}<br>
    Model: {stats.get("llm_model","—").replace("claude-","")}<br>
    Embed: all-MiniLM-L6-v2
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-head">Ingest Text</div>', unsafe_allow_html=True)
    src  = st.text_input("src",  value="manual_input", placeholder="Source name",   label_visibility="collapsed")
    body = st.text_area ("body", height=100,            placeholder="Paste text...", label_visibility="collapsed")
    if st.button("⬡ Ingest", use_container_width=True):
        if body.strip():
            with st.spinner("Ingesting..."): 
                try:
                    res = ingest_api(body, src)
                    st.success(f"✓ {res['chunks_added']} chunks added")
                    st.rerun()
                except Exception as e: st.error(str(e))
        else: st.warning("Paste some text first")

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


dot = f'<div class="dot {"on" if online else "off"}"></div>'
col = "#22c55e" if online else "#ef4444"
lbl = "ONLINE" if online else "OFFLINE"

st.markdown(f"""
<div class="app-header">
  <div class="hex-logo"></div>
  <div>
    <div class="app-title">RAG Intelligence</div>
    <div class="app-sub">Retrieval-Augmented Generation · Claude + ChromaDB</div>
  </div>
  <div class="status-badge">{dot}<span style="color:{col};font-family:'JetBrains Mono',monospace;font-size:0.82rem">{lbl}</span></div>
</div>""", unsafe_allow_html=True)


if not st.session_state.messages:
    st.markdown('<div class="empty"><div class="empty-hex">⬡</div><div class="empty-text">Ask anything from your knowledge base</div></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="chat">', unsafe_allow_html=True)
    for m in st.session_state.messages:
        if m["role"] == "user":
            st.markdown(f'<div class="user-msg"><div class="user-bubble">{m["content"]}</div></div>', unsafe_allow_html=True)
        else:
            chips = "".join(f'<span class="chip">⬡ {s["source"]} · {s["relevance_score"]}</span>' for s in m.get("sources",[]))
            src_h  = f'<div class="chips">{chips}</div>' if chips else ""
            ev_h   = eval_html(m["evaluation"], m.get("overall_score",0)) if m.get("evaluation") else ""
            t      = m.get("tokens_used",{})
            tok_h  = f'<div class="tokens">↑{t.get("input",0)} ↓{t.get("output",0)} tokens</div>' if t else ""
            st.markdown(f'<div class="bot-msg"><div class="bot-hex"></div><div><div class="bot-bubble">{m["content"]}</div>{src_h}{ev_h}{tok_h}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

with st.form("f", clear_on_submit=True):
    c1, c2 = st.columns([5,1])
    with c1: q = st.text_input("q", placeholder="Ask a question from your knowledge base...", label_visibility="collapsed")
    with c2: go = st.form_submit_button("Send ➜", use_container_width=True)

if go and q.strip():
    if not online:
        st.error(f"API offline — run: uvicorn src.api.main:app --reload --host 127.0.0.1 --port … (must match {API_BASE})")
    else:
        st.session_state.messages.append({"role":"user","content":q})
        with st.spinner("Thinking..."):
            try:
                res = query_api(q, top_k, evaluate)
                msg = {"role":"assistant","content":res["answer"],"sources":res.get("sources",[]),"tokens_used":res.get("tokens_used",{})}
                if evaluate and "evaluation" in res:
                    msg["evaluation"] = res["evaluation"]
                    msg["overall_score"] = res.get("overall_score",0)
                st.session_state.messages.append(msg)
                st.session_state.queries += 1
                st.session_state.tokens  += res.get("tokens_used",{}).get("input",0) + res.get("tokens_used",{}).get("output",0)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")