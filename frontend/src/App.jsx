import { useState, useEffect, useRef, useCallback } from "react";

const API_BASE = "http://localhost:8000";

const EVENT_CONFIG = {
  user_input:        { label: "input",    color: "#6366f1" },
  thinking:          { label: "thinking", color: "#8b5cf6" },
  tool_call:         { label: "tool",     color: "#0ea5e9" },
  tool_result:       { label: "result",   color: "#10b981" },
  final_answer:      { label: "answer",   color: "#22c55e" },
  guardrail_blocked: { label: "blocked",  color: "#ef4444" },
  error:             { label: "error",    color: "#f97316" },
};

const css = `
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@400;500;600;700&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:      #0a0a0f;
    --bg2:     #111118;
    --bg3:     #18181f;
    --bg4:     #1f1f28;
    --border:  rgba(255,255,255,0.07);
    --border2: rgba(255,255,255,0.13);
    --text:    #e8e8f0;
    --muted:   #6b6b80;
    --accent:  #7c6af7;
    --accent2: #5b4de0;
    --green:   #22c55e;
    --red:     #ef4444;
    --orange:  #f97316;
    --blue:    #0ea5e9;
    --font-ui:   'Syne', sans-serif;
    --font-code: 'JetBrains Mono', monospace;
  }
  body { background: var(--bg); color: var(--text); font-family: var(--font-ui); }

  /* ── Layout ── */
  .app { display: flex; height: 100vh; overflow: hidden; }
  .sidebar {
    width: 210px; flex-shrink: 0;
    background: var(--bg2); border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
  }
  .sidebar-logo {
    padding: 18px 16px 14px;
    border-bottom: 1px solid var(--border);
    font-size: 12px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase;
    color: var(--accent); display: flex; align-items: center; gap: 8px;
  }
  .logo-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 8px var(--accent);
    animation: blink 2s ease-in-out infinite;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
  .sidebar-section { padding: 14px 16px 5px; font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
  .sidebar-item {
    padding: 8px 16px; font-size: 13px; font-weight: 500;
    color: var(--muted); cursor: pointer;
    border-left: 2px solid transparent;
    display: flex; align-items: center; gap: 8px;
    transition: all .15s;
  }
  .sidebar-item:hover { color: var(--text); background: rgba(255,255,255,0.03); }
  .sidebar-item.active { color: var(--text); border-left-color: var(--accent); background: rgba(124,106,247,0.08); }
  .sidebar-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; opacity: .5; flex-shrink: 0; }
  .sidebar-new {
    margin: 8px 12px;
    padding: 8px; border-radius: 8px;
    background: rgba(124,106,247,0.12); border: 1px solid rgba(124,106,247,0.28);
    color: var(--accent); font-family: var(--font-ui); font-size: 12px; font-weight: 700;
    cursor: pointer; letter-spacing: .05em; transition: all .15s;
  }
  .sidebar-new:hover { background: rgba(124,106,247,0.22); }

  .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  .topbar {
    height: 50px; flex-shrink: 0;
    background: var(--bg2); border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 22px;
  }
  .topbar-left { display: flex; align-items: center; gap: 10px; }
  .topbar-title { font-size: 14px; font-weight: 700; }
  .topbar-id { font-size: 11px; color: var(--muted); font-family: var(--font-code); }
  .topbar-tabs { display: flex; gap: 6px; }
  .tab {
    padding: 5px 13px; border-radius: 6px; font-family: var(--font-ui);
    font-size: 12px; font-weight: 600; cursor: pointer; letter-spacing: .04em;
    border: 1px solid var(--border2); background: transparent; color: var(--muted);
    transition: all .15s;
  }
  .tab:hover { color: var(--text); }
  .tab.active { background: var(--accent); border-color: var(--accent); color: #fff; }
  .view { flex: 1; overflow: hidden; display: flex; }

  /* ── Buttons ── */
  .btn {
    padding: 7px 16px; border-radius: 7px; font-family: var(--font-ui);
    font-size: 12px; font-weight: 700; cursor: pointer; letter-spacing: .05em;
    border: 1px solid var(--border2); background: transparent; color: var(--muted);
    transition: all .15s;
  }
  .btn:hover { color: var(--text); border-color: var(--border2); }
  .btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
  .btn-primary:hover { background: var(--accent2); }
  .btn:disabled { opacity: .4; cursor: not-allowed; }

  /* ── Builder ── */
  .builder { flex: 1; overflow-y: auto; padding: 26px 30px; }
  .builder::-webkit-scrollbar { width: 4px; }
  .builder::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }
  .section-label {
    font-size: 10px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 10px; margin-top: 22px;
  }
  .section-label:first-child { margin-top: 0; }
  .field { display: flex; flex-direction: column; gap: 5px; margin-bottom: 14px; }
  .field-label { font-size: 11px; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; color: var(--muted); }
  .field-input, .field-textarea {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 8px; padding: 9px 12px;
    color: var(--text); font-family: var(--font-ui); font-size: 13px;
    outline: none; transition: border-color .15s;
  }
  .field-textarea { font-family: var(--font-code); font-size: 12px; resize: vertical; min-height: 90px; line-height: 1.6; }
  .field-input:focus, .field-textarea:focus { border-color: var(--accent); }

  /* Calculator chip — read-only, always on */
  .tool-chip-only {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 7px 14px; border-radius: 7px; font-size: 13px; font-weight: 600;
    background: rgba(124,106,247,0.12); border: 1px solid rgba(124,106,247,0.35);
    color: var(--accent);
  }
  .tool-chip-lock { font-size: 11px; color: var(--muted); margin-left: 4px; }

  /* Model chip — read-only */
  .model-chip {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 7px 14px; border-radius: 7px; font-size: 13px; font-weight: 600;
    background: var(--bg3); border: 1px solid var(--border2);
    color: var(--text); font-family: var(--font-code);
  }

  /* Max steps — single input */
  .steps-row { display: flex; align-items: center; gap: 12px; }
  .steps-input {
    width: 72px; background: var(--bg3); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 10px; text-align: center;
    color: var(--text); font-family: var(--font-code); font-size: 16px; font-weight: 700;
    outline: none; transition: border-color .15s;
  }
  .steps-input:focus { border-color: var(--accent); }
  .steps-hint { font-size: 12px; color: var(--muted); }

  /* Forbidden topics */
  .topics-input {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 8px; padding: 9px 12px; width: 100%;
    color: var(--text); font-family: var(--font-ui); font-size: 13px;
    outline: none; transition: border-color .15s;
  }
  .topics-input:focus { border-color: var(--accent); }
  .topics-hint { font-size: 11px; color: var(--muted); margin-top: 5px; }
  .topic-pills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .topic-pill {
    display: flex; align-items: center; gap: 5px;
    padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600;
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25);
    color: var(--red);
  }
  .topic-pill-x { cursor: pointer; opacity: .6; transition: opacity .15s; font-size: 12px; background: none; border: none; color: var(--red); padding: 0; line-height: 1; }
  .topic-pill-x:hover { opacity: 1; }

  .save-row { display: flex; justify-content: flex-end; padding-top: 20px; border-top: 1px solid var(--border); margin-top: 22px; }

  /* ── Tracker ── */
  .tracker { flex: 1; display: flex; overflow: hidden; }
  .tracker-log-col { flex: 1; display: flex; flex-direction: column; border-right: 1px solid var(--border); overflow: hidden; }
  .tracker-chat-col { width: 290px; flex-shrink: 0; display: flex; flex-direction: column; overflow: hidden; }
  .panel-head {
    height: 42px; flex-shrink: 0; padding: 0 16px;
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid var(--border);
    font-size: 10px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted);
  }
  .run-badge {
    font-size: 10px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
    padding: 2px 8px; border-radius: 4px;
  }
  .s-running   { background: rgba(14,165,233,.15); color: var(--blue); }
  .s-completed { background: rgba(34,197,94,.15);  color: var(--green); }
  .s-blocked   { background: rgba(239,68,68,.15);  color: var(--red); }
  .s-error, .s-max_steps_reached { background: rgba(249,115,22,.15); color: var(--orange); }

  .events-list { flex: 1; overflow-y: auto; padding: 14px 16px; }
  .events-list::-webkit-scrollbar { width: 3px; }
  .events-list::-webkit-scrollbar-thumb { background: var(--border2); }
  .ev-item { display: flex; gap: 10px; margin-bottom: 12px; }
  .ev-step {
    flex-shrink: 0; width: 20px; height: 20px; border-radius: 50%;
    background: var(--bg4); display: flex; align-items: center; justify-content: center;
    font-family: var(--font-code); font-size: 9px; font-weight: 700; color: var(--muted);
    margin-top: 2px;
  }
  .ev-body { flex: 1; min-width: 0; }
  .ev-tag {
    display: inline-block; font-size: 10px; font-weight: 700;
    letter-spacing: .07em; text-transform: uppercase;
    padding: 2px 7px; border-radius: 4px; margin-bottom: 4px;
  }
  .ev-title { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
  .ev-payload {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 6px; padding: 7px 10px;
    font-family: var(--font-code); font-size: 11px;
    color: var(--text); line-height: 1.5;
    white-space: pre-wrap; word-break: break-word;
    max-height: 140px; overflow-y: auto;
  }

  .chat-msgs { flex: 1; overflow-y: auto; padding: 12px 14px; display: flex; flex-direction: column; gap: 9px; }
  .chat-msgs::-webkit-scrollbar { width: 3px; }
  .chat-msgs::-webkit-scrollbar-thumb { background: var(--border2); }
  .bubble {
    max-width: 92%; padding: 8px 11px;
    font-size: 12px; line-height: 1.55; border-radius: 10px;
  }
  .bubble.user { align-self: flex-end; background: rgba(124,106,247,.2); border: 1px solid rgba(124,106,247,.3); border-radius: 10px 10px 2px 10px; }
  .bubble.bot  { align-self: flex-start; background: var(--bg3); border: 1px solid var(--border); border-radius: 2px 10px 10px 10px; }
  .bubble.blocked { align-self: flex-start; background: rgba(239,68,68,.08); border: 1px solid rgba(239,68,68,.2); color: var(--red); font-size: 11px; border-radius: 2px 10px 10px 10px; }

  .chat-input-area { border-top: 1px solid var(--border); padding: 10px 12px; display: flex; flex-direction: column; gap: 7px; }
  .chat-textarea {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 11px;
    color: var(--text); font-family: var(--font-ui); font-size: 12px;
    resize: none; outline: none; line-height: 1.5; transition: border-color .15s;
  }
  .chat-textarea:focus { border-color: var(--accent); }
  .send-btn {
    align-self: flex-end; padding: 6px 16px; border-radius: 7px;
    background: var(--accent); border: none; color: #fff;
    font-family: var(--font-ui); font-size: 12px; font-weight: 700;
    cursor: pointer; transition: background .15s;
  }
  .send-btn:hover { background: var(--accent2); }
  .send-btn:disabled { opacity: .4; cursor: not-allowed; }

  /* ── Deploy ── */
  .deploy { flex: 1; overflow-y: auto; padding: 26px 30px; }
  .deploy::-webkit-scrollbar { width: 4px; }
  .deploy::-webkit-scrollbar-thumb { background: var(--border2); }
  .deploy-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 10px; }
  .d-card { background: var(--bg3); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
  .d-card-title { font-size: 13px; font-weight: 700; margin-bottom: 3px; }
  .d-card-sub { font-size: 11px; color: var(--muted); margin-bottom: 11px; }
  .code-block {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 7px; padding: 9px 11px;
    font-family: var(--font-code); font-size: 11px;
    color: #a5b4fc; line-height: 1.7; white-space: pre;
  }
  .copy-row { display: flex; align-items: center; justify-content: space-between; margin-top: 7px; }
  .copy-btn { font-size: 11px; font-weight: 700; color: var(--accent); background: none; border: none; cursor: pointer; font-family: var(--font-ui); padding: 0; transition: color .15s; }
  .copy-btn:hover { color: #fff; }

  /* ── Misc ── */
  .spinner {
    display: inline-block; width: 13px; height: 13px; border-radius: 50%;
    border: 2px solid var(--border2); border-top-color: var(--accent);
    animation: spin .7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: var(--muted); font-size: 13px; }
  .empty-ico { font-size: 26px; opacity: .25; }
  .toast { position: fixed; bottom: 22px; right: 22px; background: var(--bg3); border: 1px solid var(--border2); border-radius: 8px; padding: 9px 15px; font-size: 12px; font-weight: 500; z-index: 99; animation: slide-up .2s ease; }
  @keyframes slide-up { from { transform: translateY(8px); opacity:0; } to { transform: none; opacity:1; } }
`;

// ─── Toast ─────────────────────────────────────────────────────────────────────
function Toast({ msg, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 1800); return () => clearTimeout(t); }, [onDone]);
  return <div className="toast">{msg}</div>;
}

function copyText(text, setToast) {
  navigator.clipboard.writeText(text).then(() => setToast("Copied!"));
}

function fmtPayload(raw) {
  if (!raw) return null;
  try { return JSON.stringify(JSON.parse(raw), null, 2); } catch { return raw; }
}

// ─── Builder ───────────────────────────────────────────────────────────────────
function BuilderView({ agent, onSaved, setToast }) {
  const isNew = !agent;
  const [name, setName] = useState(agent?.name ?? "");
  const [prompt, setPrompt] = useState(agent?.system_prompt ?? "You are a helpful assistant.");
  const [maxSteps, setMaxSteps] = useState(agent?.max_steps ?? 5);
  const [topicInput, setTopicInput] = useState("");
  const [topics, setTopics] = useState(agent?.forbidden_topics ?? []);
  const [saving, setSaving] = useState(false);

  const [availableTools, setAvailableTools] = useState([]);
  const [selectedTools, setSelectedTools] = useState(agent?.allowed_tools ?? []);
  const [toolsLoading, setToolsLoading] = useState(true);

  useEffect(() => {
    const fetchTools = async () => {
      const res = await fetch(`${API_BASE}/tools`);
      if (!res.ok) throw new Error(await res.text());
      const tools = await res.json();
      setAvailableTools(tools);
      // Ensure selected tools exist in available tools
      setSelectedTools(prev => 
        prev.filter(tool => tools.some(t => t.tool_name === tool))
      );

      setToolsLoading(false);
    };
    fetchTools();
  }, []);

  const addTopic = () => {
    const t = topicInput.trim();
    if (t && !topics.includes(t)) setTopics(ts => [...ts, t]);
    setTopicInput("");
  };

  const removeTopic = (t) => setTopics(ts => ts.filter(x => x !== t));

  const handleSave = async () => {
    if (!name.trim()) { setToast("Name is required"); return; }
    setSaving(true);
    const body = {
      name,
      system_prompt: prompt,
      model_provider: "gemini",
      model_name: "gemini-2.5-flash",
      allowed_tools: selectedTools,
      max_steps: maxSteps,
      forbidden_topics: topics,
    };
    try {
      const res = await fetch(
        isNew ? `${API_BASE}/agents` : `${API_BASE}/agents/${agent.id}`,
        { method: isNew ? "POST" : "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
      );
      if (!res.ok) throw new Error(await res.text());
      const saved = await res.json();
      setToast(isNew ? "Agent created!" : "Saved!");
      onSaved(saved);
    } catch (e) { setToast("Error: " + e.message); }
    finally { setSaving(false); }
  };

  return (
    <div className="builder">
      <div className="section-label">Identity</div>

      <div className="field">
        <label className="field-label">Agent name</label>
        <input className="field-input" value={name} onChange={e => setName(e.target.value)} placeholder="My calculator bot" />
      </div>

      <div className="field">
        <label className="field-label">System prompt</label>
        <textarea className="field-textarea" rows={4} value={prompt} onChange={e => setPrompt(e.target.value)} />
      </div>

      <div className="section-label">Model</div>
      <div className="model-chip">gemini-2.5-flash</div>

      <div className="section-label" style={{ marginTop: 18 }}>Tools</div>
      {toolsLoading ? (
        <div style={{ padding: "8px 0" }}>
          <span className="spinner" /> Loading tools...
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {availableTools.map(tool => {
            const isSelected = selectedTools.includes(tool.tool_name);
            return (
              <label 
                key={tool.tool_name}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "8px 12px",
                  background: "var(--bg3)",
                  border: `1px solid ${isSelected ? "var(--accent)" : "var(--border)"}`,
                  borderRadius: 8,
                  cursor: "pointer",
                  fontSize: 13,
                  fontWeight: 500,
                  transition: "border-color .15s"
                }}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {
                    setSelectedTools(prev =>
                      isSelected
                        ? prev.filter(t => t !== tool.tool_name)
                        : [...prev, tool.tool_name]
                    );
                  }}
                />
                ⊞ {tool.tool_name}
              </label>
            );
          })}
          {availableTools.length === 0 && (
            <div style={{ color: "var(--muted)", fontSize: 12, padding: "8px 0" }}>
              No tools available
            </div>
          )}
        </div>
      )}

      <div className="section-label" style={{ marginTop: 18 }}>Guardrails</div>

      <div className="field">
        <label className="field-label">Max steps</label>
        <div className="steps-row">
          <input
            type="number" className="steps-input"
            min={1} max={20} value={maxSteps}
            onChange={e => setMaxSteps(Math.max(1, Math.min(20, +e.target.value)))}
          />
          <span className="steps-hint">max iterations the agent can take per run</span>
        </div>
      </div>

      <div className="field">
        <label className="field-label">Forbidden topics</label>
        <div style={{ display: "flex", gap: 7 }}>
          <input
            className="topics-input"
            value={topicInput}
            onChange={e => setTopicInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); addTopic(); } }}
            placeholder="Type topic and press Enter"
          />
          <button className="btn" onClick={addTopic} style={{ flexShrink: 0 }}>Add</button>
        </div>
        {topics.length > 0 && (
          <div className="topic-pills">
            {topics.map(t => (
              <span className="topic-pill" key={t}>
                {t}
                <button className="topic-pill-x" onClick={() => removeTopic(t)}>×</button>
              </span>
            ))}
          </div>
        )}
        <div className="topics-hint">Agent will refuse requests containing these words/phrases</div>
      </div>

      <div className="save-row">
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <span className="spinner" /> : isNew ? "Create agent" : "Save changes"}
        </button>
      </div>
    </div>
  );
}

// ─── Tracker ──────────────────────────────────────────────────────────────────
function TrackerView({ agent, setToast }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [run, setRun] = useState(null);
  const [events, setEvents] = useState([]);
  const [chat, setChat] = useState([]);
  const logEndRef = useRef(null);

  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [events]);

  const handleRun = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setLoading(true);
    setEvents([]);
    setRun(null);
    setChat(h => [...h, { role: "user", text: msg }]);

    try {
      const res = await fetch(`${API_BASE}/agents/${agent.id}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: msg }),
      });
      if (!res.ok) throw new Error(await res.text());
      const runData = await res.json();
      setRun(runData);

      const evRes = await fetch(`${API_BASE}/runs/${runData.id}/events`);
      const evData = await evRes.json();
      setEvents(evData);

      setChat(h => [...h, {
        role: "bot",
        text: runData.final_answer || "No answer returned.",
        blocked: runData.status === "blocked",
      }]);
    } catch (e) {
      setToast("Failed: " + e.message);
      setChat(h => [...h, { role: "bot", text: "Error: " + e.message }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="tracker">
      {/* Log column */}
      <div className="tracker-log-col">
        <div className="panel-head">
          <span>Execution log</span>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {run && <span className={`run-badge s-${run.status}`}>{run.status}</span>}
            {loading && <span className="spinner" />}
          </div>
        </div>
        <div className="events-list">
          {events.length === 0 && !loading && (
            <div className="empty"><div className="empty-ico">◎</div><span>Send a message to run the agent</span></div>
          )}
          {events.map(ev => {
            const cfg = EVENT_CONFIG[ev.type] || { label: ev.type, color: "#888" };
            const payload = fmtPayload(ev.payload);
            return (
              <div className="ev-item" key={ev.id}>
                <div className="ev-step">{ev.step}</div>
                <div className="ev-body">
                  <span className="ev-tag" style={{ background: cfg.color + "22", color: cfg.color }}>{cfg.label}</span>
                  <div className="ev-title">{ev.title}</div>
                  {payload && <div className="ev-payload">{payload}</div>}
                </div>
              </div>
            );
          })}
          <div ref={logEndRef} />
        </div>
      </div>

      {/* Chat column */}
      <div className="tracker-chat-col">
        <div className="panel-head">Chat</div>
        <div className="chat-msgs">
          {chat.length === 0 && <div className="empty"><div className="empty-ico">✦</div><span>Ask anything</span></div>}
          {chat.map((m, i) => (
            <div key={i} className={`bubble ${m.role === "user" ? "user" : m.blocked ? "blocked" : "bot"}`}>
              {m.text}
            </div>
          ))}
          {loading && <div className="bubble bot"><span className="spinner" /></div>}
        </div>
        <div className="chat-input-area">
          <textarea
            className="chat-textarea" rows={2}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleRun(); } }}
            placeholder={`Ask ${agent.name}…`}
          />
          <button className="send-btn" onClick={handleRun} disabled={loading || !input.trim()}>
            {loading ? <span className="spinner" style={{ borderTopColor: "#fff", width: 11, height: 11 }} /> : "Run ↗"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Deploy ───────────────────────────────────────────────────────────────────
function DeployView({ agent, setToast }) {
  const runUrl = `${API_BASE}/agents/${agent.id}/runs`;
  const eventsUrl = `${API_BASE}/runs/{run_id}/events`;
  const curlSnippet = `curl -X POST ${runUrl} \\\n  -H "Content-Type: application/json" \\\n  -d '{"user_input": "what is 42 * 7"}'`;
  const jsSnippet = `const res = await fetch("${runUrl}", {\n  method: "POST",\n  headers: { "Content-Type": "application/json" },\n  body: JSON.stringify({ user_input: "2 + 2" }),\n});\nconst run = await res.json();\nconsole.log(run.final_answer);`;
  const iframeSnippet = `<iframe\n  src="${API_BASE}/embed/${agent.id}"\n  width="420"\n  height="640">\n</iframe>`;
  const widgetSnippet = `<script\n  src="${API_BASE}/widget.js"\n  data-agent="${agent.id}">\n</script>`;

  return (
    <div className="deploy">
      <div className="section-label">Integration</div>
      <div className="deploy-grid">
        <div className="d-card">
          <div className="d-card-title">cURL</div>
          <div className="d-card-sub">Test from terminal</div>
          <div className="code-block">{curlSnippet}</div>
          <div className="copy-row">
            <button className="copy-btn" onClick={() => copyText(curlSnippet, setToast)}>Copy</button>
          </div>
        </div>

        <div className="d-card">
          <div className="d-card-title">JavaScript fetch</div>
          <div className="d-card-sub">Call from any frontend</div>
          <div className="code-block">{jsSnippet}</div>
          <div className="copy-row">
            <button className="copy-btn" onClick={() => copyText(jsSnippet, setToast)}>Copy</button>
          </div>
        </div>

        <div className="d-card">
          <div className="d-card-title">JS Widget</div>
          <div className="d-card-sub">One-line embed</div>
          <div className="code-block">{widgetSnippet}</div>
          <div className="copy-row">
            <button className="copy-btn" onClick={() => copyText(widgetSnippet, setToast)}>Copy</button>
          </div>
        </div>

        <div className="d-card" style={{ border: "1px solid rgba(124,106,247,0.35)" }}>
          <div className="d-card-title">iFrame</div>
          <div className="d-card-sub">Full chat UI on your page</div>
          <div className="code-block">{iframeSnippet}</div>
          <div className="copy-row">
            <button className="copy-btn" onClick={() => copyText(iframeSnippet, setToast)}>Copy</button>
            <span style={{ fontSize: 10, background: "rgba(34,197,94,.12)", color: "var(--green)", borderRadius: 4, padding: "2px 7px", fontWeight: 700 }}>recommended</span>
          </div>
        </div>
      </div>

      <div className="section-label" style={{ marginTop: 24 }}>Endpoints</div>
      <div className="d-card" style={{ marginTop: 0 }}>
        <div className="code-block">{`POST ${runUrl}\nGET  ${eventsUrl}`}</div>
      </div>
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [agents, setAgents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [view, setView] = useState("builder");
  const [creatingNew, setCreatingNew] = useState(false);
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/agents`);
      const data = await res.json();
      setAgents(data);
      if (data.length > 0 && !selectedId) { setSelectedId(data[0].id); setView("tracker"); }
    } catch { /* backend not running */ }
    finally { setLoading(false); }
  }, [selectedId]);

  useEffect(() => { fetchAgents(); }, []);

  const selected = agents.find(a => a.id === selectedId) || null;

  const handleSaved = (a) => {
    if (!a) { setCreatingNew(false); return; }
    fetchAgents();
    setSelectedId(a.id);
    setCreatingNew(false);
    setView("tracker");
  };

  const handleSelect = (id) => { setSelectedId(id); setCreatingNew(false); setView("tracker"); };
  const handleNew = () => { setCreatingNew(true); setSelectedId(null); setView("builder"); };

  const showBuilder = creatingNew || (!creatingNew && selected && view === "builder");
  const showTracker = !creatingNew && selected && view === "tracker";
  const showDeploy  = !creatingNew && selected && view === "deploy";

  return (
    <>
      <style>{css}</style>
      <div className="app">
        <div className="sidebar">
          <div className="sidebar-logo"><div className="logo-dot" /> Agentic Studio</div>
          <div className="sidebar-section">Agents</div>
          {loading && <div style={{ padding: "12px 16px" }}><span className="spinner" /></div>}
          {agents.map(a => (
            <div key={a.id} className={`sidebar-item ${selectedId === a.id && !creatingNew ? "active" : ""}`} onClick={() => handleSelect(a.id)}>
              <div className="sidebar-dot" />{a.name}
            </div>
          ))}
          <button className="sidebar-new" onClick={handleNew}>+ New agent</button>
        </div>

        <div className="main">
          <div className="topbar">
            <div className="topbar-left">
              <span className="topbar-title">{creatingNew ? "New agent" : selected?.name || "Agentic Studio"}</span>
              {selected && !creatingNew && <span className="topbar-id">#{selected.id}</span>}
            </div>
            {selected && !creatingNew && (
              <div className="topbar-tabs">
                <button className={`tab ${view === "builder" ? "active" : ""}`} onClick={() => setView("builder")}>Builder</button>
                <button className={`tab ${view === "tracker" ? "active" : ""}`} onClick={() => setView("tracker")}>Tracker</button>
                <button className={`tab ${view === "deploy"  ? "active" : ""}`} onClick={() => setView("deploy")}>Deploy</button>
              </div>
            )}
          </div>

          <div className="view">
            {creatingNew && <BuilderView agent={null} onSaved={handleSaved} setToast={setToast} />}
            {!creatingNew && !selected && !loading && (
              <div className="empty">
                <div className="empty-ico">◎</div>
                <span>No agents yet</span>
                <button className="btn btn-primary" onClick={handleNew}>Create first agent</button>
              </div>
            )}
            {showBuilder && !creatingNew && <BuilderView agent={selected} onSaved={handleSaved} setToast={setToast} />}
            {showTracker && <TrackerView agent={selected} setToast={setToast} />}
            {showDeploy  && <DeployView  agent={selected} setToast={setToast} />}
          </div>
        </div>
      </div>
      {toast && <Toast msg={toast} onDone={() => setToast(null)} />}
    </>
  );
}
