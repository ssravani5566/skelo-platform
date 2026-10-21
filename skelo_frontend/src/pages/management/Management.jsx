import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  BarChart3,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  Code2,
  FileText,
  Plus,
  Trash2,
  Users,
  Upload,
  Paperclip,
  Eye,
  X,
} from "lucide-react";

import PageHeader from "../../components/PageHeader";
import CodeathonManager from "./CodeathonManager";
import { Badge, DetailPanel } from "../../components/ModuleCard";
import { ErrorState, Loading } from "../../components/AsyncState";
import {
  errorMessage,
  get,
  patch,
  post,
  del,
  unwrapList,
} from "../../services/api";

const TABS = [
  "Overview",
  "Users",
  "Courses",
  "Assessments",
  "Results",
  "Assignments",
  "Codeathons",
  "Interviews",
  "Attendance",
  "External Coding",
];

const emptyCourse = {
  title: "",
  slug: "",
  description: "",
  category: "",
  level: "BEGINNER",
  duration_minutes: "",
  is_published: false,
  thumbnail: null,
};

const emptyAssessment = {
  title: "",
  description: "",
  assessment_type: "MCQ",
  duration_minutes: 30,
  total_marks: 0,
  passing_marks: 0,
  is_published: false,
  start_at: "",
  end_at: "",
};

const emptyQuestion = {
  text: "",
  question_type: "MCQ",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
  correct_answer: "A",
  explanation: "",
  marks: 1,
  coding_language: "PYTHON",
  starter_code: "",
  input_format: "",
  output_format: "",
  constraints: "",
  test_cases: [{ input: "", output: "" }],
  order: 1,
};

export default function Management() {
  const user = JSON.parse(localStorage.getItem("skelo_user") || "{}");

  const tabs =
    user.role === "ADMIN"
      ? TABS
      : TABS.filter(
          (item) => !["Overview", "Users", "Results"].includes(item)
        );

  const [params, setParams] = useSearchParams();
  const requestedTab = params.get("tab");

  const [tab, setTab] = useState(
    tabs.includes(requestedTab) ? requestedTab : tabs[0]
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [data, setData] = useState([]);
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    if (requestedTab && tabs.includes(requestedTab) && requestedTab !== tab) {
      setTab(requestedTab);
    }
  }, [requestedTab, tab]);

  useEffect(() => {
    load();
  }, [tab]);

  const load = async () => {
    setLoading(true);
    setError("");

    try {
      if (tab === "Overview") {
        setOverview(await get("/dashboard/admin/overview/"));
        return;
      }

      const pathMap = {
        Users: "/auth/users/?page_size=100",
        Courses: "/courses/?page_size=100",
        Assessments: "/assessments/?page_size=100",
        Results: "/assessments/admin/results/",
        Assignments: "/assignments/?page_size=100",
        Codeathons: "/codeathons/?page_size=100",
        Interviews: "/interviews/?page_size=100",
        Attendance: "/attendance/sessions/?page_size=100",
        "External Coding":
          "/coding/problems/?source=external&page_size=100",
      };

      const path = pathMap[tab];

      if (path) {
        setData(unwrapList(await get(path)));
      } else {
        setData([]);
      }
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const done = (text) => {
    setMessage(text);
    load();
  };

  const roleChange = async (id, role) => {
    try {
      await patch(`/auth/users/${id}/`, { role });
      done("User role updated.");
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const selectTab = (nextTab) => {
    setTab(nextTab);
    setParams(nextTab === "Overview" ? {} : { tab: nextTab });
    setMessage("");
    setError("");
  };

  return (
    <div>
      <PageHeader
        eyebrow="SCOTT · ADMIN CONSOLE"
        title="Admin Management"
        subtitle="Create and publish learning content, question papers and student activities from the database."
      />

      <div className="management-tabs">
        {tabs.map((item) => (
          <button
            key={item}
            type="button"
            className={tab === item ? "active" : ""}
            onClick={() => selectTab(item)}
          >
            {item}
          </button>
        ))}
      </div>

      {message && (
        <div className="success-box">
          <CheckCircle2 size={14} />
          {message}
        </div>
      )}

      {loading ? (
        <Loading text={`Loading ${tab.toLowerCase()}...`} />
      ) : error ? (
        <ErrorState text={error} onRetry={load} />
      ) : tab === "Overview" ? (
        <Overview data={overview} />
      ) : tab === "Users" ? (
        <UsersManager data={data} onRole={roleChange} />
      ) : tab === "Courses" ? (
        <CourseManager data={data} onDone={done} />
      ) : tab === "Assessments" ? (
        <AssessmentManager data={data} onDone={done} />
      ) : tab === "Results" ? (
        <ResultsManager data={data} />
      ) : tab === "Assignments" ? (
        <AssignmentManager data={data} onDone={done} />
      ) : tab === "Codeathons" ? (
        <CodeathonManager data={data} onDone={done} />
      ) : tab === "External Coding" ? (
        <ExternalCoding data={data} onDone={done} />
      ) : (
        <SimpleManager tab={tab} data={data} />
      )}
    </div>
  );
}

function Overview({ data }) {
  if (!data) return null;

  const cards = [
    ["Students", data.students, Users],
    ["Courses", data.courses, BookOpen],
    ["Published Courses", data.published_courses, BookOpen],
    ["Assessments", data.assessments, ClipboardCheck],
    ["Questions", data.questions, FileText],
    ["Assessment Attempts", data.attempts, CheckCircle2],
    ["Coding Problems", data.coding_problems, Code2],
    ["Coding Submissions", data.coding_submissions, BarChart3],
    ["Assignments", data.assignments, FileText],
    ["Faculty", data.faculty, Users],
  ];

  return (
    <>
      <div className="card-grid compact">
        {cards.map(([label, value, Icon]) => (
          <DetailPanel key={label}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <div className="assessment-icon">
                <Icon size={20} />
              </div>

              <div>
                <b style={{ fontSize: 22 }}>{value ?? 0}</b>
                <div className="muted-text">{label}</div>
              </div>
            </div>
          </DetailPanel>
        ))}
      </div>

      <DetailPanel title="Admin account">
        <p className="muted-text">
          Use <b>Admin</b> as the Admin ID and <b>Admin@1234</b> as the
          initial password. Change the password from Django Admin before
          production deployment.
        </p>
      </DetailPanel>
    </>
  );
}

function UsersManager({ data, onRole }) {
  return (
    <DetailPanel title={`All users · ${data.length}`}>
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {data.map((user) => (
              <tr key={user.id}>
                <td>
                  <b>{user.name}</b>
                </td>

                <td>{user.email}</td>

                <td>
                  <select
                    value={user.role}
                    onChange={(e) => onRole(user.id, e.target.value)}
                  >
                    <option value="STUDENT">STUDENT</option>
                    <option value="FACULTY">FACULTY</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </td>

                <td>
                  <Badge tone={user.is_active ? "success" : "muted"}>
                    {user.is_active ? "Active" : "Disabled"}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DetailPanel>
  );
}

function CourseManager({ data, onDone }) {
  const [form, setForm] = useState(emptyCourse);
  const [selected, setSelected] = useState(null);
  const [modules, setModules] = useState([]);
  const [module, setModule] = useState({
    title: "",
    description: "",
    order: 1,
  });
  const [lesson, setLesson] = useState({
    module_id: "",
    title: "",
    description: "",
    content: "",
    video_url: "",
    order: 1,
    duration_minutes: 0,
    is_published: true,
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  const change = (e) => {
    const { name, value, type, checked, files } = e.target;

    setForm((current) => ({
      ...current,
      [name]:
        type === "checkbox"
          ? checked
          : name === "thumbnail"
          ? files?.[0] || null
          : value,
    }));
  };

  const create = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErr("");

    try {
      const fd = new FormData();

      Object.entries(form).forEach(([key, value]) => {
        if (value !== null && value !== "") {
          fd.append(key, value);
        }
      });

      const created = await post("/courses/", fd);

      setSelected(created);
      setForm(emptyCourse);

      await refresh(created.id);

      onDone(
        "Course created. Add modules and lessons, then publish it for students."
      );
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const refresh = async (id) => {
    const rows = await get(`/courses/${id}/modules/`);
    setModules(rows);

    setLesson((current) => ({
      ...current,
      module_id: current.module_id || rows[0]?.id || "",
    }));
  };

  const select = async (course) => {
    setSelected(course);
    setForm({
      ...emptyCourse,
      ...course,
      thumbnail: null,
    });

    try {
      await refresh(course.id);
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  const addModule = async (e) => {
    e.preventDefault();

    try {
      await post(`/courses/${selected.id}/modules/`, module);

      setModule({
        title: "",
        description: "",
        order: modules.length + 1,
      });

      await refresh(selected.id);
      onDone("Module added.");
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  const addLesson = async (e) => {
    e.preventDefault();

    try {
      const fd = new FormData();

      Object.entries(lesson).forEach(([key, value]) => {
        if (key !== "module_id" && value !== undefined) {
          fd.append(key, value);
        }
      });

      fd.append("module_id", lesson.module_id);

      await post(`/courses/${selected.id}/lessons/`, fd);

      await refresh(selected.id);

      setLesson((current) => ({
        ...current,
        title: "",
        description: "",
        content: "",
        video_url: "",
        order: 1,
      }));

      onDone("Lesson added.");
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  const publish = async () => {
    try {
      await patch(`/courses/${selected.id}/`, {
        is_published: !selected.is_published,
      });

      setSelected((current) => ({
        ...current,
        is_published: !current.is_published,
      }));

      onDone("Course publication status updated.");
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  return (
    <>
      <DetailPanel title="Create course">
        <form className="management-form" onSubmit={create}>
          {[
            ["title", "Course title"],
            ["slug", "Unique slug"],
            ["category", "Category"],
            ["duration_minutes", "Duration minutes"],
          ].map(([name, label]) => (
            <label key={name}>
              {label}
              <input
                name={name}
                value={form[name]}
                onChange={change}
                required={name !== "category"}
              />
            </label>
          ))}

          <label>
            Level
            <select
              name="level"
              value={form.level}
              onChange={change}
            >
              <option value="BEGINNER">BEGINNER</option>
              <option value="INTERMEDIATE">INTERMEDIATE</option>
              <option value="ADVANCED">ADVANCED</option>
            </select>
          </label>

          <label className="full-span">
            Description
            <textarea
              name="description"
              rows="4"
              value={form.description}
              onChange={change}
            />
          </label>

          <label>
            Thumbnail
            <input
              name="thumbnail"
              type="file"
              accept="image/*"
              onChange={change}
            />
          </label>

          <label className="checkbox-field">
            <input
              type="checkbox"
              name="is_published"
              checked={form.is_published}
              onChange={change}
            />
            Publish immediately
          </label>

          <button className="primary-btn" disabled={saving}>
            <Plus size={15} />
            Create course
          </button>
        </form>
      </DetailPanel>

      {err && <div className="form-error">{err}</div>}

      <DetailPanel title="Existing courses">
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Course</th>
                <th>Level</th>
                <th>Lessons</th>
                <th>Published</th>
                <th>Manage</th>
              </tr>
            </thead>

            <tbody>
              {data.map((course) => (
                <tr key={course.id}>
                  <td>
                    <b>{course.title}</b>
                    <br />
                    <span className="muted-text">
                      {course.category || "General"}
                    </span>
                  </td>

                  <td>{course.level}</td>
                  <td>{course.lessons || 0}</td>

                  <td>
                    <Badge
                      tone={
                        course.is_published ? "success" : "muted"
                      }
                    >
                      {course.is_published ? "Published" : "Draft"}
                    </Badge>
                  </td>

                  <td>
                    <button
                      type="button"
                      className="outline-btn"
                      onClick={() => select(course)}
                    >
                      Manage content
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DetailPanel>

      {selected && (
        <DetailPanel
          title={`Course builder · ${selected.title}`}
          actions={
            <button
              type="button"
              className="outline-btn"
              onClick={publish}
            >
              {selected.is_published ? "Unpublish" : "Publish"}
            </button>
          }
        >
          <form className="management-form" onSubmit={addModule}>
            <label>
              Module title
              <input
                value={module.title}
                onChange={(e) =>
                  setModule({
                    ...module,
                    title: e.target.value,
                  })
                }
                required
              />
            </label>

            <label>
              Order
              <input
                type="number"
                value={module.order}
                onChange={(e) =>
                  setModule({
                    ...module,
                    order: e.target.value,
                  })
                }
              />
            </label>

            <label className="full-span">
              Module description
              <textarea
                rows="3"
                value={module.description}
                onChange={(e) =>
                  setModule({
                    ...module,
                    description: e.target.value,
                  })
                }
              />
            </label>

            <button className="primary-btn">
              <Plus size={15} />
              Add module
            </button>
          </form>

          <div style={{ marginTop: 18 }}>
            {modules.map((item) => (
              <div
                key={item.id}
                className="management-existing"
              >
                <div>
                  <b>
                    {item.order}. {item.title}
                  </b>
                  <div className="muted-text">
                    {item.lessons?.length || 0} lessons
                  </div>
                </div>
              </div>
            ))}
          </div>

          <form
            className="management-form"
            onSubmit={addLesson}
            style={{ marginTop: 18 }}
          >
            <label>
              Module
              <select
                value={lesson.module_id}
                onChange={(e) =>
                  setLesson({
                    ...lesson,
                    module_id: e.target.value,
                  })
                }
                required
              >
                <option value="">Select module</option>
                {modules.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.order}. {item.title}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Lesson title
              <input
                value={lesson.title}
                onChange={(e) =>
                  setLesson({
                    ...lesson,
                    title: e.target.value,
                  })
                }
                required
              />
            </label>

            <label>
              Duration minutes
              <input
                type="number"
                value={lesson.duration_minutes}
                onChange={(e) =>
                  setLesson({
                    ...lesson,
                    duration_minutes: e.target.value,
                  })
                }
              />
            </label>

            <label>
              Video URL
              <input
                type="url"
                value={lesson.video_url}
                onChange={(e) =>
                  setLesson({
                    ...lesson,
                    video_url: e.target.value,
                  })
                }
              />
            </label>

            <label className="full-span">
              Lesson description
              <textarea
                rows="2"
                value={lesson.description}
                onChange={(e) =>
                  setLesson({
                    ...lesson,
                    description: e.target.value,
                  })
                }
              />
            </label>

            <label className="full-span">
              Lesson content
              <textarea
                rows="6"
                value={lesson.content}
                onChange={(e) =>
                  setLesson({
                    ...lesson,
                    content: e.target.value,
                  })
                }
              />
            </label>

            <button className="primary-btn">
              <Plus size={15} />
              Add lesson
            </button>
          </form>
        </DetailPanel>
      )}
    </>
  );
}

function AssessmentManager({ data, onDone }) {
  const [form, setForm] = useState(emptyAssessment);
  const [selected, setSelected] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [q, setQ] = useState(emptyQuestion);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  const change = (e) => {
    const { name, value, type, checked } = e.target;

    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const qchange = (e) => {
    const { name, value } = e.target;

    setQ((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const refresh = async (id) => {
    setQuestions(await get(`/assessments/${id}/questions/`));
  };

  const create = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErr("");

    try {
      const payload = {
        ...form,
        duration_minutes: Number(form.duration_minutes || 0),
        total_marks: Number(form.total_marks || 0),
        passing_marks: Number(form.passing_marks || 0),
        start_at: form.start_at
          ? new Date(form.start_at).toISOString()
          : null,
        end_at: form.end_at
          ? new Date(form.end_at).toISOString()
          : null,
      };

      const assessment = await post("/assessments/", payload);

      setSelected(assessment);
      setForm(emptyAssessment);

      await refresh(assessment.id);

      onDone(
        "Assessment created. Add its MCQ or coding questions before publishing."
      );
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const select = async (assessment) => {
    setSelected(assessment);
    setQ({
      ...emptyQuestion,
      order: 1,
    });
    setEditingId(null);

    try {
      await refresh(assessment.id);
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  const addQuestion = async (e) => {
    e.preventDefault();
    setErr("");

    try {
      const payload = {
        ...q,
        marks: Number(q.marks || 1),
        order: Number(q.order || questions.length + 1),
        test_cases:
          q.question_type === "CODING"
            ? q.test_cases.filter(
                (item) => item.input !== "" || item.output !== ""
              )
            : [],
      };

      if (editingId) {
        await patch(`/assessments/${selected.id}/questions/`, {
          ...payload,
          assessment_question_id: editingId,
        });
      } else {
        await post(
          `/assessments/${selected.id}/questions/`,
          payload
        );
      }

      setQ({
        ...emptyQuestion,
        order: questions.length + (editingId ? 1 : 2),
      });

      setEditingId(null);

      await refresh(selected.id);

      onDone(
        editingId
          ? "Question updated."
          : "Question added to the paper."
      );
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  const editQuestion = (assessmentQuestion) => {
    setEditingId(assessmentQuestion.id);

    setQ({
      ...emptyQuestion,
      ...assessmentQuestion.question,
      order: assessmentQuestion.order,
      marks:
        assessmentQuestion.marks ||
        assessmentQuestion.question.marks,
      test_cases:
        Array.isArray(assessmentQuestion.question.test_cases) &&
        assessmentQuestion.question.test_cases.length
          ? assessmentQuestion.question.test_cases
          : [{ input: "", output: "" }],
    });
  };

  const remove = async (assessmentQuestion) => {
    if (
      !window.confirm(
        "Delete this question from the assessment?"
      )
    ) {
      return;
    }

    try {
      await del(`/assessments/${selected.id}/questions/`, {
        data: {
          assessment_question_id: assessmentQuestion.id,
        },
      });

      await refresh(selected.id);
      onDone("Question removed.");
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  const publish = async () => {
    try {
      const updated = await patch(
        `/assessments/${selected.id}/`,
        {
          is_published: !selected.is_published,
        }
      );

      setSelected((current) => ({
        ...current,
        ...updated,
      }));

      onDone("Assessment publication status updated.");
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  return (
    <>
      <DetailPanel title="Create assessment">
        <form className="management-form" onSubmit={create}>
          {[
            ["title", "Assessment title"],
            ["duration_minutes", "Duration minutes"],
            ["total_marks", "Total marks"],
            ["passing_marks", "Passing marks"],
          ].map(([name, label]) => (
            <label key={name}>
              {label}
              <input
                name={name}
                type={name === "title" ? "text" : "number"}
                value={form[name]}
                onChange={change}
                required
              />
            </label>
          ))}

          <label>
            Assessment type
            <select
              name="assessment_type"
              value={form.assessment_type}
              onChange={change}
            >
              <option value="MCQ">MCQ</option>
              <option value="CODING">CODING</option>
              <option value="MIXED">MIXED</option>
            </select>
          </label>

          <label>
            Start
            <input
              name="start_at"
              type="datetime-local"
              value={form.start_at}
              onChange={change}
            />
          </label>

          <label>
            End
            <input
              name="end_at"
              type="datetime-local"
              value={form.end_at}
              onChange={change}
            />
          </label>

          <label className="checkbox-field">
            <input
              type="checkbox"
              name="is_published"
              checked={form.is_published}
              onChange={change}
            />
            Publish immediately
          </label>

          <label className="full-span">
            Description
            <textarea
              name="description"
              rows="4"
              value={form.description}
              onChange={change}
            />
          </label>

          <button
            className="primary-btn"
            disabled={saving}
          >
            <Plus size={15} />
            Create assessment
          </button>
        </form>
      </DetailPanel>

      {err && <div className="form-error">{err}</div>}

      <DetailPanel title="Assessment papers">
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Questions</th>
                <th>Status</th>
                <th>Manage</th>
              </tr>
            </thead>

            <tbody>
              {data.map((assessment) => (
                <tr key={assessment.id}>
                  <td>
                    <b>{assessment.title}</b>
                  </td>

                  <td>{assessment.assessment_type}</td>
                  <td>{assessment.questions || 0}</td>

                  <td>
                    <Badge
                      tone={
                        assessment.is_published
                          ? "success"
                          : "muted"
                      }
                    >
                      {assessment.is_published
                        ? "Published"
                        : "Draft"}
                    </Badge>
                  </td>

                  <td>
                    <button
                      type="button"
                      className="outline-btn"
                      onClick={() => select(assessment)}
                    >
                      Edit question paper
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DetailPanel>

      {selected && (
        <DetailPanel
          title={`Question paper · ${selected.title}`}
          actions={
            <button
              type="button"
              className="outline-btn"
              onClick={publish}
            >
              {selected.is_published
                ? "Unpublish"
                : "Publish"}
            </button>
          }
        >
          <div className="management-existing">
            <b>{questions.length} questions</b>
            <span>
              Students see this paper only after publication
              and availability checks.
            </span>
          </div>

          {questions.map((assessmentQuestion) => (
            <div
              key={assessmentQuestion.id}
              className="management-existing"
            >
              <div style={{ flex: 1 }}>
                <b>
                  Q{assessmentQuestion.order}.{" "}
                  {assessmentQuestion.question.text}
                </b>

                <div className="muted-text">
                  {assessmentQuestion.question.question_type} ·{" "}
                  {assessmentQuestion.marks ||
                    assessmentQuestion.question.marks}{" "}
                  marks
                </div>
              </div>

              <div style={{ display: "flex", gap: 6 }}>
                <button
                  type="button"
                  className="outline-btn"
                  onClick={() =>
                    editQuestion(assessmentQuestion)
                  }
                >
                  Edit
                </button>

                <button
                  type="button"
                  className="outline-btn"
                  onClick={() =>
                    remove(assessmentQuestion)
                  }
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}

          <form
            className="management-form"
            onSubmit={addQuestion}
            style={{ marginTop: 18 }}
          >
            <label className="full-span">
              Question
              <textarea
                name="text"
                rows="4"
                value={q.text}
                onChange={qchange}
                required
              />
            </label>

            <label>
              Type
              <select
                name="question_type"
                value={q.question_type}
                onChange={qchange}
              >
                <option value="MCQ">MCQ</option>
                <option value="CODING">CODING</option>
                <option value="TRUE_FALSE">
                  TRUE_FALSE
                </option>
                <option value="SHORT">SHORT</option>
              </select>
            </label>

            <label>
              Marks
              <input
                name="marks"
                type="number"
                min="1"
                value={q.marks}
                onChange={qchange}
              />
            </label>

            {q.question_type === "MCQ" && (
              <>
                <label>
                  Option A
                  <input
                    name="option_a"
                    value={q.option_a}
                    onChange={qchange}
                    required
                  />
                </label>

                <label>
                  Option B
                  <input
                    name="option_b"
                    value={q.option_b}
                    onChange={qchange}
                    required
                  />
                </label>

                <label>
                  Option C
                  <input
                    name="option_c"
                    value={q.option_c}
                    onChange={qchange}
                  />
                </label>

                <label>
                  Option D
                  <input
                    name="option_d"
                    value={q.option_d}
                    onChange={qchange}
                  />
                </label>

                <label>
                  Correct answer
                  <select
                    name="correct_answer"
                    value={q.correct_answer}
                    onChange={qchange}
                  >
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                  </select>
                </label>
              </>
            )}

            {q.question_type === "TRUE_FALSE" && (
              <label>
                Correct answer
                <select
                  name="correct_answer"
                  value={q.correct_answer}
                  onChange={qchange}
                >
                  <option value="True">True</option>
                  <option value="False">False</option>
                </select>
              </label>
            )}

            {q.question_type === "CODING" && (
              <>
                <label>
                  Language
                  <select
                    name="coding_language"
                    value={q.coding_language}
                    onChange={qchange}
                  >
                    <option value="PYTHON">PYTHON</option>
                    <option value="JAVA">JAVA</option>
                    <option value="CPP">CPP</option>
                    <option value="C">C</option>
                    <option value="JAVASCRIPT">
                      JAVASCRIPT
                    </option>
                  </select>
                </label>

                <label className="full-span">
                  Starter code
                  <textarea
                    name="starter_code"
                    rows="5"
                    value={q.starter_code}
                    onChange={qchange}
                  />
                </label>

                <label>
                  Input format
                  <textarea
                    name="input_format"
                    rows="3"
                    value={q.input_format}
                    onChange={qchange}
                  />
                </label>

                <label>
                  Output format
                  <textarea
                    name="output_format"
                    rows="3"
                    value={q.output_format}
                    onChange={qchange}
                  />
                </label>

                <label className="full-span">
                  Constraints
                  <textarea
                    name="constraints"
                    rows="3"
                    value={q.constraints}
                    onChange={qchange}
                  />
                </label>

                <div className="full-span">
                  <b style={{ fontSize: 10 }}>
                    Hidden/public test cases
                  </b>

                  {q.test_cases.map((testCase, index) => (
                    <div
                      className="management-form"
                      key={index}
                      style={{ marginTop: 8 }}
                    >
                      <label>
                        Input
                        <textarea
                          rows="2"
                          value={testCase.input}
                          onChange={(e) =>
                            setQ((current) => ({
                              ...current,
                              test_cases:
                                current.test_cases.map(
                                  (item, itemIndex) =>
                                    itemIndex === index
                                      ? {
                                          ...item,
                                          input:
                                            e.target.value,
                                        }
                                      : item
                                ),
                            }))
                          }
                        />
                      </label>

                      <label>
                        Expected output
                        <textarea
                          rows="2"
                          value={testCase.output}
                          onChange={(e) =>
                            setQ((current) => ({
                              ...current,
                              test_cases:
                                current.test_cases.map(
                                  (item, itemIndex) =>
                                    itemIndex === index
                                      ? {
                                          ...item,
                                          output:
                                            e.target.value,
                                        }
                                      : item
                                ),
                            }))
                          }
                        />
                      </label>
                    </div>
                  ))}

                  <button
                    type="button"
                    className="outline-btn"
                    onClick={() =>
                      setQ((current) => ({
                        ...current,
                        test_cases: [
                          ...current.test_cases,
                          {
                            input: "",
                            output: "",
                          },
                        ],
                      }))
                    }
                  >
                    <Plus size={13} />
                    Add test case
                  </button>
                </div>
              </>
            )}

            <label className="full-span">
              Explanation
              <textarea
                name="explanation"
                rows="3"
                value={q.explanation}
                onChange={qchange}
              />
            </label>

            <button className="primary-btn" type="submit">
              {editingId
                ? "Save question changes"
                : "Add question to paper"}
            </button>

            {editingId && (
              <button
                type="button"
                className="outline-btn"
                onClick={() => {
                  setEditingId(null);
                  setQ({
                    ...emptyQuestion,
                    order: questions.length + 1,
                  });
                }}
              >
                Cancel edit
              </button>
            )}
          </form>
        </DetailPanel>
      )}
    </>
  );
}


function AssignmentManager({ data, onDone }) {
  const empty = {
    title: "",
    description: "",
    instructions: "",
    due_date: "",
    duration_minutes: 60,
    max_marks: 100,
    status: "DRAFT",
    attachment: null,
  };

  const [form, setForm] = useState(empty);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [fileName, setFileName] = useState("");

  const change = (event) => {
    const { name, value } = event.target;
    setForm((old) => ({ ...old, [name]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setErr("");

    try {
      const body = new FormData();
      body.append("title", form.title);
      body.append("description", form.description);
      body.append("instructions", form.instructions);
      body.append("due_date", new Date(form.due_date).toISOString());
      body.append("duration_minutes", String(Number(form.duration_minutes || 0)));
      body.append("max_marks", String(Number(form.max_marks || 0)));
      body.append("status", form.status);

      if (form.attachment) {
        body.append("attachment", form.attachment);
      }

      if (editing) {
        await patch(`/assignments/${editing.id}/`, body);
        onDone("Assignment updated successfully.");
      } else {
        await post("/assignments/", body);
        onDone("Assignment created successfully.");
      }

      setForm(empty);
      setEditing(null);
      setFileName("");
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const edit = (item) => {
    setEditing(item);
    setForm({
      title: item.title || "",
      description: item.description || "",
      instructions: item.instructions || "",
      due_date: item.due_date
        ? new Date(item.due_date).toISOString().slice(0, 16)
        : "",
      duration_minutes: item.duration_minutes || 60,
      max_marks: item.max_marks || 100,
      status: item.status || "DRAFT",
      attachment: null,
    });
    setFileName("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const remove = async (item) => {
    if (!window.confirm(`Delete "${item.title}"?`)) return;

    try {
      await del(`/assignments/${item.id}/`);
      onDone("Assignment deleted.");
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  const togglePublish = async (item) => {
    try {
      await patch(`/assignments/${item.id}/`, {
        status: item.status === "PUBLISHED" ? "DRAFT" : "PUBLISHED",
      });
      onDone(
        item.status === "PUBLISHED"
          ? "Assignment moved to draft."
          : "Assignment published."
      );
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  return (
    <>
      <DetailPanel
        title={editing ? "Edit assignment" : "Create assignment"}
      >
        <form className="management-form" onSubmit={submit}>
          <label>
            Assignment title
            <input
              name="title"
              value={form.title}
              onChange={change}
              placeholder="e.g. Java OOP Mini Project"
              required
            />
          </label>

          <label>
            Maximum marks
            <input
              name="max_marks"
              type="number"
              min="1"
              value={form.max_marks}
              onChange={change}
              required
            />
          </label>

          <label>
            Duration (minutes)
            <input
              name="duration_minutes"
              type="number"
              min="1"
              value={form.duration_minutes}
              onChange={change}
              required
            />
          </label>

          <label>
            Due date & time
            <input
              name="due_date"
              type="datetime-local"
              value={form.due_date}
              onChange={change}
              required
            />
          </label>

          <label>
            Status
            <select
              name="status"
              value={form.status}
              onChange={change}
            >
              <option value="DRAFT">Draft</option>
              <option value="PUBLISHED">Publish</option>
              <option value="CLOSED">Closed</option>
            </select>
          </label>

          <label className="full-span">
            Description
            <textarea
              name="description"
              rows="3"
              value={form.description}
              onChange={change}
              placeholder="Explain what students need to complete."
              required
            />
          </label>

          <label className="full-span">
            Instructions
            <textarea
              name="instructions"
              rows="5"
              value={form.instructions}
              onChange={change}
              placeholder="Submission rules, required format, evaluation criteria, etc."
            />
          </label>

          <label className="full-span assignment-upload-box">
            <span className="assignment-upload-title">
              <Paperclip size={15} />
              Assignment question / reference file
            </span>
            <span className="assignment-upload-help">
              Upload PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, ZIP, JPG, PNG or
              another file for students to download.
            </span>
            <input
              type="file"
              onChange={(event) => {
                const selected = event.target.files?.[0] || null;
                setForm((old) => ({
                  ...old,
                  attachment: selected,
                }));
                setFileName(selected?.name || "");
              }}
            />
            <span className="assignment-file-name">
              {fileName || "Choose a file"}
            </span>
          </label>

          {err && <div className="form-error full-span">{err}</div>}

          <div className="full-span" style={{ display: "flex", gap: 8 }}>
            <button className="primary-btn" disabled={saving}>
              <Upload size={15} />
              {saving
                ? "Saving..."
                : editing
                ? "Update assignment"
                : "Create assignment"}
            </button>

            {editing && (
              <button
                type="button"
                className="outline-btn"
                onClick={() => {
                  setEditing(null);
                  setForm(empty);
                  setFileName("");
                  setErr("");
                }}
              >
                <X size={14} />
                Cancel
              </button>
            )}
          </div>
        </form>
      </DetailPanel>

      <DetailPanel title={`Assignments · ${data.length}`}>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Assignment</th>
                <th>Marks</th>
                <th>Duration</th>
                <th>Due</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {data.map((item) => (
                <tr key={item.id}>
                  <td>
                    <b>{item.title}</b>
                    <small>
                      {item.attachment ? "Reference file attached" : "No reference file"}
                    </small>
                  </td>

                  <td>{item.max_marks}</td>

                  <td>{item.duration_minutes || "—"} min</td>

                  <td>
                    {item.due_date
                      ? new Date(item.due_date).toLocaleString()
                      : "—"}
                  </td>

                  <td>
                    <Badge
                      tone={
                        item.status === "PUBLISHED"
                          ? "success"
                          : item.status === "CLOSED"
                          ? "warning"
                          : "muted"
                      }
                    >
                      {item.status}
                    </Badge>
                  </td>

                  <td>
                    <div style={{ display: "flex", gap: 6 }}>
                      <button
                        type="button"
                        className="action-link"
                        onClick={() => edit(item)}
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        className="action-link"
                        onClick={() => togglePublish(item)}
                      >
                        {item.status === "PUBLISHED"
                          ? "Unpublish"
                          : "Publish"}
                      </button>

                      <button
                        type="button"
                        className="action-link"
                        onClick={() => remove(item)}
                      >
                        Delete
                      </button>

                      {item.attachment && (
                        <a
                          className="action-link"
                          href={item.attachment}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <Eye size={13} />
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}

              {!data.length && (
                <tr>
                  <td colSpan="6">
                    <span className="muted-text">
                      No assignments created yet.
                    </span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </DetailPanel>

      <AssignmentSubmissionsManager />
    </>
  );
}

function AssignmentSubmissionsManager() {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");
  const loadSubmissions = async () => { setLoading(true); setError(""); try { const response = await get("/assignments/submissions/?page_size=200"); setSubmissions(unwrapList(response)); } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); } };
  useEffect(() => { loadSubmissions(); }, []);
  const visible = submissions.filter((item) => !filter || JSON.stringify(item).toLowerCase().includes(filter.toLowerCase()));
  return (
    <DetailPanel title={`Student submissions · ${submissions.length}`}>
      <div className="module-toolbar" style={{ marginBottom: 14 }}>
        <label className="module-search"><FileText size={15}/><input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Search student or assignment..."/></label>
        <button type="button" className="outline-btn" onClick={loadSubmissions} disabled={loading}>{loading ? "Refreshing..." : "Refresh"}</button>
      </div>
      {error ? <div className="form-error">{error}</div> : null}
      {loading ? <Loading text="Loading student submissions..."/> : !visible.length ? <div className="empty-state"><FileText size={22}/><b>No student submissions</b><span>Submitted assignment files will appear here.</span></div> : (
        <div className="table-scroll"><table className="data-table"><thead><tr><th>Student</th><th>Assignment</th><th>Submitted</th><th>Status</th><th>Marks</th><th>Student file</th><th>Action</th></tr></thead><tbody>
          {visible.map((submission) => <tr key={submission.id}>
            <td><b>{submission.student_name || submission.student?.name || submission.student?.user?.name || "Student"}</b><small>{submission.student_email || submission.student?.user?.email || ""}</small></td>
            <td><b>{submission.assignment_title || submission.assignment?.title || `Assignment #${submission.assignment}`}</b></td>
            <td>{submission.submitted_at ? new Date(submission.submitted_at).toLocaleString() : "—"}</td>
            <td><Badge tone={submission.status === "EVALUATED" ? "success" : submission.status === "LATE" ? "warning" : "muted"}>{submission.status || "SUBMITTED"}</Badge></td>
            <td>{submission.score != null ? submission.score : "—"}</td>
            <td>{submission.submitted_file ? <a className="resource-link" href={submission.submitted_file} target="_blank" rel="noreferrer"><Eye size={14}/> View file</a> : <span className="muted-text">No file</span>}</td>
            <td>{submission.submitted_file ? <a className="action-link" href={submission.submitted_file} target="_blank" rel="noreferrer">Open / Download</a> : <span className="muted-text">Text only</span>}</td>
          </tr>)}
        </tbody></table></div>
      )}
    </DetailPanel>
  );
}

function ResultsManager({ data }) {
  return (
    <DetailPanel
      title={`Assessment results · ${data.length}`}
    >
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Student</th>
              <th>Assessment</th>
              <th>Type</th>
              <th>Correct</th>
              <th>Wrong</th>
              <th>Unanswered</th>
              <th>Score</th>
              <th>Result</th>
            </tr>
          </thead>

          <tbody>
            {data.map((item) => (
              <tr key={item.id}>
                <td>
                  <b>{item.student_name}</b>
                  <br />
                  <span className="muted-text">
                    {item.student_email}
                  </span>
                </td>

                <td>{item.assessment_title}</td>
                <td>{item.assessment_type}</td>

                <td className="result-correct">
                  {item.correct_answers}
                </td>

                <td className="result-wrong">
                  {item.wrong_answers}
                </td>

                <td>{item.unanswered}</td>

                <td>
                  <b>{item.score}</b> / {item.percentage}%
                </td>

                <td>
                  <Badge
                    tone={item.passed ? "success" : "warning"}
                  >
                    {item.passed ? "PASS" : "REVIEW"}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DetailPanel>
  );
}

function ExternalCoding({ data, onDone }) {
  const initialForm = {
    platform: "LEETCODE",
    title: "",
    external_url: "",
    external_problem_id: "",
    external_number: "",
    description: "",
    difficulty: "EASY",
    topic: "",
    is_published: true,
  };

  const [form, setForm] = useState(initialForm);

  const submit = async (e) => {
    e.preventDefault();

    try {
      await post("/coding/external/", form);

      setForm(initialForm);

      onDone("External coding question added.");
    } catch (e) {
      alert(errorMessage(e));
    }
  };

  return (
    <DetailPanel title="Connect official coding-platform questions">
      <p className="muted-text">
        Store metadata and the original official URL. Students
        are sent to the original platform to solve external
        questions.
      </p>

      <form className="management-form" onSubmit={submit}>
        <label>
          Question title
          <input
            name="title"
            value={form.title}
            onChange={(e) =>
              setForm({
                ...form,
                title: e.target.value,
              })
            }
            required
          />
        </label>

        <label>
          Official URL
          <input
            name="external_url"
            value={form.external_url}
            onChange={(e) =>
              setForm({
                ...form,
                external_url: e.target.value,
              })
            }
            required
          />
        </label>

        <label>
          Problem ID
          <input
            name="external_problem_id"
            value={form.external_problem_id}
            onChange={(e) =>
              setForm({
                ...form,
                external_problem_id: e.target.value,
              })
            }
          />
        </label>

        <label>
          Question number
          <input
            name="external_number"
            value={form.external_number}
            onChange={(e) =>
              setForm({
                ...form,
                external_number: e.target.value,
              })
            }
          />
        </label>

        <label>
          Topic
          <input
            name="topic"
            value={form.topic}
            onChange={(e) =>
              setForm({
                ...form,
                topic: e.target.value,
              })
            }
          />
        </label>

        <label>
          Platform
          <select
            value={form.platform}
            onChange={(e) =>
              setForm({
                ...form,
                platform: e.target.value,
              })
            }
          >
            <option value="LEETCODE">LeetCode</option>
            <option value="HACKERRANK">HackerRank</option>
            <option value="CODECHEF">CodeChef</option>
            <option value="CODEFORCES">Codeforces</option>
            <option value="GEEKSFORGEEKS">
              GeeksforGeeks
            </option>
          </select>
        </label>

        <label>
          Difficulty
          <select
            value={form.difficulty}
            onChange={(e) =>
              setForm({
                ...form,
                difficulty: e.target.value,
              })
            }
          >
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
          </select>
        </label>

        <label className="full-span">
          Description
          <textarea
            rows="4"
            value={form.description}
            onChange={(e) =>
              setForm({
                ...form,
                description: e.target.value,
              })
            }
          />
        </label>

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={form.is_published}
            onChange={(e) =>
              setForm({
                ...form,
                is_published: e.target.checked,
              })
            }
          />
          Publish immediately
        </label>

        <button type="submit" className="primary-btn">
          <Plus size={15} />
          Add official question
        </button>
      </form>

      <div
        className="table-scroll"
        style={{ marginTop: 18 }}
      >
        <table className="data-table">
          <thead>
            <tr>
              <th>Question</th>
              <th>Platform</th>
              <th>Difficulty</th>
              <th>URL</th>
            </tr>
          </thead>

          <tbody>
            {data.map((problem) => (
              <tr key={problem.id}>
                <td>{problem.title}</td>
                <td>
                  {problem.platform_label ||
                    problem.platform}
                </td>
                <td>
                  {problem.difficulty_label ||
                    problem.difficulty}
                </td>

                <td>
                  <a
                    className="resource-link"
                    href={problem.external_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DetailPanel>
  );
}

function SimpleManager({ tab, data }) {
  const columns = Object.keys(
    data[0] || {
      title: "Title",
      status: "Status",
    }
  ).slice(0, 6);

  return (
    <DetailPanel
      title={`${tab} · ${data.length} records`}
    >
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((key) => (
                <th key={key}>{key}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {data.map((item) => (
              <tr key={item.id}>
                {columns.map((key) => (
                  <td key={key}>
                    {typeof item[key] === "object"
                      ? JSON.stringify(item[key])
                      : String(item[key] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p
        className="muted-text"
        style={{ marginTop: 12 }}
      >
        This module is connected to the live Django data.
        Course and assessment authoring have dedicated editors
        above.
      </p>
    </DetailPanel>
  );
}
