import React, { useEffect, useState } from "react";
import { ArrowRight, Award, BrainCircuit, CheckCircle2, Clock3, History, Mic2, Play, Search, Sparkles, Video } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { Empty, ErrorState, Loading } from "../../components/AsyncState";
import { Badge } from "../../components/ModuleCard";
import { errorMessage, get, post, unwrapList } from "../../services/api";
import "./Interview.css";

const TYPES = [
  ["MIXED", "Full Mock Interview", "A placement-style round with HR and technical questions", "✦"],
  ["TECHNICAL", "Technical Interview", "Core concepts, fundamentals and projects", "⚙"],
  ["HR", "HR Interview", "Motivation, communication and behavioral questions", "◌"],
  ["CODING", "Coding Interview", "Explain your approach and reason through a solution", "⌘"],
  ["DSA", "DSA Interview", "Data structures, algorithms and complexity", "◇"],
  ["BEHAVIORAL", "Behavioral Interview", "Teamwork, leadership and conflict resolution", "↗"],
  ["PROJECT", "Project Interview", "Discuss architecture, decisions and lessons", "▦"],
  ["SYSTEM_DESIGN", "System Design", "Architecture, reliability and trade-offs", "⌘"],
  ["COMPANY_SPECIFIC", "Company Practice", "Practice tailored to a selected company and role", "◎"],
  ["RESUME_BASED", "Resume-Based Practice", "Use resume skills and project notes as session context", "▤"],
];

const initial = {
  interview_type: "TECHNICAL",
  company: "General Placement",
  role: "Software Developer",
  difficulty: "INTERMEDIATE",
  duration_minutes: 30,
  interview_mode: "TEXT",
  technical_topics: "Java, SQL, DSA",
};

function interviewError(error) {
  const data = error?.response?.data;
  const text = typeof data === "string" ? data : "";
  if (text.includes("<!DOCTYPE html") || text.includes("<html") || error?.response?.status === 404) {
    return "The interview API returned a 404/HTML error page. Install the updated Django interviews/urls.py and interviews/views.py, run migrations, and restart the backend server. Your interview has not started yet.";
  }
  return errorMessage(error, "Could not complete that interview action. Please try again.");
}

export default function Interviews() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");
  const [startError, setStartError] = useState("");
  const [form, setForm] = useState(initial);
  const [starting, setStarting] = useState(false);
  const nav = useNavigate();

  const load = () => {
    setLoading(true);
    setHistoryError("");
    get("/interviews/?page_size=100")
      .then((data) => setItems(unwrapList(data)))
      .catch((error) => setHistoryError(interviewError(error)))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const change = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  const start = async () => {
    setStarting(true);
    setStartError("");
    try {
      const type = TYPES.find((item) => item[0] === form.interview_type)?.[1] || "Mock Interview";
      const created = await post("/interviews/practice/start/", {
        ...form,
        duration_minutes: Number(form.duration_minutes),
        title: `${form.company} · ${type}`,
      });
      if (!created?.id) throw new Error("The backend did not return an interview session ID. Check that the updated Django interview URLs are installed.");
      nav(`/interviews/${created.id}`);
    } catch (error) {
      setStartError(interviewError(error));
    } finally {
      setStarting(false);
    }
  };

  const filtered = items.filter((item) => JSON.stringify(item).toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="interviews-page">
      <PageHeader eyebrow="SKelo · CAREER PREPARATION" title="AI Interview Studio" subtitle="Practise a real interview flow, answer one question at a time, and get an actionable report after the round." />
      <section className="interview-hero">
        <div>
          <span className="interview-kicker"><Sparkles size={14} /> YOUR PERSONAL PRACTICE ROOM</span>
          <h2>Show up prepared.<br /><em>Leave more confident.</em></h2>
          <p>Choose a format and target role. The interviewer asks questions, evaluates submitted answers, and adapts the next question when AI is configured.</p>
          <button className="interview-primary" onClick={() => document.getElementById("interview-setup")?.scrollIntoView({ behavior: "smooth" })}><Play size={16} fill="currentColor" /> Set up an interview <ArrowRight size={16} /></button>
        </div>
        <div className="interview-hero-art" aria-hidden="true">
          <div className="orb orb-one" /><div className="orb orb-two" />
          <div className="ai-avatar"><BrainCircuit size={54} /></div>
          <div className="floating-note note-top"><Mic2 size={16} /> Practise out loud</div>
          <div className="floating-note note-bottom"><CheckCircle2 size={16} /> Learn with every attempt</div>
        </div>
      </section>

      <div className="interview-section-heading">
        <div><span className="interview-kicker">PRACTICE PATHS</span><h2>What would you like to practise?</h2></div>
        <span className="interview-muted">Select a type to configure the session</span>
      </div>
      <div className="interview-type-grid">
        {TYPES.map((type) => (
          <button key={type[0]} className={`interview-type-card ${form.interview_type === type[0] ? "selected" : ""}`} onClick={() => setForm((current) => ({ ...current, interview_type: type[0] }))}>
            <span className="type-symbol">{type[3]}</span><span className="type-title">{type[1]}</span><span className="type-description">{type[2]}</span><ArrowRight size={17} className="type-arrow" />
          </button>
        ))}
      </div>

      <section id="interview-setup" className="interview-setup">
        <div className="setup-heading"><div className="setup-icon"><Sparkles size={20} /></div><div><span className="interview-kicker">PERSONALIZE YOUR SESSION</span><h2>Configure your interview</h2><p>Choose the conditions you want to practise for.</p></div></div>
        <div className="interview-form-grid">
          <label>Interview type<select name="interview_type" value={form.interview_type} onChange={change}>{TYPES.map((type) => <option key={type[0]} value={type[0]}>{type[1]}</option>)}</select></label>
          <label>Company<select name="company" value={form.company} onChange={change}>{["General Placement", "TCS", "Infosys", "Accenture", "Amazon", "Google", "Microsoft", "Zoho", "Wipro", "Other"].map((company) => <option key={company} value={company}>{company}</option>)}</select></label>
          <label>Job role<input name="role" value={form.role} onChange={change} placeholder="e.g. Software Developer" maxLength={150} /></label>
          <label>Difficulty<select name="difficulty" value={form.difficulty} onChange={change}><option value="BEGINNER">Beginner</option><option value="INTERMEDIATE">Intermediate</option><option value="ADVANCED">Advanced</option></select></label>
          <label>Duration<select name="duration_minutes" value={form.duration_minutes} onChange={change}>{[10, 15, 20, 30, 45, 60].map((minutes) => <option key={minutes} value={minutes}>{minutes} minutes</option>)}</select></label>
          <label>Practice mode<select name="interview_mode" value={form.interview_mode} onChange={change}><option value="TEXT">Text-based</option><option value="VOICE">Voice (browser microphone)</option><option value="VIDEO">Video (camera + answers)</option></select></label>
          <label className="topics-field">Technical topics / resume context<input name="technical_topics" value={form.technical_topics} onChange={change} placeholder="Java, Python, SQL, skills or project context" maxLength={2000} /></label>
        </div>
        <div className="setup-footer"><span><Clock3 size={16} /> {form.duration_minutes} minutes <span className="dot-separator">·</span> {form.difficulty.toLowerCase()} level</span><button className="interview-primary" disabled={starting} onClick={start}>{starting ? "Preparing your interview…" : "Start practice session"} <ArrowRight size={16} /></button></div>
        {startError && <div className="interview-error" role="alert"><b>Could not start interview</b><span>{startError}</span><button type="button" onClick={() => setStartError("")}>Dismiss</button></div>}
        <p className="simulation-note">Company selections create practice simulations, not official or guaranteed interview questions. Text practice works without an AI key; configure OPENAI_API_KEY in Django to enable AI-generated follow-ups and answer analysis. Browser voice/camera availability depends on the device and browser.</p>
      </section>

      <div className="interview-section-heading history-heading"><div><span className="interview-kicker">KEEP GROWING</span><h2>Your interview history</h2></div><label className="interview-search"><Search size={15} /><input value={q} onChange={(event) => setQ(event.target.value)} placeholder="Search your sessions" /></label></div>
      {loading ? <Loading text="Loading your interview history…" /> : historyError ? <ErrorState text={historyError} onRetry={load} /> : !filtered.length ? <Empty title="Your next practice starts here" text="Start a practice session above. Your saved answers, scores, and reports will appear here." /> : (
        <div className="interview-history-grid">{filtered.map((item) => <article className="interview-history-card" key={item.id}><div className="history-icon"><History size={20} /></div><div className="history-main"><div className="history-meta"><Badge tone={item.status === "COMPLETED" ? "success" : item.status === "CANCELLED" ? "muted" : "info"}>{item.status?.replaceAll("_", " ")}</Badge><span>{item.company || "General Placement"}</span></div><h3>{item.title}</h3><p>{item.role || "Interview practice"} · {item.duration_minutes || 30} min</p><div className="history-date"><Clock3 size={13} />{item.created_at ? new Date(item.created_at).toLocaleDateString() : "Practice session"}{item.status === "COMPLETED" ? ` · Score ${Math.round(Number(item.overall_score || 0))}/100` : ""}</div></div><button className="history-open" onClick={() => nav(`/interviews/${item.id}`)} aria-label={`Open ${item.title}`}><ArrowRight size={18} /></button></article>)}</div>
      )}
      <div className="interview-disclaimer"><Award size={18} /><span>Practice scores are learning indicators, not predictions of hiring outcomes. Feedback focuses on answer content, reasoning and clarity—not appearance, accent or inferred emotions.</span></div>
    </div>
  );
}
