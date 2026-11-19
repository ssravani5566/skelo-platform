import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen, CheckCircle2, Clock3, GraduationCap, PlayCircle, ShieldCheck, Sparkles } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { DetailPanel, Badge, Progress } from "../../components/ModuleCard";
import { Empty, ErrorState, Loading } from "../../components/AsyncState";
import { errorMessage, get, post } from "../../services/api";
import "./Lesson.css";

export default function CourseDetail() {
  const { id } = useParams(), nav = useNavigate();
  const [course, setCourse] = useState(null), [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true), [error, setError] = useState("");
  const [notice, setNotice] = useState(""), [saving, setSaving] = useState(false);
  const load = async () => {
    setLoading(true); setError("");
    try {
      const [c, m] = await Promise.all([get(`/courses/${id}/`), get(`/courses/${id}/modules/`)]);
      setCourse(c); setModules(m);
    } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [id]);

  const joinCourse = async () => {
    setSaving(true); setError(""); setNotice("");
    try {
      await post(`/courses/${id}/enroll/`);
      await post(`/courses/${id}/start/`);
      setNotice("You are enrolled. Your learning progress will be saved automatically.");
      await load();
    } catch (e) { setError(errorMessage(e)); }
    finally { setSaving(false); }
  };
  const outcomes = (course?.learning_outcomes || "").split("\n").map((x) => x.trim()).filter(Boolean);
  if (loading) return <Loading text="Loading course..."/>;
  if (error && !course) return <ErrorState text={error} onRetry={load}/>;
  const enrolled = Boolean(course?.enrolled);

  return <div className="course-detail-page">
    <button className="back-link" onClick={() => nav("/courses")}><ArrowLeft size={15}/> Courses</button>
    <PageHeader eyebrow="SKELO · COURSE DETAILS" title={course.title} subtitle={course.description || "Explore the syllabus and learning outcomes for this course."} action={enrolled ? <button className="primary-btn" onClick={() => { const allLessons = modules.flatMap((m) => m.lessons || []); const target = allLessons.find((l) => !l.completed) || allLessons[0]; if (course.completed) setNotice("You have completed this course."); else if (target) nav(`/courses/${id}/lessons/${target.id}`); else setNotice("Your instructor is preparing the course lessons."); }}><PlayCircle size={16}/>{course.completed ? "Course completed" : "Continue learning"}</button> : course.can_enroll ? <button className="primary-btn" onClick={joinCourse} disabled={saving}><GraduationCap size={16}/>{saving ? "Enrolling..." : "Enrol in free course"}</button> : <button className="outline-btn" disabled><ShieldCheck size={15}/> Ask admin for access</button>}/>
    {notice && <div className="success-box"><CheckCircle2 size={14}/>{notice}</div>}
    {error && <div className="form-error">{error}</div>}
    <div className="lms-course-detail-metrics">
      <div><Clock3 size={16}/><span><small>Duration</small><b>{course.duration_minutes ? `${course.duration_minutes} minutes` : "Self paced"}</b></span></div>
      <div><BookOpen size={16}/><span><small>Lessons</small><b>{course.lessons || 0} lessons</b></span></div>
      <div><GraduationCap size={16}/><span><small>Level</small><b>{course.level}</b></span></div>
      <div><Sparkles size={16}/><span><small>Language</small><b>{course.language || "English"}</b></span></div>
      <div><ShieldCheck size={16}/><span><small>Access</small><b>{course.access_type === "PAID" ? `Paid · ₹${course.price}` : "Free"}</b></span></div>
    </div>
    <div className="detail-grid">
      <DetailPanel title="Your learning progress"><div className="big-metric"><strong>{Number(course.progress || 0)}%</strong><span>{course.completed_lessons || 0} of {course.lessons || 0} lessons completed</span></div><Progress value={course.progress || 0}/><p className="lms-detail-note">Lessons count as complete only after you select “Mark as complete”.</p></DetailPanel>
      <DetailPanel title="Course information"><div className="kv"><span>Category</span><b>{course.category || "General"}</b></div><div className="kv"><span>Trainer</span><b>{course.trainer_name || "Not assigned"}</b></div><div className="kv"><span>Delivery language</span><b>{course.language || "English"}</b></div><div className="kv"><span>Enrolment</span><Badge tone={enrolled ? "success" : course.access_type === "PAID" ? "warning" : "info"}>{enrolled ? "Enrolled" : course.access_type === "PAID" ? "Admin assignment" : "Open enrolment"}</Badge></div></DetailPanel>
    </div>
    <div className="detail-grid">
      <DetailPanel title="What you will learn">{outcomes.length ? <ul className="lms-outcome-list">{outcomes.map((x, i) => <li key={i}><CheckCircle2 size={14}/>{x}</li>)}</ul> : <p className="muted-text">Learning outcomes have not been added yet.</p>}</DetailPanel>
      <DetailPanel title="Prerequisites"><p className="lesson-content">{course.prerequisites || "No prerequisites specified."}</p></DetailPanel>
    </div>
    <DetailPanel title="Course syllabus"><div className="module-list">{modules.length ? modules.map((m) => <section className="module-item" key={m.id}><div><div className="module-number">{m.order}</div><div><h3>{m.title}</h3><p>{m.description || "Module overview"}</p></div></div><div className="lesson-list">{m.lessons?.length ? m.lessons.map((l) => <button key={l.id} onClick={() => enrolled && nav(`/courses/${id}/lessons/${l.id}`)} className={`lesson-row ${!enrolled ? "locked" : ""}`} disabled={!enrolled}><span>{enrolled && l.completed ? <CheckCircle2 size={16}/> : <PlayCircle size={16}/>} {l.title}</span><small>{l.duration_minutes ? `${l.duration_minutes} min` : "Lesson"}</small></button>) : <span className="muted-text">Lesson titles will be available after course access is granted.</span>}</div>{enrolled && <div className="lms-activity-links">{(m.assessments || []).map((a) => <button key={a.id} onClick={() => nav(`/assessments/${a.id}`)}><CheckCircle2 size={13}/> {a.title}</button>)}{(m.assignments || []).map((a) => <button key={a.id} onClick={() => nav(`/assignments/${a.id}`)}><BookOpen size={13}/> {a.title}</button>)}</div>}</section>) : <Empty title="No syllabus yet" text="The course administrator has not added modules yet."/>}</div></DetailPanel>
  </div>;
}
