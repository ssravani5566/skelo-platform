import React, { useEffect, useState } from "react";
import { ArrowLeft, Check, CheckCircle2, ExternalLink, Globe2, Play, LoaderCircle } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { Badge, DetailPanel } from "../../components/ModuleCard";
import { Empty, ErrorState, Loading } from "../../components/AsyncState";
import { del, errorMessage, get, post } from "../../services/api";

function openExternal(url) {
  if (!url || !/^https:\/\//i.test(url)) return;
  window.open(url, "_blank", "noopener,noreferrer");
}

export default function ProblemDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("PYTHON");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [progressBusy, setProgressBusy] = useState(false);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    get(`/coding/problems/${id}/`)
      .then(setProblem)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  const submit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const response = await post(`/coding/problems/${id}/submit/`, {
        language,
        source_code: code,
      });
      setResult(response);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  const toggleExternalSolved = async () => {
    setProgressBusy(true);
    setError("");
    try {
      if (problem.solved) await del(`/coding/problems/${id}/progress/`);
      else await post(`/coding/problems/${id}/progress/`, {});
      await load();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setProgressBusy(false);
    }
  };

  if (loading) return <Loading text="Loading question..." />;
  if (error && !problem) return <ErrorState text={error} onRetry={load} />;

  if (problem?.is_external) {
    const metric = problem.acceptance_rate != null
      ? `${Number(problem.acceptance_rate).toFixed(1)}% acceptance`
      : problem.success_rate != null
        ? `${Number(problem.success_rate).toFixed(1)}% success`
        : problem.platform === "CODEFORCES" && problem.platform_metric_value != null
          ? `${Number(problem.platform_metric_value).toLocaleString()} solved`
          : "Platform metric unavailable";

    return (
      <div>
        <button className="back-link" onClick={() => nav("/coding")}>
          <ArrowLeft size={15} /> Coding Arena
        </button>

        <PageHeader
          eyebrow={`SCOTT · ${problem.platform_label || "EXTERNAL"}`}
          title={problem.title}
          subtitle={problem.topic || "External coding question"}
          action={<Badge tone={String(problem.difficulty).toLowerCase()}>{problem.difficulty_label}</Badge>}
        />

        <section className="external-detail-hero">
          <div>
            <div className="external-detail-kicker"><Globe2 size={15} /> {problem.platform_label}</div>
            <h2>{problem.solved ? "Completed in your SCOTT practice tracker" : "Solve this question on the original platform"}</h2>
            <p>
              SCOTT keeps the catalog and your practice state. The original platform remains responsible for the full statement, editor, execution and submission result.
            </p>
          </div>
          <div className="external-detail-actions">
            <button className="primary-btn external-solve-btn" onClick={() => openExternal(problem.external_url)}>
              <ExternalLink size={16} /> Solve on {problem.platform_label}
            </button>
            <button className={`outline-btn ${problem.solved ? "external-marked-btn" : ""}`} onClick={toggleExternalSolved} disabled={progressBusy}>
              {progressBusy ? <LoaderCircle className="spin" size={15} /> : problem.solved ? <Check size={15} /> : null}
              {problem.solved ? "Mark unsolved" : "Mark solved"}
            </button>
          </div>
        </section>

        <div className="detail-grid">
          <DetailPanel title="Question metadata">
            <div className="external-meta-grid">
              <div><span>Platform</span><b>{problem.platform_label}</b></div>
              <div><span>Question</span><b>{problem.external_number || problem.external_problem_id || "—"}</b></div>
              <div><span>Difficulty</span><b>{problem.difficulty_label}</b></div>
              <div><span>Acceptance / success</span><b>{metric}</b></div>
            </div>
            <div className="lesson-content external-note">
              {problem.description || "Full question content is available on the original platform."}
            </div>
            {problem.topics?.length > 0 && (
              <div className="topic-chip-list">{problem.topics.map((topic) => <span key={topic}>{topic}</span>)}</div>
            )}
          </DetailPanel>

          <DetailPanel title="Original question link">
            <div className="external-url-box"><span>{problem.external_url}</span></div>
            <button className="outline-btn external-open-btn" onClick={() => openExternal(problem.external_url)}>
              <ExternalLink size={15} /> Open original question
            </button>
            <div className="external-integrity-note">
              <CheckCircle2 size={14} />
              Your solve result comes from {problem.platform_label}, not from a fake SCOTT submission.
            </div>
          </DetailPanel>
        </div>

        {error && <div className="form-error">{error}</div>}
      </div>
    );
  }

  return (
    <div>
      <button className="back-link" onClick={() => nav("/coding")}>
        <ArrowLeft size={15} /> Coding Arena
      </button>

      <PageHeader
        eyebrow="SCOTT · PROBLEM"
        title={problem.title}
        subtitle={problem.topic || "Problem details"}
        action={<Badge tone={String(problem.difficulty).toLowerCase()}>{problem.difficulty_label}</Badge>}
      />

      <div className="detail-grid">
        <DetailPanel title="Problem statement">
          <div className="lesson-content">{problem.description}</div>
          <div className="kv"><span>Input</span><p>{problem.input_format || "Not provided"}</p></div>
          <div className="kv"><span>Output</span><p>{problem.output_format || "Not provided"}</p></div>
          <div className="kv"><span>Constraints</span><p>{problem.constraints || "Not provided"}</p></div>
        </DetailPanel>

        <DetailPanel title="Sample tests">
          {problem.samples?.length ? problem.samples.map((x) => (
            <div className="sample-box" key={x.id}>
              <b>Sample {x.order}</b>
              <pre>{`Input:\n${x.input}\n\nExpected output:\n${x.expected_output}`}</pre>
            </div>
          )) : (
            <Empty title="No sample tests" text="No public sample test cases were added." />
          )}
        </DetailPanel>
      </div>

      <section className="live-panel code-editor-panel">
        <div className="live-panel-head">
          <h2>Submit solution</h2>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="PYTHON">Python</option>
            <option value="JAVA">Java</option>
            <option value="CPP">C++</option>
            <option value="C">C</option>
            <option value="JAVASCRIPT">JavaScript</option>
          </select>
        </div>

        <textarea
          className="code-editor"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Write your solution here..."
          spellCheck="false"
        />

        {error && <div className="form-error">{error}</div>}

        <button className="primary-btn" disabled={submitting || !code.trim()} onClick={submit}>
          <Play size={16} /> {submitting ? "Running..." : "Run & submit"}
        </button>
      </section>

      {result && (
        <DetailPanel title="Latest submission">
          <div className="submission-result">
            <strong>{result.status}</strong>
            <span>{result.passed_test_cases}/{result.total_test_cases} tests passed</span>
            {result.error_message && <pre>{result.error_message}</pre>}
          </div>
          <button className="outline-btn" onClick={() => nav("/coding/submissions")}>
            <CheckCircle2 size={15} /> View history
          </button>
        </DetailPanel>
      )}
    </div>
  );
}
