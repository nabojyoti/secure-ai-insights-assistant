import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart3,
  Bot,
  CheckCircle2,
  Database,
  FileText,
  History,
  Loader2,
  MessageSquare,
  Play,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import {
  askQuestion,
  getAudienceSegments,
  getStrongestCity,
  getTopTitles,
  getWeakGenres,
  issueToken,
  seedData,
} from "./api";
import "./styles.css";

const SAMPLE_QUESTIONS = [
  "Which titles performed best in 2025?",
  "Why is Stellar Run trending recently?",
  "Compare Dark Orbit vs Last Kingdom.",
  "Which city had the strongest engagement last month?",
  "What explains weak comedy performance?",
  "What recommendations would you give for leadership?",
];

function App() {
  const [token, setToken] = useState("");
  const [query, setQuery] = useState(SAMPLE_QUESTIONS[0]);
  const [year, setYear] = useState("2025");
  const [month, setMonth] = useState("2026-04");
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [topTitles, setTopTitles] = useState([]);
  const [strongestCity, setStrongestCity] = useState(null);
  const [weakGenres, setWeakGenres] = useState([]);
  const [segments, setSegments] = useState([]);
  const [selectedResponse, setSelectedResponse] = useState(null);
  const [status, setStatus] = useState("Disconnected");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const latestTrace = selectedResponse?.trace || messages.at(-1)?.response?.trace;
  const latestSources = selectedResponse?.sources || messages.at(-1)?.response?.sources || [];
  const latestGuardrails = selectedResponse?.guardrails || messages.at(-1)?.response?.guardrails;

  useEffect(() => {
    bootstrap();
  }, []);

  async function bootstrap() {
    setLoading(true);
    setError("");
    try {
      setStatus("Connecting");
      const issued = await issueToken();
      setToken(issued.access_token);
      setStatus("Token ready");
      await seedData(issued.access_token);
      setStatus("Demo data loaded");
      await refreshInsights(issued.access_token);
      setStatus("Ready");
    } catch (err) {
      setError(err.message);
      setStatus("Needs attention");
    } finally {
      setLoading(false);
    }
  }

  async function refreshInsights(activeToken = token) {
    if (!activeToken) return;
    const [titles, city, genres, audience] = await Promise.all([
      getTopTitles(activeToken, year, 5),
      getStrongestCity(activeToken, month),
      getWeakGenres(activeToken),
      getAudienceSegments(activeToken),
    ]);
    setTopTitles(titles);
    setStrongestCity(city);
    setWeakGenres(genres);
    setSegments(audience);
  }

  async function submitQuestion(nextQuery = query) {
    const cleanQuery = nextQuery.trim();
    if (!cleanQuery || !token) return;

    setLoading(true);
    setError("");
    setQuery("");
    setMessages((items) => [...items, { role: "user", content: cleanQuery }]);
    try {
      const response = await askQuestion(token, cleanQuery);
      const assistantMessage = {
        role: "assistant",
        content: response.answer,
        response,
      };
      setMessages((items) => [...items, assistantMessage]);
      setSelectedResponse(response);
      setHistory((items) => [
        {
          query: cleanQuery,
          answer: response.answer,
          tools: response.trace?.tools_used || [],
          at: new Date().toLocaleTimeString(),
          response,
        },
        ...items.slice(0, 7),
      ]);
    } catch (err) {
      setError(err.message);
      setMessages((items) => [...items, { role: "assistant", content: err.message, tone: "error" }]);
    } finally {
      setLoading(false);
    }
  }

  const revenueMax = useMemo(
    () => Math.max(...topTitles.map((item) => Number(item.revenue) || 0), 1),
    [topTitles],
  );

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Secure AI Insights Assistant</p>
          <h1>Internal entertainment analytics</h1>
        </div>
        <div className="status-strip">
          <StatusBadge icon={ShieldCheck} label={latestGuardrails?.output === "passed" ? "Guarded" : "Guardrails"} />
          <StatusBadge icon={Database} label={status} />
          <button className="icon-button" type="button" onClick={bootstrap} title="Reconnect and seed data">
            {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
          </button>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="filter-band">
        <label>
          <span>Year</span>
          <select value={year} onChange={(event) => setYear(event.target.value)}>
            <option value="2025">2025</option>
            <option value="2024">2024</option>
          </select>
        </label>
        <label>
          <span>Month</span>
          <select value={month} onChange={(event) => setMonth(event.target.value)}>
            <option value="2026-04">2026-04</option>
          </select>
        </label>
        <button className="secondary-button" type="button" onClick={() => refreshInsights()} disabled={!token || loading}>
          <SlidersHorizontal size={16} />
          Apply filters
        </button>
        <button className="primary-button" type="button" onClick={() => submitQuestion()} disabled={!token || loading}>
          <Play size={16} />
          Run selected question
        </button>
      </section>

      <section className="workspace">
        <section className="chat-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Chat</p>
              <h2>Ask business questions</h2>
            </div>
            <MessageSquare size={20} />
          </div>

          <div className="question-grid">
            {SAMPLE_QUESTIONS.map((sample) => (
              <button
                key={sample}
                type="button"
                className={query === sample ? "question-chip active" : "question-chip"}
                onClick={() => setQuery(sample)}
              >
                {sample}
              </button>
            ))}
          </div>

          <div className="messages">
            {messages.length === 0 ? (
              <div className="empty-state">
                <Bot size={24} />
                <p>Use the sample questions or type your own entertainment analytics query.</p>
              </div>
            ) : (
              messages.map((message, index) => (
                <article key={`${message.role}-${index}`} className={`message ${message.role} ${message.tone || ""}`}>
                  <span>{message.role === "user" ? "You" : "Assistant"}</span>
                  <p>{message.content}</p>
                </article>
              ))
            )}
          </div>

          <form
            className="composer"
            onSubmit={(event) => {
              event.preventDefault();
              submitQuestion();
            }}
          >
            <Search size={18} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} />
            <button className="send-button" type="submit" disabled={!token || loading} title="Send question">
              {loading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
            </button>
          </form>
        </section>

        <aside className="insights-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Insights</p>
              <h2>Performance view</h2>
            </div>
            <BarChart3 size={20} />
          </div>

          <div className="metric-row">
            <Metric label="Top title" value={topTitles[0]?.title || "No data"} />
            <Metric label="Strongest city" value={strongestCity?.city || "No data"} />
          </div>

          <div className="chart-block">
            <div className="chart-title">
              <span>Revenue by title</span>
              <span>{year}</span>
            </div>
            <div className="bar-list">
              {topTitles.map((item) => (
                <div className="bar-item" key={item.title}>
                  <span className="bar-label">{item.title}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${Math.max(8, (item.revenue / revenueMax) * 100)}%` }} />
                  </div>
                  <span className="bar-value">{Math.round(item.revenue)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="split-list">
            <SmallList title="Weak genres" rows={weakGenres} primary="genre" secondary="views" />
            <SmallList title="Audience segments" rows={segments} primary="segment" secondary="views" />
          </div>
        </aside>
      </section>

      <section className="lower-grid">
        <TracePanel trace={latestTrace} sources={latestSources} />
        <HistoryPanel history={history} onSelect={(item) => setSelectedResponse(item.response)} />
      </section>
    </main>
  );
}

function StatusBadge({ icon: Icon, label }) {
  return (
    <div className="status-badge">
      <Icon size={16} />
      <span>{label}</span>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SmallList({ title, rows, primary, secondary }) {
  return (
    <div className="small-list">
      <h3>{title}</h3>
      {rows.slice(0, 4).map((row) => (
        <div className="list-row" key={row[primary]}>
          <span>{row[primary]}</span>
          <strong>{row[secondary]}</strong>
        </div>
      ))}
    </div>
  );
}

function TracePanel({ trace, sources }) {
  return (
    <section className="trace-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Trace</p>
          <h2>Tools and sources</h2>
        </div>
        <CheckCircle2 size={20} />
      </div>
      <div className="trace-tools">
        {(trace?.tools_used || []).map((tool) => (
          <span key={tool}>{tool}</span>
        ))}
      </div>
      {trace?.synthesis_engine ? (
        <div className="trace-meta">
          <span>Engine: {trace.synthesis_engine}</span>
          <span>Confidence: {trace.confidence || "n/a"}</span>
        </div>
      ) : null}
      <div className="source-list">
        {sources.map((source, index) => (
          <article key={`${source.name}-${index}`} className="source-item">
            <FileText size={16} />
            <div>
              <strong>{source.name}</strong>
              <p>{source.snippet || source.source_type}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function HistoryPanel({ history, onSelect }) {
  return (
    <section className="history-panel">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">History</p>
          <h2>Recent queries</h2>
        </div>
        <History size={20} />
      </div>
      <div className="history-list">
        {history.length === 0 ? (
          <p className="muted">No questions yet.</p>
        ) : (
          history.map((item) => (
            <button key={`${item.at}-${item.query}`} type="button" onClick={() => onSelect(item)}>
              <span>{item.query}</span>
              <small>{item.tools.join(", ") || "no tools"} - {item.at}</small>
            </button>
          ))
        )}
      </div>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
