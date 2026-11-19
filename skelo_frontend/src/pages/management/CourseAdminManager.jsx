import React, { useEffect, useMemo, useState } from "react";
import {
  Archive, ArrowDown, ArrowLeft, ArrowUp, BookOpen, CheckCircle2,
  ClipboardCheck, Download, Edit3, Eye, FileText, Layers, Link2,
  ListChecks, Plus, Search, Trash2, Upload, Users, Video, X,
} from "lucide-react";
import { Badge, DetailPanel } from "../../components/ModuleCard";
import { Empty, ErrorState, Loading } from "../../components/AsyncState";
import PageHeader from "../../components/PageHeader";
import { del, downloadProtectedFile, errorMessage, get, patch, post, unwrapList } from "../../services/api";
import "./CourseAdminManager.css";

const blankCourse = {
  title: "", slug: "", description: "", category: "", level: "BEGINNER",
  language: "English", learning_outcomes: "", prerequisites: "",
  access_type: "FREE", price: "0", minimum_quiz_percentage: "70", require_assignment_approval: false, duration_minutes: "", thumbnail: null,
};
const blankModule = { title: "", description: "", order: 1 };
const blankLesson = {
  module_id: "", title: "", description: "", content: "", video_url: "",
  video_file: null, order: 1, duration_minutes: 0, is_published: true,
};

function Field({ label, children, className = "" }) {
  return <label className={`lms-field ${className}`}><span>{label}</span>{children}</label>;
}
function Stat({ label, value, icon: Icon }) {
  return <div className="lms-stat"><span><Icon size={16}/>{label}</span><strong>{value}</strong></div>;
}
function asFormData(values) {
  const fd = new FormData();
  Object.entries(values).forEach(([key, value]) => {
    if (value === null || value === undefined) return;
    fd.append(key, value);
  });
  return fd;
}

export default function CourseAdminManager() {
  const [courses, setCourses] = useState([]);
  const [query, setQuery] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [courseStats, setCourseStats] = useState({ total: 0, published: 0, drafts: 0, archived: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState(null);
  const [modules, setModules] = useState([]);
  const [courseForm, setCourseForm] = useState(blankCourse);
  const [courseEditing, setCourseEditing] = useState(false);
  const [courseFormOpen, setCourseFormOpen] = useState(false);
  const [courseSaving, setCourseSaving] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [moduleForm, setModuleForm] = useState(blankModule);
  const [moduleEditing, setModuleEditing] = useState(null);
  const [lessonForm, setLessonForm] = useState(blankLesson);
  const [lessonEditing, setLessonEditing] = useState(null);
  const [lessonResources, setLessonResources] = useState([]);
  const [savedLessonResources, setSavedLessonResources] = useState([]);
  const [activityData, setActivityData] = useState({ assessments: [], assignments: [] });
  const [linkSelection, setLinkSelection] = useState({});
  const [workspaceTab, setWorkspaceTab] = useState("Curriculum");
  const [batches, setBatches] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedBatchIds, setSelectedBatchIds] = useState([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState([]);
  const [expiresOn, setExpiresOn] = useState("");
  const [batchForm, setBatchForm] = useState({ name: "", code: "", description: "" });
  const [batchStudentIds, setBatchStudentIds] = useState([]);
  const [report, setReport] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const filteredCourses = useMemo(() => courses.filter((c) =>
    `${c.title} ${c.category} ${c.level}`.toLowerCase().includes(query.toLowerCase())
  ), [courses, query]);

  const loadCourses = async () => {
    setLoading(true); setError("");
    try {
      const [activeRows, archivedRows] = await Promise.all([
        get("/courses/?page_size=200"),
        get("/courses/?page_size=200&archived=true"),
      ]);
      const active = unwrapList(activeRows), archived = unwrapList(archivedRows);
      setCourseStats({
        total: active.length + archived.length,
        published: active.filter((course) => course.is_published).length,
        drafts: active.filter((course) => !course.is_published).length,
        archived: archived.length,
      });
      setCourses(showArchived ? archived : active);
    } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  };
  useEffect(() => { loadCourses(); }, [showArchived]);

  const loadWorkspace = async (course) => {
    setSelected(course); setError(""); setNotice(""); setWorkspaceTab("Curriculum");
    setLessonForm({ ...blankLesson, order: 1 }); setLessonEditing(null);
    try {
      const [moduleRows, assessmentRows, assignmentRows, batchRows, studentRows] = await Promise.all([
        get(`/courses/${course.id}/modules/`),
        get("/assessments/?page_size=200").catch(() => []),
        get("/assignments/?page_size=200").catch(() => []),
        get("/courses/batches/").catch(() => []),
        get("/courses/admin/students/").catch(() => []),
      ]);
      const loadedModules = unwrapList(moduleRows);
      setModules(loadedModules);
      setModuleForm({ ...blankModule, order: Math.max(0, ...loadedModules.map((row) => Number(row.order) || 0)) + 1 });
      setActivityData({ assessments: unwrapList(assessmentRows), assignments: unwrapList(assignmentRows) });
      setBatches(unwrapList(batchRows)); setStudents(unwrapList(studentRows));
      const reportData = await get(`/courses/${course.id}/report/`).catch(() => null);
      setReport(reportData);
      const assignmentData = await get(`/courses/${course.id}/assignments/`).catch(() => null);
      setSelectedBatchIds(assignmentData?.batches?.map((x) => x.id) || []);
      setSelectedStudentIds((assignmentData?.enrollments || []).filter((x) => x.source === "INDIVIDUAL").map((x) => x.student_id).filter(Boolean));
      const expiries = [
        ...(assignmentData?.batches || []).map((x) => x.access_expires_at),
        ...(assignmentData?.enrollments || []).map((x) => x.access_expires_at),
      ].filter(Boolean);
      setExpiresOn(expiries[0] ? String(expiries[0]).slice(0, 10) : "");
    } catch (e) { setError(errorMessage(e)); }
  };

  const newCourse = () => {
    setSelected(null); setModules([]); setCourseEditing(false); setCourseFormOpen(true); setCourseForm(blankCourse);
    setError(""); setNotice(""); window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const editCourse = (course) => {
    setSelected(course); setCourseEditing(true); setCourseFormOpen(true);
    setCourseForm({ ...blankCourse, ...course, thumbnail: null, price: String(course.price ?? 0), duration_minutes: String(course.duration_minutes || "") });
    setError(""); setNotice(""); window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const updateCourseField = (e) => {
    const { name, value, files } = e.target;
    setCourseForm((old) => ({ ...old, [name]: name === "thumbnail" ? (files?.[0] || null) : value }));
  };
  const saveCourse = async (e) => {
    e.preventDefault(); setCourseSaving(true); setError(""); setNotice("");
    try {
      const fd = asFormData({ ...courseForm, duration_minutes: Number(courseForm.duration_minutes || 0), price: Number(courseForm.price || 0) });
      if (selected && courseEditing && !String(courseForm.slug || "").trim()) fd.delete("slug");
      const saved = selected && courseEditing
        ? await patch(`/courses/${selected.id}/`, fd, { timeout: 0 })
        : await post("/courses/", fd, { timeout: 0 });
      setNotice(selected && courseEditing ? "Course details updated." : "Course created as a draft. Add its curriculum before publishing.");
      setCourseEditing(false); setCourseFormOpen(false); setCourseForm({ ...blankCourse });
      await loadCourses(); await loadWorkspace(saved);
    } catch (e2) { setError(errorMessage(e2)); }
    finally { setCourseSaving(false); }
  };
  const togglePublish = async (course) => {
    try {
      const updated = await patch(`/courses/${course.id}/`, { is_published: !course.is_published });
      setNotice(updated.is_published ? "Course published and visible in the student catalogue." : "Course unpublished. Existing learning records are preserved.");
      await loadCourses(); if (selected?.id === course.id) setSelected(updated);
    } catch (e) { setError(errorMessage(e)); }
  };
  const archiveCourse = async (course) => {
    if (!window.confirm(`Archive “${course.title}”? Student enrolments and progress will be preserved.`)) return;
    try { await del(`/courses/${course.id}/`); setNotice("Course archived. Learning records were preserved."); setSelected(null); await loadCourses(); }
    catch (e) { setError(errorMessage(e)); }
  };

  const refreshModules = async () => {
    if (!selected) return;
    setModules(unwrapList(await get(`/courses/${selected.id}/modules/`)));
  };
  const saveModule = async (e) => {
    e.preventDefault(); if (!selected) return;
    try {
      const wasEditing = Boolean(moduleEditing);
      if (moduleEditing) await patch(`/courses/${selected.id}/modules/`, { ...moduleForm, id: moduleEditing });
      else await post(`/courses/${selected.id}/modules/`, { ...moduleForm, order: Math.max(0, ...modules.map((row) => Number(row.order) || 0)) + 1 });
      setModuleForm({ ...blankModule, order: Math.max(0, ...modules.map((row) => Number(row.order) || 0)) + (wasEditing ? 1 : 2) });
      setModuleEditing(null); await refreshModules(); setNotice(wasEditing ? "Module updated." : "Module added.");
    } catch (e2) { setError(errorMessage(e2)); }
  };
  const editModule = (module) => { setModuleEditing(module.id); setModuleForm({ title: module.title, description: module.description || "", order: module.order }); };
  const removeModule = async (module) => {
    if (!window.confirm(`Delete “${module.title}” and its lessons?`)) return;
    try { await del(`/courses/${selected.id}/modules/`, { data: { id: module.id } }); await refreshModules(); setNotice("Module removed."); }
    catch (e) { setError(errorMessage(e)); }
  };
  const moveModule = async (module, direction) => {
    const index = modules.findIndex((m) => m.id === module.id), target = modules[index + direction];
    if (!target) return;
    try {
      // Course modules have a unique (course, order) constraint, so use a
      // temporary free position to avoid violating it during a swap.
      const temporaryOrder = Math.max(0, ...modules.map((row) => Number(row.order) || 0)) + 1;
      await patch(`/courses/${selected.id}/modules/`, { id: module.id, order: temporaryOrder });
      await patch(`/courses/${selected.id}/modules/`, { id: target.id, order: module.order });
      await patch(`/courses/${selected.id}/modules/`, { id: module.id, order: target.order });
      await refreshModules();
    } catch (e) { setError(errorMessage(e)); }
  };

  const openNewLesson = (module) => {
    setLessonEditing(null); setLessonResources([]); setSavedLessonResources([]);
    setLessonForm({ ...blankLesson, module_id: String(module.id), order: (module.lessons?.length || 0) + 1 });
  };
  const editLesson = (module, lesson) => {
    setLessonEditing(lesson.id); setLessonResources([]); setSavedLessonResources(lesson.resources || []);
    setLessonForm({ ...blankLesson, ...lesson, module_id: String(module.id), video_file: null });
  };
  const removeSavedLessonResource = async (resource) => {
    if (!window.confirm(`Remove note “${resource.title}”?`)) return;
    try {
      await del(`/courses/lessons/${lessonEditing}/resources/`, { data: { id: resource.id } });
      setSavedLessonResources((old) => old.filter((item) => item.id !== resource.id));
      setNotice("Lesson note removed.");
    } catch (e) { setError(errorMessage(e)); }
  };
  const downloadLessonNote = async (resource) => {
    try { await downloadProtectedFile(resource.file_url, resource.title); }
    catch (e) { setError(errorMessage(e, "Unable to download this note.")); }
  };
  const updateLessonField = (e) => {
    const { name, value, type, checked, files } = e.target;
    setLessonForm((old) => ({ ...old, [name]: type === "checkbox" ? checked : name === "video_file" ? (files?.[0] || null) : value }));
  };
  const saveLesson = async (e) => {
    e.preventDefault(); if (!selected) return;
    setError("");
    try {
      const hasUploads = Boolean(lessonForm.video_file || lessonResources.length);
      setUploadProgress(hasUploads ? 0 : null);
      const uploadConfig = {
        timeout: 0,
        onUploadProgress: (event) => {
          if (event.total) setUploadProgress(Math.round((event.loaded / event.total) * 100));
        },
      };
      const fd = asFormData({ ...lessonForm, order: Number(lessonForm.order || 1), duration_minutes: Number(lessonForm.duration_minutes || 0), is_published: Boolean(lessonForm.is_published) });
      let saved;
      if (lessonEditing) {
        fd.append("id", String(lessonEditing));
        saved = await patch(`/courses/${selected.id}/lessons/`, fd, uploadConfig);
      } else saved = await post(`/courses/${selected.id}/lessons/`, fd, uploadConfig);
      if (lessonForm.video_file) setLessonForm((old) => ({ ...old, video_file: null }));
      for (const file of [...lessonResources]) {
        const resourceFd = new FormData(); resourceFd.append("file", file); resourceFd.append("title", file.name);
        await post(`/courses/lessons/${saved.id}/resources/`, resourceFd, uploadConfig);
        setLessonResources((old) => old.filter((pending) => pending !== file));
      }
      setUploadProgress(null);
      setLessonForm(blankLesson); setLessonEditing(null); setLessonResources([]); setSavedLessonResources([]);
      await refreshModules(); setNotice(lessonEditing ? "Lesson updated." : "Lesson added with its learning content.");
    } catch (e2) { setUploadProgress(null); setError(errorMessage(e2)); }
  };
  const removeLesson = async (lesson) => {
    if (!window.confirm(`Delete lesson “${lesson.title}”?`)) return;
    try { await del(`/courses/${selected.id}/lessons/`, { data: { id: lesson.id } }); await refreshModules(); setNotice("Lesson deleted."); }
    catch (e) { setError(errorMessage(e)); }
  };
  const moveLesson = async (module, lesson, direction) => {
    const rows = module.lessons || [], index = rows.findIndex((x) => x.id === lesson.id), target = rows[index + direction];
    if (!target) return;
    try {
      await Promise.all([
        patch(`/courses/${selected.id}/lessons/`, { id: lesson.id, order: target.order }),
        patch(`/courses/${selected.id}/lessons/`, { id: target.id, order: lesson.order }),
      ]); await refreshModules();
    } catch (e) { setError(errorMessage(e)); }
  };
  const linkActivity = async (module, kind) => {
    const activityId = linkSelection[`${module.id}:${kind}`];
    if (!activityId) return;
    try {
      await post(`/courses/${selected.id}/modules/${module.id}/activities/`, { kind, activity_id: Number(activityId) });
      await refreshModules(); setNotice(`${kind === "assessment" ? "Assessment" : "Assignment"} linked to ${module.title}.`);
    } catch (e) { setError(errorMessage(e)); }
  };
  const unlinkActivity = async (module, kind, activityId) => {
    try {
      await del(`/courses/${selected.id}/modules/${module.id}/activities/`, { data: { kind, activity_id: activityId } });
      await refreshModules();
    } catch (e) { setError(errorMessage(e)); }
  };

  const createBatch = async (e) => {
    e.preventDefault();
    try {
      const batch = await post("/courses/batches/", { ...batchForm, student_ids: batchStudentIds });
      setBatches((old) => [...old, batch]); setBatchForm({ name: "", code: "", description: "" }); setBatchStudentIds([]); setNotice(`Batch “${batch.name}” created.`);
    } catch (e2) { setError(errorMessage(e2)); }
  };
  const assignCourse = async () => {
    try {
      const access_expires_at = expiresOn ? new Date(`${expiresOn}T23:59:59`).toISOString() : null;
      await post(`/courses/${selected.id}/assignments/`, { student_ids: selectedStudentIds, batch_ids: selectedBatchIds, access_expires_at });
      setNotice("Course access assigned to the selected students and batches.");
      const assignmentData = await get(`/courses/${selected.id}/assignments/`);
      setSelectedStudentIds((assignmentData.enrollments || []).filter((x) => x.source === "INDIVIDUAL").map((x) => x.student_id).filter(Boolean));
      const rep = await get(`/courses/${selected.id}/report/`); setReport(rep);
    } catch (e) { setError(errorMessage(e)); }
  };
  const loadReport = async () => { try { setReport(await get(`/courses/${selected.id}/report/`)); } catch (e) { setError(errorMessage(e)); } };

  return <div className="lms-admin-page">
    <PageHeader eyebrow="SKelo · COURSE STUDIO" title="Course Learning Management" subtitle="Build course content, organise lessons and notes, assign students or batches, and monitor learning progress." action={<button className="primary-btn" onClick={newCourse}><Plus size={16}/> Create course</button>}/>
    {notice && <div className="success-box"><CheckCircle2 size={14}/>{notice}</div>}
    {error && <div className="lms-inline-error">{error}<button onClick={() => setError("")}><X size={14}/></button></div>}

    {courseFormOpen && <DetailPanel title={courseEditing ? `Edit course · ${selected?.title || ""}` : "Create a course"}>
      <form className="lms-form-grid" onSubmit={saveCourse}>
        <Field label="Course title"><input name="title" value={courseForm.title} onChange={updateCourseField} required placeholder="e.g. Java Basics"/></Field>
        <Field label="URL slug (optional)"><input name="slug" value={courseForm.slug} onChange={updateCourseField} placeholder="java-basics"/></Field>
        <Field label="Category"><input name="category" value={courseForm.category} onChange={updateCourseField} placeholder="Programming"/></Field>
        <Field label="Level"><select name="level" value={courseForm.level} onChange={updateCourseField}><option value="BEGINNER">Beginner</option><option value="INTERMEDIATE">Intermediate</option><option value="ADVANCED">Advanced</option></select></Field>
        <Field label="Delivery language"><input name="language" value={courseForm.language} onChange={updateCourseField} placeholder="English"/></Field>
        <Field label="Duration (minutes)"><input name="duration_minutes" type="number" min="0" value={courseForm.duration_minutes} onChange={updateCourseField}/></Field>
        <Field label="Access type"><select name="access_type" value={courseForm.access_type} onChange={updateCourseField}><option value="FREE">Free</option><option value="PAID">Paid (manual access only)</option></select></Field>
        <Field label="Price (₹)"><input name="price" type="number" min="0" step="0.01" value={courseForm.price} onChange={updateCourseField} disabled={courseForm.access_type === "FREE"}/></Field>
        <Field label="Minimum quiz score for completion (%)"><input name="minimum_quiz_percentage" type="number" min="0" max="100" step="0.5" value={courseForm.minimum_quiz_percentage} onChange={updateCourseField}/></Field>
        <Field label="Course thumbnail" className="lms-file-field"><input name="thumbnail" type="file" accept="image/*" onChange={updateCourseField}/></Field>
        <Field label="Description" className="full-span"><textarea name="description" value={courseForm.description} onChange={updateCourseField} rows="3" placeholder="What students will learn in this course..."/></Field>
        <Field label="Learning outcomes · one per line" className="full-span"><textarea name="learning_outcomes" value={courseForm.learning_outcomes} onChange={updateCourseField} rows="3"/></Field>
        <Field label="Prerequisites" className="full-span"><textarea name="prerequisites" value={courseForm.prerequisites} onChange={updateCourseField} rows="2"/></Field>
        <label className="lms-check full-span"><input type="checkbox" name="require_assignment_approval" checked={Boolean(courseForm.require_assignment_approval)} onChange={(e) => setCourseForm((old) => ({ ...old, require_assignment_approval: e.target.checked }))}/> Require all linked assignments to be evaluated before course completion</label>
        <div className="lms-form-actions full-span"><button className="primary-btn" disabled={courseSaving}>{courseSaving ? "Saving..." : courseEditing ? "Save changes" : "Create course draft"}</button><button type="button" className="outline-btn" onClick={() => { setCourseEditing(false); setCourseFormOpen(false); setCourseForm(blankCourse); }}>Cancel</button></div>
        {courseForm.access_type === "PAID" && <p className="lms-hint full-span">Online checkout is not configured. Paid courses can only be opened after an administrator assigns access.</p>}
      </form>
    </DetailPanel>}

    {!selected && <>
      <div className="lms-admin-stats">
        <Stat label="Total courses" value={courseStats.total} icon={BookOpen}/>
        <Stat label="Published" value={courseStats.published} icon={CheckCircle2}/>
        <Stat label="Drafts" value={courseStats.drafts} icon={Edit3}/>
        <Stat label="Archived" value={courseStats.archived} icon={Archive}/>
      </div>
      <DetailPanel title="Course catalogue management">
        <div className="lms-course-list-toolbar"><label className="lms-search"><Search size={15}/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search courses..."/></label><div className="lms-course-list-tools"><span>{filteredCourses.length} {showArchived ? "archived" : "active"} courses</span><button className="outline-btn small" onClick={() => setShowArchived((value) => !value)}>{showArchived ? "Show active courses" : "Show archived"}</button></div></div>
        {loading ? <Loading text="Loading course catalogue..."/> : error && !courses.length ? <ErrorState text={error} onRetry={loadCourses}/> : !filteredCourses.length ? <Empty title="No courses created yet" text="Create your first course to begin building its modules and lessons."/> :
          <div className="lms-admin-course-list">{filteredCourses.map((course) => <article className="lms-admin-course" key={course.id}>
            <div className="lms-admin-course-icon"><BookOpen size={21}/></div>
            <div className="lms-admin-course-copy"><div><h3>{course.title}</h3><Badge tone={course.is_published ? "success" : "muted"}>{course.is_archived ? "Archived" : course.is_published ? "Published" : "Draft"}</Badge></div><p>{course.category || "General"} · {course.level} · {course.language || "English"} · {course.lessons || 0} lessons</p></div>
            <div className="lms-admin-course-actions"><button className="outline-btn small" onClick={() => loadWorkspace(course)}><Layers size={14}/> Manage</button><button className="icon-button" title="Edit course details" onClick={() => editCourse(course)}><Edit3 size={15}/></button>{course.is_archived ? <button className="outline-btn small" onClick={async () => { try { await patch(`/courses/${course.id}/`, { is_archived: false }); setNotice("Course restored as an unpublished draft. Existing learning records remain available."); await loadCourses(); } catch (e) { setError(errorMessage(e)); } }}>Restore</button> : <><button className="icon-button" title={course.is_published ? "Unpublish" : "Publish"} onClick={() => togglePublish(course)}><Eye size={15}/></button><button className="icon-button danger" title="Archive course" onClick={() => archiveCourse(course)}><Archive size={15}/></button></>}</div>
          </article>)}</div>}
      </DetailPanel>
    </>}

    {selected && <>
      <button className="back-link" onClick={() => { setSelected(null); setCourseEditing(false); loadCourses(); }}><ArrowLeft size={15}/> All courses</button>
      <div className="lms-workspace-heading"><div><span>COURSE WORKSPACE</span><h2>{selected.title}</h2><p>{selected.description || "Add a description to help students understand this course."}</p></div><div className="lms-workspace-actions"><Badge tone={selected.is_published ? "success" : "muted"}>{selected.is_published ? "Published" : "Draft"}</Badge><button className="outline-btn small" onClick={() => editCourse(selected)}><Edit3 size={14}/> Edit details</button><button className="outline-btn small" onClick={() => setPreviewOpen(true)}><Eye size={14}/> Preview</button><button className="primary-btn small" onClick={() => togglePublish(selected)}>{selected.is_published ? "Unpublish" : "Publish"}</button></div></div>
      <div className="lms-workspace-tabs">{["Curriculum", "Assignments & batches", "Progress report"].map((tab) => <button key={tab} className={workspaceTab === tab ? "active" : ""} onClick={() => { setWorkspaceTab(tab); if (tab === "Progress report") loadReport(); }}>{tab}</button>)}</div>

      {workspaceTab === "Curriculum" && <div className="lms-curriculum-grid">
        <DetailPanel title="Course structure">
          {modules.length ? <div className="lms-module-stack">{modules.map((module, idx) => <section className="lms-module-card" key={module.id}>
            <div className="lms-module-title"><div className="lms-module-order">{module.order}</div><div><h3>{module.title}</h3><p>{module.description || "No module description"}</p></div><div className="lms-row-actions"><button className="icon-button" title="Move up" onClick={() => moveModule(module, -1)} disabled={idx === 0}><ArrowUp size={14}/></button><button className="icon-button" title="Move down" onClick={() => moveModule(module, 1)} disabled={idx === modules.length - 1}><ArrowDown size={14}/></button><button className="icon-button" onClick={() => editModule(module)}><Edit3 size={14}/></button><button className="icon-button danger" onClick={() => removeModule(module)}><Trash2 size={14}/></button></div></div>
            <div className="lms-lesson-stack">{(module.lessons || []).map((lesson, lessonIndex) => <div className="lms-lesson-admin-row" key={lesson.id}><div className="lms-lesson-admin-icon">{lesson.video_url || lesson.video_file_url ? <Video size={15}/> : <FileText size={15}/>}</div><div className="lms-lesson-admin-copy"><b>{lesson.title}</b><span>{lesson.duration_minutes || 0} min · {(lesson.resources || []).length + (lesson.resource_url ? 1 : 0)} notes · {lesson.is_published ? "Visible to students" : "Hidden"}</span></div><div className="lms-row-actions"><button className="icon-button" title="Move up" onClick={() => moveLesson(module, lesson, -1)} disabled={lessonIndex === 0}><ArrowUp size={13}/></button><button className="icon-button" title="Move down" onClick={() => moveLesson(module, lesson, 1)} disabled={lessonIndex === (module.lessons || []).length - 1}><ArrowDown size={13}/></button><button className="icon-button" onClick={() => editLesson(module, lesson)}><Edit3 size={14}/></button><button className="icon-button danger" onClick={() => removeLesson(lesson)}><Trash2 size={14}/></button></div></div>)}</div>
            <div className="lms-linked-activities">{(module.assessments || []).map((a) => <span key={`a${a.id}`}><ClipboardCheck size={12}/>{a.title}</span>)}{(module.assignments || []).map((a) => <span key={`t${a.id}`}><FileText size={12}/>{a.title}</span>)}</div>
            <button className="outline-btn small lms-add-lesson" onClick={() => openNewLesson(module)}><Plus size={13}/> Add lesson</button>
            <div className="lms-link-activity-row"><select value={linkSelection[`${module.id}:assessment`] || ""} onChange={(e) => setLinkSelection((x) => ({ ...x, [`${module.id}:assessment`]: e.target.value }))}><option value="">Link an assessment...</option>{activityData.assessments.map((a) => <option key={a.id} value={a.id}>{a.title}</option>)}</select><button className="outline-btn small" onClick={() => linkActivity(module, "assessment")}><Link2 size={12}/> Link quiz</button><select value={linkSelection[`${module.id}:assignment`] || ""} onChange={(e) => setLinkSelection((x) => ({ ...x, [`${module.id}:assignment`]: e.target.value }))}><option value="">Link an assignment...</option>{activityData.assignments.map((a) => <option key={a.id} value={a.id}>{a.title}</option>)}</select><button className="outline-btn small" onClick={() => linkActivity(module, "assignment")}><Link2 size={12}/> Link task</button></div>
          </section>)}</div> : <Empty title="No modules yet" text="Add a module to create the course syllabus."/>}
        </DetailPanel>
        <div className="lms-editor-stack">
          <DetailPanel title={moduleEditing ? "Edit module" : "Add a module"}>
            <form className="lms-editor-form" onSubmit={saveModule}><Field label="Module title"><input value={moduleForm.title} onChange={(e) => setModuleForm({ ...moduleForm, title: e.target.value })} required placeholder="e.g. Java fundamentals"/></Field><Field label="Description"><textarea rows="2" value={moduleForm.description} onChange={(e) => setModuleForm({ ...moduleForm, description: e.target.value })}/></Field><Field label="Display order (use arrows to reorder)"><input type="number" min="1" value={moduleForm.order} readOnly/></Field><div className="lms-form-actions"><button className="primary-btn small"><Plus size={13}/>{moduleEditing ? "Save module" : "Add module"}</button>{moduleEditing && <button type="button" className="outline-btn small" onClick={() => { setModuleEditing(null); setModuleForm({ ...blankModule, order: Math.max(0, ...modules.map((row) => Number(row.order) || 0)) + 1 }); }}>Cancel</button>}</div></form>
          </DetailPanel>
          <DetailPanel title={lessonEditing ? "Edit lesson" : "Add a lesson"}>
            {!lessonForm.module_id ? <p className="lms-hint">Choose “Add lesson” under a module to attach the lesson to that module.</p> : <form className="lms-editor-form" onSubmit={saveLesson}>
              <Field label="Lesson title"><input name="title" value={lessonForm.title} onChange={updateLessonField} required/></Field>
              <Field label="Module"><select name="module_id" value={lessonForm.module_id} onChange={updateLessonField}>{modules.map((m) => <option value={m.id} key={m.id}>{m.title}</option>)}</select></Field>
              <Field label="Short description"><textarea name="description" rows="2" value={lessonForm.description} onChange={updateLessonField}/></Field>
              <Field label="Lesson explanation / instructions"><textarea name="content" rows="6" value={lessonForm.content} onChange={updateLessonField} placeholder="Written content is optional when a video is provided."/></Field>
              <Field label="Hosted video URL (optional)"><input name="video_url" type="url" value={lessonForm.video_url} onChange={updateLessonField} placeholder="https://..."/></Field>
              <Field label="Upload / replace video (optional)" className="lms-file-field"><input name="video_file" type="file" accept="video/*" onChange={updateLessonField}/></Field>
              <Field label="Lesson notes (PDF, PPT, DOCX, ZIP, code files · max 25 MB each)" className="lms-file-field"><input type="file" multiple onChange={(e) => setLessonResources(Array.from(e.target.files || []))}/></Field>
              {savedLessonResources.length > 0 && <div className="lms-saved-files"><b>Uploaded notes</b>{savedLessonResources.map((resource) => <span key={resource.id}><button type="button" className="lms-saved-file-download" onClick={() => downloadLessonNote(resource)}>{resource.title}</button><button type="button" className="icon-button danger" title="Remove note" onClick={() => removeSavedLessonResource(resource)}><Trash2 size={12}/></button></span>)}</div>}
              {lessonResources.length > 0 && <div className="lms-selected-files">{lessonResources.map((f) => <span key={`${f.name}-${f.size}`}>{f.name}</span>)}</div>}
              {uploadProgress !== null && <div className="lms-upload-progress"><span>Uploading lesson media and notes · {uploadProgress}%</span><i><b style={{ width: `${uploadProgress}%` }}/></i></div>}
              <div className="lms-two-fields"><Field label="Order"><input name="order" type="number" min="1" value={lessonForm.order} onChange={updateLessonField}/></Field><Field label="Duration (minutes)"><input name="duration_minutes" type="number" min="0" value={lessonForm.duration_minutes} onChange={updateLessonField}/></Field></div>
              <label className="lms-check"><input type="checkbox" name="is_published" checked={Boolean(lessonForm.is_published)} onChange={updateLessonField}/> Publish this lesson to enrolled students</label>
              <div className="lms-form-actions"><button className="primary-btn small"><Upload size={13}/>{lessonEditing ? "Save lesson" : "Save lesson"}</button><button type="button" className="outline-btn small" onClick={() => { setLessonForm(blankLesson); setLessonEditing(null); setLessonResources([]); setSavedLessonResources([]); }}>Clear</button></div>
            </form>}
          </DetailPanel>
        </div>
      </div>}

      {workspaceTab === "Assignments & batches" && <div className="lms-assignment-grid">
        <DetailPanel title="Assign this course">
          <p className="lms-hint">Assign access directly to students, or select one or more college batches. Students in selected batches are enrolled automatically.</p>
          <Field label="Access expiry (optional)"><input type="date" value={expiresOn} onChange={(e) => setExpiresOn(e.target.value)}/></Field>
          <h4 className="lms-section-label">College batches</h4>
          <div className="lms-select-list">{batches.length ? batches.map((b) => <label key={b.id}><input type="checkbox" checked={selectedBatchIds.includes(b.id)} onChange={(e) => setSelectedBatchIds((old) => e.target.checked ? [...old, b.id] : old.filter((x) => x !== b.id))}/><span><b>{b.name}</b><small>{b.code} · {b.student_count} students</small></span></label>) : <p className="lms-hint">No batches have been created yet.</p>}</div>
          <h4 className="lms-section-label">Individual students</h4>
          <div className="lms-select-list lms-student-select">{students.map((s) => <label key={s.id}><input type="checkbox" checked={selectedStudentIds.includes(s.id)} onChange={(e) => setSelectedStudentIds((old) => e.target.checked ? [...old, s.id] : old.filter((x) => x !== s.id))}/><span><b>{s.name}</b><small>{s.register_number} · {s.email}</small></span></label>)}</div>
          <button className="primary-btn" onClick={assignCourse}><Users size={15}/> Save course assignments</button>
        </DetailPanel>
        <DetailPanel title="Create / maintain a batch">
          <form className="lms-editor-form" onSubmit={createBatch}><Field label="Batch name"><input value={batchForm.name} onChange={(e) => setBatchForm({ ...batchForm, name: e.target.value })} required placeholder="MCA 2026 - Java"/></Field><Field label="Batch code"><input value={batchForm.code} onChange={(e) => setBatchForm({ ...batchForm, code: e.target.value })} required placeholder="MCA26JAVA"/></Field><Field label="Description"><textarea rows="2" value={batchForm.description} onChange={(e) => setBatchForm({ ...batchForm, description: e.target.value })}/></Field><h4 className="lms-section-label">Add students to this batch</h4><div className="lms-select-list lms-student-select">{students.map((s) => <label key={s.id}><input type="checkbox" checked={batchStudentIds.includes(s.id)} onChange={(e) => setBatchStudentIds((old) => e.target.checked ? [...old, s.id] : old.filter((x) => x !== s.id))}/><span><b>{s.name}</b><small>{s.register_number}</small></span></label>)}</div><button className="primary-btn small"><Plus size={13}/> Create batch</button></form>
          <div className="lms-existing-batches"><h4 className="lms-section-label">Existing batches</h4>{batches.map((b) => <div key={b.id}><span><b>{b.name}</b><small>{b.code} · {b.student_count} students</small></span><button className="icon-button danger" title="Delete batch" onClick={async () => { if (window.confirm(`Delete batch ${b.name}?`)) { try { await del(`/courses/batches/${b.id}/`); setBatches((old) => old.filter((x) => x.id !== b.id)); } catch (e) { setError(errorMessage(e)); } } }}><Trash2 size={14}/></button></div>)}</div>
        </DetailPanel>
      </div>}

      {workspaceTab === "Progress report" && <DetailPanel title="Student learning report">
        {!report ? <Loading text="Loading student progress..."/> : <>
          <div className="lms-admin-stats report"><Stat label="Enrolled" value={report.enrolled_count} icon={Users}/><Stat label="Completed" value={report.completed_count} icon={CheckCircle2}/><Stat label="Inactive · 7 days" value={report.inactive_count} icon={ListChecks}/></div>
          <div className="lms-table-wrap"><table className="lms-report-table"><thead><tr><th>Student</th><th>Register no.</th><th>Progress</th><th>Last activity</th><th>Quizzes</th><th>Assignments</th><th>Status</th><th>Source</th></tr></thead><tbody>{(report.students || []).map((s) => <tr key={s.student_id}><td><b>{s.student}</b><small>{s.email}</small></td><td>{s.register_number}</td><td><div className="lms-progress-cell"><span>{s.progress}%</span><i><b style={{ width: `${s.progress}%` }}/></i></div></td><td>{s.last_activity ? new Date(s.last_activity).toLocaleString() : "—"}</td><td>{(s.quiz_scores || []).length ? s.quiz_scores.map((x) => `${x.title}: ${x.percentage}%`).join(" · ") : "—"}</td><td>{(s.assignment_results || []).length ? s.assignment_results.map((x) => `${x.title}: ${x.marks == null ? x.status : `${x.marks}/${x.max_marks}`}`).join(" · ") : "—"}</td><td><Badge tone={s.completed ? "success" : s.inactive ? "warning" : "info"}>{s.completed ? "Completed" : s.inactive ? "Inactive" : "Learning"}</Badge></td><td>{s.source}</td></tr>)}</tbody></table></div>
          {!report.students?.length && <Empty title="No students enrolled" text="Assign the course to a student or batch to begin tracking progress."/>}
        </>}
      </DetailPanel>}
    </>}

    {previewOpen && selected && <div className="lms-preview-backdrop" onClick={() => setPreviewOpen(false)}><div className="lms-preview-modal" onClick={(e) => e.stopPropagation()}><div className="lms-preview-header"><div><span>STUDENT PREVIEW</span><h2>{selected.title}</h2></div><button className="icon-button" onClick={() => setPreviewOpen(false)}><X size={18}/></button></div><p>{selected.description || "No course description yet."}</p><div className="lms-preview-meta">{selected.level} · {selected.language || "English"} · {selected.access_type === "PAID" ? `₹${selected.price}` : "Free"}</div><h3>Course syllabus</h3>{modules.length ? modules.map((m) => <div className="lms-preview-module" key={m.id}><b>Module {m.order}: {m.title}</b>{(m.lessons || []).map((l) => <span key={l.id}>{l.title} · {l.duration_minutes || 0} min</span>)}</div>) : <p className="lms-hint">No modules added yet.</p>}<button className="primary-btn" onClick={() => setPreviewOpen(false)}>Close preview</button></div></div>}
  </div>;
}
