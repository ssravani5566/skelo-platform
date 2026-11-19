import React, { useEffect, useMemo, useState } from "react";
import { BookOpen, ChevronRight, Clock3, GraduationCap, Search, Languages } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { Empty, ErrorState, Loading } from "../../components/AsyncState";
import { Progress } from "../../components/ModuleCard";
import { errorMessage, get, unwrapList } from "../../services/api";
import "./Courses.css";

export default function Courses() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [tab, setTab] = useState("Catalogue");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const nav = useNavigate();

  const load = async () => {
    setLoading(true); setError("");
    try {
      const path = tab === "My Learning"
        ? "/courses/my-learning/"
        : `/courses/?q=${encodeURIComponent(q)}${filter !== "ALL" ? `&level=${filter}` : ""}`;
      const data = unwrapList(await get(path));
      setItems(tab === "My Learning" ? data.map((row) => ({ ...row.course_detail, enrollment_source: row.source, access_expires_at: row.access_expires_at })) : data);
    } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  };

  useEffect(() => { const id = setTimeout(load, tab === "Catalogue" ? 250 : 0); return () => clearTimeout(id); }, [q, filter, tab]);
  const displayed = useMemo(() => items, [items]);

  return <div className="student-courses-page">
    <PageHeader eyebrow="SKELO · LEARNING" title="Courses" subtitle="Explore structured courses, learn lesson by lesson, and keep your progress saved." action={<button className="outline-btn" onClick={() => setTab("My Learning")}> <GraduationCap size={15}/> My learning</button>}/>
    <div className="lms-student-tabs">{["Catalogue", "My Learning"].map((name) => <button key={name} onClick={() => setTab(name)} className={tab === name ? "active" : ""}>{name}</button>)}</div>
    {tab === "Catalogue" && <div className="module-toolbar"><div className="tabs">{["ALL", "BEGINNER", "INTERMEDIATE", "ADVANCED"].map((x) => <button key={x} className={filter === x ? "active" : ""} onClick={() => setFilter(x)}>{x === "ALL" ? "All levels" : x[0] + x.slice(1).toLowerCase()}</button>)}</div><label className="module-search"><Search size={16}/><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search courses..."/></label></div>}
    {loading ? <Loading text="Loading courses..."/> : error ? <ErrorState text={error} onRetry={load}/> : !displayed.length ? <Empty title={tab === "My Learning" ? "No enrolled courses yet" : "No published courses"} text={tab === "My Learning" ? "Browse the catalogue and enrol in a free course, or ask your college administrator to assign a course." : "New courses will appear here when your faculty or administrator publishes them."}/> :
      <div className="card-grid">{displayed.map((course) => <article className="course-card live-card lms-course-card" key={course.id}>
        <div className="lms-course-cover" style={course.thumbnail_url ? { backgroundImage: `linear-gradient(135deg,#19132b55,#19132b15),url("${course.thumbnail_url}")` } : undefined}><span>{course.category || "Learning"}</span><BookOpen size={25}/></div>
        <div className="card-body"><div className="lms-course-badges"><span>{course.level}</span><span className={course.access_type === "PAID" ? "paid" : "free"}>{course.access_type === "PAID" ? `₹${course.price}` : "Free"}</span></div>
          <div className="card-title-row"><h3>{course.title}</h3>{tab === "My Learning" && <b>{Number(course.progress || 0)}%</b>}</div>
          <p className="lms-course-description">{course.description || "A guided learning path with lessons and practice."}</p>
          <div className="lms-course-meta"><span><Clock3 size={13}/>{course.duration_minutes ? `${Math.ceil(course.duration_minutes / 60)} hrs` : "Self paced"}</span><span><Languages size={13}/>{course.language || "English"}</span><span><BookOpen size={13}/>{course.lessons || 0} lessons</span></div>
          {tab === "My Learning" && <div className="lms-progress-area"><Progress value={course.progress}/><span>{course.completed_lessons || 0} of {course.lessons || 0} lessons completed</span></div>}
          <div className="card-footer"><span>{tab === "My Learning" ? (course.enrolled ? `Assigned: ${course.enrollment_source || "Enrolled"}` : "Access expired · contact admin") : course.enrolled ? "Already enrolled" : course.access_type === "PAID" ? "Admin access required" : "Join this course"}</span><button className="action-link" onClick={() => nav(`/courses/${course.id}`)}>{tab === "My Learning" ? (course.enrolled ? "Continue learning" : "View access details") : "View details"}<ChevronRight size={15}/></button></div>
        </div>
      </article>)}</div>}
  </div>;
}
