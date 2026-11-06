import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertCircle, CalendarClock, CheckCircle2, Clock3, Download,
  GraduationCap, History, Plus, RefreshCw, ShieldCheck, Sparkles, Users, X,
} from "lucide-react";
import { Badge, DetailPanel } from "../../components/ModuleCard";
import { ErrorState, Loading } from "../../components/AsyncState";
import { download, errorMessage, get, post, patch, del, unwrapList } from "../../services/api";
import "./AttendanceManager.css";

const dateToday = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
};
const blankSession = () => ({
  title: "", description: "", session_type: "CLASS", course: "", session_date: dateToday(),
  start_time: "10:00", end_time: "11:00", location: "Online", batch_label: "",
  target_department: "", target_year: "", target_semester: "", minimum_attendance_minutes: 15,
  late_after_minutes: 10, join_window_minutes: 15, is_active: true,
});
const fmtTime = (value) => {
  if (!value) return "—";
  const d = new Date(`1970-01-01T${value}`);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
};
const fmtDate = (value) => value ? new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "—";
const toneFor = (status) => ({ PRESENT: "success", LATE: "warning", ABSENT: "muted", IN_PROGRESS: "info" }[status] || "muted");

export default function AttendanceManager({ data = [], onDone }) {
  const [form, setForm] = useState(blankSession);
  const [policy, setPolicy] = useState({ minimum_attendance_percentage: 75, default_minimum_attendance_minutes: 15, default_late_after_minutes: 10, default_join_window_minutes: 15 });
  const [courses, setCourses] = useState([]);
  const [overview, setOverview] = useState(null);
  const [selected, setSelected] = useState(null);
  const [records, setRecords] = useState([]);
  const [correction, setCorrection] = useState(null);
  const [correctionForm, setCorrectionForm] = useState({ status: "PRESENT", remarks: "" });
  const [saving, setSaving] = useState(false);
  const [loadingExtras, setLoadingExtras] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refreshExtras = async () => {
    setLoadingExtras(true);
    try {
      const results = await Promise.allSettled([
        get("/attendance/admin/overview/"), get("/attendance/policy/"), get("/courses/?page_size=100"),
      ]);
      if (results[0].status === "fulfilled") setOverview(results[0].value);
      if (results[1].status === "fulfilled") {
        const nextPolicy = results[1].value;
        setPolicy((current) => ({ ...current, ...nextPolicy }));
        setForm((current) => current.id ? current : ({
          ...current,
          minimum_attendance_minutes: nextPolicy.default_minimum_attendance_minutes ?? current.minimum_attendance_minutes,
          late_after_minutes: nextPolicy.default_late_after_minutes ?? current.late_after_minutes,
          join_window_minutes: nextPolicy.default_join_window_minutes ?? current.join_window_minutes,
        }));
      }
      if (results[2].status === "fulfilled") setCourses(unwrapList(results[2].value));
      const failure = results.find((result) => result.status === "rejected");
      if (failure && !overview) setError(errorMessage(failure.reason));
    } finally {
      setLoadingExtras(false);
    }
  };

  useEffect(() => { refreshExtras(); }, []);

  const refreshRecords = async (sessionId) => {
    const result = await get(`/attendance/sessions/${sessionId}/records/?page_size=100`);
    setRecords(unwrapList(result));
  };

  const resetForm = () => setForm(blankSession());
  const change = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
  };

  const saveSession = async (event) => {
    event.preventDefault();
    setSaving(true); setError(""); setNotice("");
    try {
      const payload = {
        ...form,
        course: form.course ? Number(form.course) : null,
        target_year: form.target_year ? Number(form.target_year) : null,
        target_semester: form.target_semester ? Number(form.target_semester) : null,
        minimum_attendance_minutes: Number(form.minimum_attendance_minutes || policy.default_minimum_attendance_minutes || 15),
        late_after_minutes: Number(form.late_after_minutes || 0),
        join_window_minutes: Number(form.join_window_minutes || 0),
      };
      const saved = form.id ? await patch(`/attendance/sessions/${form.id}/`, payload) : await post("/attendance/sessions/", payload);
      setSelected(saved);
      setNotice(form.id ? "Session updated." : "Session scheduled. Students will be tracked automatically when they join within the session window.");
      resetForm();
      await refreshExtras();
      onDone?.(form.id ? "Attendance session updated." : "Attendance session scheduled successfully.");
    } catch (e) { setError(errorMessage(e)); }
    finally { setSaving(false); }
  };

  const editSession = (session) => {
    setForm({
      id: session.id, title: session.title || "", description: session.description || "", session_type: session.session_type || "CLASS",
      course: session.course || "", session_date: session.session_date || dateToday(), start_time: (session.start_time || "10:00").slice(0, 5),
      end_time: (session.end_time || "11:00").slice(0, 5), location: session.location || "", batch_label: session.batch_label || "",
      target_department: session.target_department || "", target_year: session.target_year || "", target_semester: session.target_semester || "",
      minimum_attendance_minutes: session.minimum_attendance_minutes ?? policy.default_minimum_attendance_minutes ?? 15,
      late_after_minutes: session.late_after_minutes ?? policy.default_late_after_minutes ?? 10,
      join_window_minutes: session.join_window_minutes ?? policy.default_join_window_minutes ?? 15,
      is_active: session.is_active,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const inspectSession = async (session) => {
    setSelected(session); setCorrection(null); setError("");
    try { await refreshRecords(session.id); }
    catch (e) { setError(errorMessage(e)); }
  };

  const toggleSession = async (session) => {
    try {
      if (session.is_active) await del(`/attendance/sessions/${session.id}/`);
      else await patch(`/attendance/sessions/${session.id}/`, { is_active: true });
      setNotice(session.is_active ? "Session deactivated. Attendance history has been preserved." : "Session activated.");
      await refreshExtras();
      onDone?.("Session status updated.");
    } catch (e) { setError(errorMessage(e)); }
  };

  const savePolicy = async (event) => {
    event.preventDefault(); setSaving(true); setError("");
    try {
      const payload = {
        minimum_attendance_percentage: Number(policy.minimum_attendance_percentage),
        default_minimum_attendance_minutes: Number(policy.default_minimum_attendance_minutes),
        default_late_after_minutes: Number(policy.default_late_after_minutes),
        default_join_window_minutes: Number(policy.default_join_window_minutes),
      };
      const updated = await post("/attendance/policy/", payload);
      setPolicy((current) => ({ ...current, ...updated }));
      setNotice("Automatic attendance policy saved. New sessions will use these default rules.");
      await refreshExtras();
    } catch (e) { setError(errorMessage(e)); }
    finally { setSaving(false); }
  };

  const reviewRecord = async (event) => {
    event.preventDefault();
    if (!selected || !correction) return;
    setSaving(true); setError("");
    try {
      await post(`/attendance/sessions/${selected.id}/mark/`, { student_id: correction.student, status: correctionForm.status, remarks: correctionForm.remarks });
      setNotice("Correction saved with a review audit record."); setCorrection(null);
      await refreshRecords(selected.id); await refreshExtras();
    } catch (e) { setError(errorMessage(e)); }
    finally { setSaving(false); }
  };

  const exportCsv = async () => {
    try {
      const result = await download(`/attendance/export/?session=${selected?.id}`);
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a"); link.href = url; link.download = `${(selected?.title || "attendance").toLowerCase().replace(/[^a-z0-9]+/g, "-")}-roster.csv`; link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) { setError(errorMessage(e, "Unable to export this session roster.")); }
  };

  const activeSessions = useMemo(() => data.filter((session) => session.is_active), [data]);
  const avgRate = Number(overview?.attendance_rate || 0);
  const clearEditing = () => { resetForm(); setError(""); };

  return <div className="attendance-admin">
    <div className="aa-intro-banner"><div className="aa-banner-icon"><ShieldCheck size={24}/></div><div><span>SKelo SMART ATTENDANCE</span><h2>Automatic participation, accountable records.</h2><p>Schedule qualifying learning sessions once. Student join events and active-session heartbeats build the attendance record; staff only reviews exceptions.</p></div><div className="aa-banner-pills"><span><Activity size={13}/> Auto tracking</span><span><History size={13}/> Audit trail</span></div></div>
    {notice && <div className="aa-alert success"><CheckCircle2 size={16}/><span>{notice}</span><button type="button" onClick={() => setNotice("")}>Dismiss</button></div>}
    {error && <div className="aa-alert error"><AlertCircle size={16}/><span>{error}</span><button type="button" onClick={() => setError("")}>Dismiss</button></div>}

    {loadingExtras ? <Loading text="Loading attendance analytics…"/> : <>
      <div className="aa-metric-grid">
        <div className="aa-metric"><div className="aa-metric-icon purple"><CalendarClock size={18}/></div><span>Active sessions</span><b>{overview?.sessions_total ?? activeSessions.length}</b><small>Scheduled for students</small></div>
        <div className="aa-metric"><div className="aa-metric-icon green"><CheckCircle2 size={18}/></div><span>Overall attendance</span><b>{avgRate.toFixed(1)}%</b><small>Finalized attendance records</small></div>
        <div className="aa-metric"><div className="aa-metric-icon blue"><Users size={18}/></div><span>Students tracked</span><b>{overview?.students_tracked ?? 0}</b><small>With saved session records</small></div>
        <div className="aa-metric"><div className="aa-metric-icon orange"><Activity size={18}/></div><span>Live tracking</span><b>{overview?.in_progress ?? 0}</b><small>Sessions currently in progress</small></div>
      </div>

      <DetailPanel title={form.id ? `Edit session · ${form.title || "Untitled"}` : "Schedule an attendance session"} actions={form.id ? <button type="button" className="outline-btn" onClick={clearEditing}><X size={14}/> Cancel edit</button> : null}>
        <form className="aa-session-form" onSubmit={saveSession}>
          <label className="aa-span-2">Session title<input name="title" value={form.title} onChange={change} placeholder="e.g. Python fundamentals — live class" required/></label>
          <label>Session type<select name="session_type" value={form.session_type} onChange={change}><option value="CLASS">Live class</option><option value="CODING_LAB">Coding lab</option><option value="WORKSHOP">Workshop</option><option value="MOCK_INTERVIEW">Mock interview</option><option value="LEARNING_LAB">Learning session</option><option value="OTHER">Other</option></select></label>
          <label>Course (optional)<select name="course" value={form.course} onChange={change}><option value="">General / no course</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</select></label>
          <label>Date<input type="date" name="session_date" value={form.session_date} onChange={change} required/></label>
          <label>Starts at<input type="time" name="start_time" value={form.start_time} onChange={change} required/></label>
          <label>Ends at<input type="time" name="end_time" value={form.end_time} onChange={change} required/></label>
          <label>Location / meeting URL<input name="location" value={form.location} onChange={change} placeholder="Room or meeting link"/></label>
          <label>Batch label<input name="batch_label" value={form.batch_label} onChange={change} placeholder="e.g. CSE · Batch 2027"/></label>
          <label>Target department<input name="target_department" value={form.target_department} onChange={change} placeholder="Blank = all departments"/></label>
          <label>Target year<select name="target_year" value={form.target_year} onChange={change}><option value="">All years</option>{[1,2,3,4,5].map((year) => <option key={year} value={year}>{year}{year === 1 ? "st" : year === 2 ? "nd" : year === 3 ? "rd" : "th"} year</option>)}</select></label>
          <label>Target semester<select name="target_semester" value={form.target_semester} onChange={change}><option value="">All semesters</option>{Array.from({length: 10}, (_, i) => i + 1).map((semester) => <option key={semester} value={semester}>Semester {semester}</option>)}</select></label>
          <label>Minimum active minutes<input type="number" min="1" max="1440" name="minimum_attendance_minutes" value={form.minimum_attendance_minutes} onChange={change} required/></label>
          <label>Late after (minutes)<input type="number" min="0" max="240" name="late_after_minutes" value={form.late_after_minutes} onChange={change} required/></label>
          <label>Join opens (minutes before)<input type="number" min="0" max="180" name="join_window_minutes" value={form.join_window_minutes} onChange={change} required/></label>
          <label className="aa-span-2">Session details<textarea name="description" value={form.description} onChange={change} rows="3" placeholder="What will students participate in?"/></label>
          {form.id && <label className="aa-checkbox"><input type="checkbox" name="is_active" checked={form.is_active} onChange={change}/> Session active</label>}
          <div className="aa-form-actions aa-span-2"><p><ShieldCheck size={14}/> No manual attendance marking. Status is calculated from server-recorded activity.</p><button className="primary-btn" disabled={saving}><Plus size={15}/>{saving ? "Saving…" : form.id ? "Save session changes" : "Schedule session"}</button></div>
        </form>
      </DetailPanel>

      <DetailPanel title="Global automatic attendance rules" actions={<Badge tone="info">Applies to new sessions</Badge>}>
        <form className="aa-policy-form" onSubmit={savePolicy}>
          <label>Attendance target (%)<input type="number" min="1" max="100" step="0.5" value={policy.minimum_attendance_percentage} onChange={(e) => setPolicy({ ...policy, minimum_attendance_percentage: e.target.value })} required/></label>
          <label>Default required active minutes<input type="number" min="1" max="1440" value={policy.default_minimum_attendance_minutes} onChange={(e) => setPolicy({ ...policy, default_minimum_attendance_minutes: e.target.value })} required/></label>
          <label>Default late threshold (minutes)<input type="number" min="0" max="240" value={policy.default_late_after_minutes} onChange={(e) => setPolicy({ ...policy, default_late_after_minutes: e.target.value })} required/></label>
          <label>Default join window (minutes)<input type="number" min="0" max="180" value={policy.default_join_window_minutes} onChange={(e) => setPolicy({ ...policy, default_join_window_minutes: e.target.value })} required/></label>
          <button className="outline-btn" disabled={saving}>Save attendance rules</button>
        </form>
      </DetailPanel>

      {overview?.insight && <section className="aa-insight"><div className="aa-insight-icon"><Sparkles size={18}/></div><div><span>{overview.insight_source === "openai" ? "AI ATTENDANCE INSIGHT" : "RULE-BASED ATTENDANCE INSIGHT"}</span><b>{overview.insight}</b><p>Insights summarize verified attendance records and thresholds. Use the session evidence to guide support; they are not a measure of student ability.</p></div></section>}

      <DetailPanel title={`Scheduled sessions · ${data.length}`} actions={<button className="outline-btn" type="button" onClick={refreshExtras}><RefreshCw size={14}/> Refresh analytics</button>}>
        {data.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>Session</th><th>Schedule</th><th>Audience</th><th>Presence</th><th>Status</th><th>Actions</th></tr></thead><tbody>{data.map((session) => <tr key={session.id}>
          <td><b>{session.title}</b><br/><span className="muted-text">{session.session_type_label || session.session_type} · {session.course_title || "General"}</span></td>
          <td>{fmtDate(session.session_date)}<br/><span className="muted-text">{fmtTime(session.start_time)}–{fmtTime(session.end_time)}</span></td>
          <td>{[session.batch_label, session.target_department, session.target_year ? `Year ${session.target_year}` : "", session.target_semester ? `Sem ${session.target_semester}` : ""].filter(Boolean).join(" · ") || "All students"}</td>
          <td><b>{session.present_count ?? 0}</b><span className="muted-text"> / {session.attendance_count ?? 0}</span></td>
          <td><Badge tone={session.is_active ? "success" : "muted"}>{session.is_active ? "Active" : "Deactivated"}</Badge></td>
          <td><div className="aa-row-actions"><button type="button" className="aa-text-btn" onClick={() => inspectSession(session)}>View roster</button><button type="button" className="aa-text-btn" onClick={() => editSession(session)}>Edit</button><button type="button" className="aa-text-btn muted" onClick={() => toggleSession(session)}>{session.is_active ? "Deactivate" : "Activate"}</button></div></td>
        </tr>)}</tbody></table></div> : <div className="aa-empty"><CalendarClock size={23}/><b>No sessions scheduled yet</b><span>Create a live class, coding lab, workshop, or mock interview above. Attendance will be recorded automatically for eligible students.</span></div>}
      </DetailPanel>

      {overview?.low_attendance_students?.length > 0 && <DetailPanel title={`Students below target · ${overview.low_attendance_count}`}>
        <p className="muted-text">Students are listed after at least three finalized sessions. Use this as a prompt to review records and provide support.</p>
        <div className="table-scroll"><table className="data-table"><thead><tr><th>Student</th><th>Department</th><th>Sessions attended</th><th>Attendance</th><th>Suggested next step</th></tr></thead><tbody>{overview.low_attendance_students.map((student) => <tr key={student.student_id}><td><b>{student.name}</b><br/><span className="muted-text">{student.email}</span></td><td>{student.department}</td><td>{student.attended} / {student.sessions}</td><td><Badge tone="warning">{student.percentage}%</Badge></td><td className="aa-recommendation">{student.recommendation}</td></tr>)}</tbody></table></div>
      </DetailPanel>}

      {selected && <DetailPanel title={`Session roster · ${selected.title}`} actions={<><button type="button" className="outline-btn" onClick={exportCsv}><Download size={14}/> Export CSV</button><button type="button" className="outline-btn" onClick={() => { setSelected(null); setRecords([]); setCorrection(null); }}><X size={14}/> Close</button></>}>
        {!records.length ? <div className="aa-empty compact"><Users size={21}/><b>No attendance records yet</b><span>Roster records appear as students join or once the scheduled session ends and the backend finalizes absent records.</span></div> : <div className="table-scroll"><table className="data-table"><thead><tr><th>Student</th><th>Status</th><th>Verified minutes</th><th>Joined</th><th>Record source</th><th>Review</th></tr></thead><tbody>{records.map((record) => <tr key={record.id}><td><b>{record.student_name}</b><br/><span className="muted-text">{record.student_email}</span></td><td><Badge tone={toneFor(record.status)}>{record.status.replace("_", " ")}</Badge><br/><span className="muted-text">{record.remarks}</span></td><td>{record.attended_minutes ?? 0} min</td><td>{record.joined_at ? new Date(record.joined_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "—"}</td><td>{record.source === "ADMIN_REVIEW" ? "Reviewed correction" : "Automatic"}</td><td><button type="button" className="aa-text-btn" onClick={() => { setCorrection(record); setCorrectionForm({ status: record.status === "IN_PROGRESS" ? "PRESENT" : record.status, remarks: "" }); }}>Review correction</button></td></tr>)}</tbody></table></div>}
        {correction && <form className="aa-correction-form" onSubmit={reviewRecord}><div><span>REVIEWING RECORD</span><b>{correction.student_name}</b><small>{correction.session_title} · current status {correction.status}</small></div><label>Correct status<select value={correctionForm.status} onChange={(e) => setCorrectionForm({ ...correctionForm, status: e.target.value })}><option value="PRESENT">Present</option><option value="LATE">Late</option><option value="ABSENT">Absent</option></select></label><label className="aa-correction-note">Reason for correction<textarea value={correctionForm.remarks} onChange={(e) => setCorrectionForm({ ...correctionForm, remarks: e.target.value })} placeholder="Explain the evidence used to correct this record" required rows="2"/></label><button className="primary-btn" disabled={saving}><CheckCircle2 size={14}/> Save audited correction</button><button className="outline-btn" type="button" onClick={() => setCorrection(null)}>Cancel</button></form>}
      </DetailPanel>}
    </>}
    <div className="aa-footnote"><ShieldCheck size={15}/><span><b>Integrity note:</b> Automatic attendance is based on authenticated joins and bounded active-time heartbeats; merely opening a course does not count. Status corrections require a reason and are stored as audited staff reviews.</span></div>
  </div>;
}
