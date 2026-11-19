import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, CheckCircle2, ChevronDown, ChevronRight,
  Clock3, Download, FileText, Lock, PlayCircle, Video,
} from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { DetailPanel, Badge } from "../../components/ModuleCard";
import { ErrorState, Loading } from "../../components/AsyncState";
import { errorMessage, get, getProtectedBlob, post, downloadProtectedFile } from "../../services/api";
import "./Lesson.css";

function youtubeEmbed(url) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes("youtu.be")) return `https://www.youtube.com/embed/${parsed.pathname.slice(1)}`;
    if (parsed.hostname.includes("youtube.com")) {
      const id = parsed.searchParams.get("v") || parsed.pathname.split("/").filter(Boolean).pop();
      if (id) return `https://www.youtube.com/embed/${id}`;
    }
    if (parsed.hostname.includes("vimeo.com")) {
      const id = parsed.pathname.split("/").filter(Boolean).pop();
      if (id) return `https://player.vimeo.com/video/${id}`;
    }
  } catch { return ""; }
  return "";
}
function looksLikeVideo(url) { return /\.(mp4|webm|ogg|mov)(\?.*)?$/i.test(url || ""); }

export default function Lesson() {
  const { courseId, lessonId } = useParams(), nav = useNavigate();
  const [course, setCourse] = useState(null), [modules, setModules] = useState([]), [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true), [error, setError] = useState(""), [saved, setSaved] = useState(false);
  const [videoBlobUrl, setVideoBlobUrl] = useState("");
  const playerRef = useRef(null), lastSavedRef = useRef(0);

  const orderedLessons = useMemo(() => modules.flatMap((module) => (module.lessons || []).map((item) => ({ ...item, moduleTitle: module.title, moduleId: module.id }))), [modules]);
  const currentIndex = orderedLessons.findIndex((x) => String(x.id) === String(lessonId));
  const previous = currentIndex > 0 ? orderedLessons[currentIndex - 1] : null;
  const next = currentIndex >= 0 && currentIndex < orderedLessons.length - 1 ? orderedLessons[currentIndex + 1] : null;

  const load = async () => {
    setLoading(true); setError("");
    try {
      const [c, moduleRows] = await Promise.all([get(`/courses/${courseId}/`), get(`/courses/${courseId}/modules/`)]);
      const found = moduleRows.flatMap((module) => (module.lessons || []).map((item) => ({ ...item, moduleTitle: module.title, moduleId: module.id }))).find((item) => String(item.id) === String(lessonId));
      if (!found) throw new Error("Lesson not found or not available for your account.");
      setCourse(c); setModules(moduleRows); setLesson(found); lastSavedRef.current = Number(found.last_position_seconds || 0);
      // Record that this lesson was opened without marking it complete.
      post(`/courses/lessons/${found.id}/progress/`, { position_seconds: Number(found.last_position_seconds || 0) }).catch(() => {});
    } catch (e) { setError(errorMessage(e, "Unable to load this lesson.")); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [courseId, lessonId]);

  useEffect(() => {
    let active = true, objectUrl = "";
    if (!lesson?.video_file_url) { setVideoBlobUrl(""); return undefined; }
    getProtectedBlob(lesson.video_file_url).then((blob) => {
      if (!active) return;
      objectUrl = window.URL.createObjectURL(blob); setVideoBlobUrl(objectUrl);
    }).catch((e) => active && setError(errorMessage(e, "Unable to load this lesson video.")));
    return () => { active = false; if (objectUrl) window.URL.revokeObjectURL(objectUrl); };
  }, [lesson?.id, lesson?.video_file_url]);

  const savePosition = async (position) => {
    const safePosition = Math.max(0, Math.floor(Number(position || 0)));
    if (Math.abs(safePosition - lastSavedRef.current) < 5) return;
    lastSavedRef.current = safePosition;
    try { await post(`/courses/lessons/${lessonId}/progress/`, { position_seconds: safePosition }); }
    catch { /* Progress save failures should not stop lesson playback. */ }
  };
  const onVideoTime = (event) => {
    const current = event.currentTarget.currentTime || 0;
    if (Math.abs(Math.floor(current) - lastSavedRef.current) >= 10) savePosition(current);
  };
  const onVideoLoaded = (event) => {
    const position = Number(lesson?.last_position_seconds || 0);
    if (position > 0 && event.currentTarget.duration > position + 2) event.currentTarget.currentTime = position;
  };
  const complete = async () => {
    try { await post(`/courses/lessons/${lessonId}/complete/`); setSaved(true); await load(); }
    catch (e) { setError(errorMessage(e)); }
  };
  const openLesson = (item) => nav(`/courses/${courseId}/lessons/${item.id}`);
  const download = async (url, name) => {
    try { await downloadProtectedFile(url, name); }
    catch (e) { setError(errorMessage(e, "Unable to download this note.")); }
  };

  if (loading) return <Loading text="Loading lesson..."/>;
  if (error && !lesson) return <ErrorState text={error} onRetry={load}/>;
  const embedUrl = lesson.video_url ? youtubeEmbed(lesson.video_url) : "";
  const directHostedVideo = lesson.video_url && !embedUrl && looksLikeVideo(lesson.video_url);
  const useVideo = Boolean(videoBlobUrl || directHostedVideo);
  const resources = [...(lesson.resources || [])];
  if (lesson.resource_url) resources.unshift({ id: `legacy-${lesson.id}`, title: "Lesson resource", file_url: lesson.resource_url });

  return <div className="lms-lesson-page">
    <button className="back-link" onClick={() => nav(`/courses/${courseId}`)}><ArrowLeft size={15}/> {course.title}</button>
    <div className="lms-lesson-topline"><div><span>{course.title}</span><b>{Number(course.progress || 0)}% course progress</b></div><div className="lms-lesson-top-progress"><i><b style={{ width: `${course.progress || 0}%` }}/></i></div></div>
    {error && <div className="form-error">{error}</div>}
    <div className="lms-learning-layout">
      <aside className="lms-learning-sidebar"><div className="lms-learning-sidebar-head"><div><span>COURSE CONTENT</span><b>{modules.length} modules</b></div><button className="icon-button" onClick={() => nav(`/courses/${courseId}`)}><ChevronDown size={15}/></button></div>
        {modules.map((module) => <section className="lms-sidebar-module" key={module.id}><h4><span>{module.order}. {module.title}</span><small>{(module.lessons || []).filter((x) => x.completed).length}/{(module.lessons || []).length}</small></h4>{(module.lessons || []).map((item) => <button key={item.id} className={`lms-sidebar-lesson ${String(item.id) === String(lessonId) ? "current" : ""}`} onClick={() => openLesson(item)}><span>{item.completed ? <CheckCircle2 size={14}/> : <PlayCircle size={14}/>}<b>{item.title}</b></span><small>{item.duration_minutes ? `${item.duration_minutes}m` : ""}</small></button>)}</section>)}
      </aside>
      <main className="lms-lesson-main">
        <div className="lms-lesson-heading"><div><span>{lesson.moduleTitle}</span><h1>{lesson.title}</h1><p>{lesson.description || "Work through this lesson, review the downloadable notes, and complete the practice activity."}</p></div><Badge tone={lesson.completed ? "success" : "info"}>{lesson.completed ? "Completed" : "In progress"}</Badge></div>
        {(lesson.video_file_url || lesson.video_url) ? <DetailPanel title="Lesson video"><div className="lms-video-stage">
          {useVideo ? <video ref={playerRef} controls playsInline src={videoBlobUrl || lesson.video_url} onLoadedMetadata={onVideoLoaded} onTimeUpdate={onVideoTime} onPause={(e) => savePosition(e.currentTarget.currentTime)} onEnded={(e) => savePosition(e.currentTarget.currentTime)} /> : embedUrl ? <iframe title={`${lesson.title} video`} src={embedUrl} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen/> : <div className="lms-video-external"><Video size={24}/><p>This lesson uses a hosted video link.</p><a className="primary-btn" href={lesson.video_url} target="_blank" rel="noreferrer">Open video <ArrowRight size={14}/></a></div>}
        </div>{useVideo && lesson.last_position_seconds > 0 && <p className="lms-resume-note">Resume position saved at {Math.floor(lesson.last_position_seconds / 60)}:{String(lesson.last_position_seconds % 60).padStart(2, "0")}.</p>}</DetailPanel> : <div className="lms-text-lesson-banner"><FileText size={21}/><div><b>Text-based lesson</b><span>This lesson does not require a video. Read the explanation and download the notes below.</span></div></div>}
        <DetailPanel title="Lesson explanation"><div className="lesson-content lms-lesson-content">{lesson.content ? <div style={{ whiteSpace: "pre-wrap" }}>{lesson.content}</div> : <p className="muted-text">No written explanation has been added for this lesson.</p>}</div></DetailPanel>
        <DetailPanel title="Lesson notes & downloads"><p className="lms-detail-note">Download the files provided by your trainer. Supported materials may include PDF, PPT, DOCX, source code and practice files.</p>{resources.length ? <div className="lms-resource-list">{resources.map((resource) => <div className="lms-resource-row" key={resource.id}><div><FileText size={17}/><span><b>{resource.title}</b><small>Course learning material</small></span></div><button className="outline-btn small" onClick={() => download(resource.file_url, resource.title || "course-note")}><Download size={14}/> Download</button></div>)}</div> : <p className="muted-text">No downloadable notes have been attached to this lesson.</p>}</DetailPanel>
        {(lesson.assessments?.length || lesson.assignments?.length || modules.find((m) => m.id === lesson.moduleId)?.assessments?.length || modules.find((m) => m.id === lesson.moduleId)?.assignments?.length) ? <DetailPanel title="Practice & assessments"><div className="lms-practice-links">{(modules.find((m) => m.id === lesson.moduleId)?.assessments || []).map((a) => <button key={`a${a.id}`} onClick={() => nav(`/assessments/${a.id}`)}><span><CheckCircle2 size={16}/><b>{a.title}</b><small>{a.assessment_type} · {a.duration_minutes} min · {a.total_marks} marks</small></span><ChevronRight size={16}/></button>)}{(modules.find((m) => m.id === lesson.moduleId)?.assignments || []).map((a) => <button key={`t${a.id}`} onClick={() => nav(`/assignments/${a.id}`)}><span><FileText size={16}/><b>{a.title}</b><small>Assignment · {a.max_marks} marks</small></span><ChevronRight size={16}/></button>)}</div></DetailPanel> : null}
        <div className="lms-lesson-bottom"><button className="outline-btn" disabled={!previous} onClick={() => previous && openLesson(previous)}><ArrowLeft size={14}/> Previous lesson</button><div>{lesson.completed ? <span className="lms-complete-label"><CheckCircle2 size={15}/> Completed</span> : <button className="primary-btn" onClick={complete}><CheckCircle2 size={15}/> Mark as complete</button>}</div><button className="primary-btn" disabled={!next} onClick={() => next && openLesson(next)}>Next lesson <ArrowRight size={14}/></button></div>
      </main>
    </div>
  </div>;
}
