import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertCircle, ArrowUpRight, CalendarClock, CalendarDays, CheckCircle2,
  CircleHelp, Clock3, Download, Filter, GraduationCap, History, Laptop, Play,
  RefreshCw, ShieldCheck, Sparkles, Square, Timer, Users, Video, Wifi,
} from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { ErrorState, Loading } from "../../components/AsyncState";
import { Badge } from "../../components/ModuleCard";
import { download, errorMessage, get, post, unwrapList } from "../../services/api";
import "./Attendance.css";

const fmtDate = (value) => {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
};
const fmtTime = (value) => {
  if (!value) return "—";
  const date = new Date(`1970-01-01T${value}`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
};
const statusTone = (status) => ({ PRESENT: "success", LATE: "warning", ABSENT: "muted", IN_PROGRESS: "info" }[status] || "muted");
const statusLabel = (status) => ({ PRESENT: "Present", LATE: "Late", ABSENT: "Absent", IN_PROGRESS: "Tracking live", NOT_JOINED: "Not joined" }[status] || status || "—");
const sessionIcon = (type) => ({ CODING_LAB: Laptop, WORKSHOP: Users, MOCK_INTERVIEW: Video, LEARNING_LAB: Activity, CLASS: GraduationCap }[type] || CalendarClock);

function getWindowState(session) {
  if (!session?.session_date || !session?.start_time || !session?.end_time) return { open: false, label: "Schedule unavailable" };
  const start = new Date(`${session.session_date}T${session.start_time}`);
  let end = new Date(`${session.session_date}T${session.end_time}`);
  if (end <= start) end = new Date(end.getTime() + 24 * 60 * 60 * 1000);
  const now = new Date();
  const opens = new Date(start.getTime() - Number(session.join_window_minutes ?? 15) * 60_000);
  const closes = new Date(end.getTime() + 10 * 60_000);
  if (now < opens) return { open: false, label: `Opens ${fmtTime(opens.toTimeString().slice(0, 8))}` };
  if (now > closes) return { open: false, label: "Session ended" };
  return { open: true, label: "Available to join" };
}

export default function Attendance() {
  const [items, setItems] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [status, setStatus] = useState("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [recordsResponse, summaryResponse, sessionsResponse] = await Promise.all([
        get("/attendance/?page_size=100"),
        get("/attendance/summary/"),
        get("/attendance/sessions/?page_size=100"),
      ]);
      const recordList = unwrapList(recordsResponse);
      const sessionList = unwrapList(sessionsResponse);
      setItems(recordList);
      setSummary(summaryResponse);
      setSessions(sessionList);
      const current = sessionList.find((item) => item.attendance_status === "IN_PROGRESS");
      setActiveSession((previous) => {
        if (current) return { ...current, attended_minutes: current.attended_minutes || 0 };
        if (previous && !sessionList.some((item) => item.id === previous.id)) return null;
        return null;
      });
    } catch (e) {
      setError(errorMessage(e, "Could not load attendance data. Check your connection and try again."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  // This is background tracking, not a student-present button. Only visible, authenticated session activity
  // sends heartbeats. The backend caps credited time between heartbeats and calculates the final status.
  useEffect(() => {
    if (!activeSession?.id || activeSession.attendance_status !== "IN_PROGRESS") return undefined;
    const sessionId = activeSession.id;
    const timer = window.setInterval(async () => {
      if (document.visibilityState !== "visible") return;
      try {
        const result = await post(`/attendance/sessions/${sessionId}/heartbeat/`, {});
        if (result.finalized || result.attendance?.status !== "IN_PROGRESS") {
          setActiveSession(null);
          setNotice(`Attendance finalized: ${statusLabel(result.attendance?.status)}.`);
          await load();
          return;
        }
        setActiveSession((current) => current?.id === sessionId ? {
          ...current,
          attended_minutes: result.attended_minutes ?? current.attended_minutes ?? 0,
          required_minutes: result.required_minutes ?? current.required_minutes ?? current.minimum_attendance_minutes,
        } : current);
      } catch {
        // Preserve the room if a heartbeat is temporarily interrupted; the next interval retries.
      }
    }, 30_000);
    return () => window.clearInterval(timer);
  }, [activeSession?.id, activeSession?.attendance_status]);

  useEffect(() => {
    if (!activeSession?.id || activeSession.attendance_status !== "IN_PROGRESS") return undefined;
    const sessionId = activeSession.id;
    const onVisibilityChange = async () => {
      if (document.visibilityState === "hidden") {
        try { await post(`/attendance/sessions/${sessionId}/pause/`, {}); } catch { /* the next visible heartbeat can recover */ }
        return;
      }
      try {
        const result = await post(`/attendance/sessions/${sessionId}/heartbeat/`, {});
        if (result.finalized || result.attendance?.status !== "IN_PROGRESS") {
          setActiveSession(null);
          setNotice(`Attendance finalized: ${statusLabel(result.attendance?.status)}.`);
          await load();
        } else {
          setActiveSession((current) => current?.id === sessionId ? {
            ...current,
            attended_minutes: result.attended_minutes ?? current.attended_minutes ?? 0,
            required_minutes: result.required_minutes ?? current.required_minutes ?? current.minimum_attendance_minutes,
          } : current);
        }
      } catch { /* retry through the periodic heartbeat */ }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [activeSession?.id, activeSession?.attendance_status]);

  const exportHistory = async () => {
    setError("");
    try {
      const result = await download("/attendance/export/");
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.filename || "scott-attendance-history.csv";
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(errorMessage(e, "Unable to export attendance history."));
    }
  };

  const join = async (session) => {
    setWorking(true);
    setError("");
    setNotice("");
    try {
      const result = await post(`/attendance/sessions/${session.id}/join/`, {});
      const selected = {
        ...session,
        ...(result.session || {}),
        attendance_status: result.attendance?.status || "IN_PROGRESS",
        attended_minutes: result.attendance?.attended_minutes || 0,
        required_minutes: result.session?.minimum_attendance_minutes || session.minimum_attendance_minutes,
      };
      setActiveSession(selected);
      setNotice(result.resumed ? "Your tracked session has been resumed." : "Session joined. Attendance is now being tracked automatically.");
      await load();
      setActiveSession((current) => current?.id === session.id ? { ...selected, attendance_status: "IN_PROGRESS" } : current);
    } catch (e) {
      setError(errorMessage(e, "Unable to join this session."));
    } finally {
      setWorking(false);
    }
  };

  const finish = async () => {
    if (!activeSession) return;
    setWorking(true);
    try {
      const result = await post(`/attendance/sessions/${activeSession.id}/leave/`, {});
      const finalStatus = result.attendance?.status;
      setNotice(`Session ended. Final attendance: ${statusLabel(finalStatus)} (${result.attendance?.attended_minutes ?? activeSession.attended_minutes ?? 0} verified minutes).`);
      setActiveSession(null);
      await load();
    } catch (e) {
      setError(errorMessage(e, "Unable to finalize the session."));
    } finally {
      setWorking(false);
    }
  };

  const upcoming = useMemo(() => sessions.filter((session) => session.is_active && ["NOT_JOINED", "IN_PROGRESS"].includes(session.attendance_status)), [sessions]);
  const filteredItems = useMemo(() => items.filter((item) => {
    const matchesStatus = status === "ALL" || item.status === status;
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || `${item.session_title} ${item.course_title} ${item.trainer_name} ${item.session_type}`.toLowerCase().includes(query);
    return matchesStatus && matchesSearch;
  }), [items, status, search]);
  const percentage = Number(summary?.percentage || 0);
  const requiredMinutes = Number(activeSession?.required_minutes || activeSession?.minimum_attendance_minutes || 15);
  const activeMinutes = Number(activeSession?.attended_minutes || 0);
  const activeProgress = Math.min(100, Math.round(activeMinutes / Math.max(1, requiredMinutes) * 100));

  if (loading) return <div className="smart-attendance"><PageHeader eyebrow="SKelo · SMART ATTENDANCE" title="Attendance" subtitle="Verified learning participation, recorded automatically."/><Loading text="Syncing attendance sessions…"/></div>;
  if (error && !summary && !items.length) return <div className="smart-attendance"><PageHeader eyebrow="SKelo · SMART ATTENDANCE" title="Attendance" subtitle="Verified learning participation, recorded automatically."/><ErrorState text={error} onRetry={load}/></div>;

  return (
    <div className="smart-attendance">
      <PageHeader eyebrow="SKelo · SMART ATTENDANCE" title="Your attendance" subtitle="Your attendance is calculated from verified participation in scheduled learning sessions—no manual Present/Absent marking." />
      {error && <div className="sa-alert sa-alert-error"><AlertCircle size={17}/><span>{error}</span><button type="button" onClick={() => setError("")}>Dismiss</button></div>}
      {notice && <div className="sa-alert sa-alert-success"><CheckCircle2 size={17}/><span>{notice}</span><button type="button" onClick={() => setNotice("")}>Dismiss</button></div>}

      <section className="sa-hero">
        <div className="sa-hero-grid" aria-hidden="true" />
        <div className="sa-hero-copy">
          <div className="sa-kicker"><Sparkles size={14}/> SMART PARTICIPATION TRACKING</div>
          <h2>Show up. Learn consistently.<br/><span>Let SKelo track the rest.</span></h2>
          <p>Join a scheduled class, coding lab, workshop, or mock interview. Verified active time is recorded in the background and your attendance is finalized using your institute’s rules.</p>
          <div className="sa-hero-pills"><span><ShieldCheck size={13}/> Authenticated activity</span><span><Wifi size={13}/> Automatic sync</span><span><Clock3 size={13}/> Server-timed duration</span></div>
        </div>
        <div className="sa-ring-wrap">
          <div className="sa-ring" style={{ "--sa-percent": `${Math.max(0, Math.min(100, percentage))}%` }}><div><strong>{percentage.toFixed(0)}%</strong><span>ATTENDANCE</span></div></div>
          <small>{summary?.minimum_percentage ?? 75}% target</small>
        </div>
      </section>

      <section className="sa-stat-grid">
        <div className="sa-stat-card"><div className="sa-stat-icon violet"><CalendarDays size={18}/></div><span>Finalized sessions</span><strong>{summary?.total_sessions ?? 0}</strong><small>Recorded in your history</small></div>
        <div className="sa-stat-card"><div className="sa-stat-icon green"><CheckCircle2 size={18}/></div><span>Present</span><strong>{summary?.present ?? 0}</strong><small>Met the participation rule</small></div>
        <div className="sa-stat-card"><div className="sa-stat-icon amber"><Clock3 size={18}/></div><span>Late arrivals</span><strong>{summary?.late ?? 0}</strong><small>Joined after the grace period</small></div>
        <div className="sa-stat-card"><div className="sa-stat-icon rose"><CalendarClock size={18}/></div><span>Missed sessions</span><strong>{summary?.absent ?? 0}</strong><small>{summary?.in_progress ?? 0} session(s) tracking now</small></div>
      </section>

      {summary?.needs_attention && <section className="sa-support-note"><div><AlertCircle size={19}/></div><div><b>Your attendance is below the current target</b><p>You're at {percentage.toFixed(1)}%, below the {summary.minimum_percentage}% target. Review upcoming sessions and contact your trainer if you need help or think a record is incorrect.</p></div></section>}

      <section className="sa-section-head"><div><span className="sa-section-eyebrow">NEXT UP</span><h2>Scheduled sessions</h2><p>Attendance tracking begins when you enter an eligible session and runs automatically while this page is visible.</p></div><button className="sa-light-btn" onClick={load} type="button"><RefreshCw size={14}/> Refresh</button></section>

      {activeSession && <section className="sa-live-room">
        <div className="sa-live-top"><div className="sa-live-dot"><span/> LIVE TRACKING</div><Badge tone="info">{activeSession.session_type_label || activeSession.session_type || "Learning session"}</Badge></div>
        <div className="sa-live-main"><div className="sa-live-icon"><Activity size={24}/></div><div className="sa-live-copy"><h3>{activeSession.title}</h3><p>{activeSession.course_title || activeSession.batch_label || "Scheduled SKelo session"} · {fmtTime(activeSession.start_time)}–{fmtTime(activeSession.end_time)}</p><span><ShieldCheck size={13}/> Activity is being tracked automatically. Keep this tab visible while participating.</span></div><button className="sa-end-btn" disabled={working} onClick={finish} type="button"><Square size={14} fill="currentColor"/> End participation</button></div>
        <div className="sa-progress-wrap"><div className="sa-progress-meta"><span>Verified active time</span><b>{activeMinutes} / {requiredMinutes} min required</b></div><div className="sa-progress"><i style={{ width: `${activeProgress}%` }}/></div><small>Only server-recorded heartbeat intervals count. Leaving early may result in an Absent status if the minimum time is not met.</small></div>
      </section>}

      <section className="sa-session-grid">
        {upcoming.length ? upcoming.map((session) => {
          const Icon = sessionIcon(session.session_type);
          const windowState = getWindowState(session);
          const inProgress = session.attendance_status === "IN_PROGRESS";
          const disabled = working || (!inProgress && !windowState.open);
          return <article className={`sa-session-card ${inProgress ? "is-tracking" : ""}`} key={session.id}>
            <div className="sa-session-card-head"><div className="sa-session-type-icon"><Icon size={19}/></div><Badge tone={inProgress ? "info" : "muted"}>{inProgress ? "In progress" : (session.session_type_label || session.session_type || "Scheduled")}</Badge></div>
            <div className="sa-session-date">{fmtDate(session.session_date)}</div><h3>{session.title}</h3>
            <p className="sa-session-description">{session.description || "A scheduled learning activity in your SKelo learning plan."}</p>
            <div className="sa-session-meta"><span><Clock3 size={14}/>{fmtTime(session.start_time)} – {fmtTime(session.end_time)}</span>{session.course_title && <span><GraduationCap size={14}/>{session.course_title}</span>}{session.location && <span><Video size={14}/>{session.location}</span>}</div>
            <div className="sa-session-foot"><span className={windowState.open || inProgress ? "sa-session-available" : "sa-session-waiting"}><span/>{inProgress ? "Tracking started" : windowState.label}</span><button type="button" disabled={disabled} onClick={() => join(session)} className="sa-join-btn">{inProgress ? "Resume tracking" : windowState.open ? "Join session" : "Not open yet"}<ArrowUpRight size={15}/></button></div>
          </article>;
        }) : <div className="sa-empty-sessions"><div><CalendarClock size={22}/></div><b>No upcoming sessions</b><p>When your trainer schedules a class, lab, workshop, or mock interview for your group, it will appear here.</p></div>}
      </section>

      <section className="sa-history-section">
        <div className="sa-section-head sa-history-head"><div><span className="sa-section-eyebrow">YOUR RECORD</span><h2>Attendance history</h2><p>Automatic records from completed sessions, including verified participation time.</p></div><button type="button" className="sa-light-btn" onClick={exportHistory}><Download size={14}/> Export CSV</button></div>
        <div className="sa-history-toolbar"><div className="sa-search"><Filter size={15}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search sessions, courses, trainers…"/></div><div className="sa-status-filters">{[["ALL", "All"], ["PRESENT", "Present"], ["LATE", "Late"], ["ABSENT", "Absent"], ["IN_PROGRESS", "Tracking"]].map(([value, label]) => <button type="button" key={value} className={status === value ? "active" : ""} onClick={() => setStatus(value)}>{label}</button>)}</div></div>
        {filteredItems.length ? <div className="sa-history-list">{filteredItems.map((item) => <article className="sa-history-row" key={item.id}><div className={`sa-history-marker ${item.status.toLowerCase()}`}>{item.status === "PRESENT" ? <CheckCircle2 size={17}/> : item.status === "IN_PROGRESS" ? <Activity size={17}/> : item.status === "LATE" ? <Clock3 size={17}/> : <CircleHelp size={17}/>}</div><div className="sa-history-info"><b>{item.session_title}</b><span>{fmtDate(item.session_date)} · {item.session_type || "Learning session"}{item.course_title ? ` · ${item.course_title}` : ""}</span><small>{item.remarks || "Attendance status generated from session participation."}</small></div><div className="sa-history-minutes"><b>{item.attended_minutes ?? 0} min</b><span>verified</span></div><Badge tone={statusTone(item.status)}>{statusLabel(item.status)}</Badge></article>)}</div> : <div className="sa-history-empty"><History size={24}/><b>No matching attendance records</b><span>Records appear here automatically after scheduled sessions finish.</span></div>}
      </section>

      <div className="sa-footer-note"><ShieldCheck size={15}/><span><b>How automatic attendance works:</b> SKelo records authenticated session joins and time-limited heartbeats while the session page is active. The server applies your session’s minimum active-time and late-arrival rules. It does not infer attendance from opening a course, and an administrator can only correct a record through a reviewed, audited exception.</span></div>
    </div>
  );
}
