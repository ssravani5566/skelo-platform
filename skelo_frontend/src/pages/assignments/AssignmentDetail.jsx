import React, { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  Clock3,
  Download,
  File,
  FileImage,
  FileText,
  UploadCloud,
  X
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { Badge } from "../../components/ModuleCard";
import { ErrorState, Loading } from "../../components/AsyncState";
import { errorMessage, get, post } from "../../services/api";
import "./AssignmentDetail.css";

const formatSize = (bytes) => {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const iconForFile = (file) => {
  if (!file) return File;
  if (file.type?.startsWith("image/")) return FileImage;
  if (
    file.type === "application/pdf" ||
    file.name?.toLowerCase().endsWith(".pdf")
  ) {
    return FileText;
  }
  return File;
};

export default function AssignmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [assignment, setAssignment] = useState(null);
  const [answer, setAnswer] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await get(`/assignments/${id}/`);
      setAssignment(data);
      setAnswer(data?.submission?.answer_text || "");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const chooseFile = (event) => {
    const selected = event.target.files?.[0] || null;

    if (selected && selected.size > 25 * 1024 * 1024) {
      setError("File size must be 25 MB or less.");
      event.target.value = "";
      return;
    }

    setError("");
    setMessage("");
    setFile(selected);
  };

  const submit = async (event) => {
    event.preventDefault();

    if (!answer.trim() && !file) {
      setError("Write an answer or upload your assignment file.");
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("answer_text", answer.trim());

      if (file) {
        formData.append("submitted_file", file);
      }

      await post(`/assignments/${id}/submit/`, formData);

      setMessage("Your assignment was submitted successfully.");
      setFile(null);

      if (inputRef.current) {
        inputRef.current.value = "";
      }

      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Loading text="Loading assignment..." />;
  }

  if (error && !assignment) {
    return <ErrorState text={error} onRetry={load} />;
  }

  if (!assignment) {
    return (
      <ErrorState
        text="Assignment was not found."
        onRetry={load}
      />
    );
  }

  const canSubmit = assignment.status === "PUBLISHED";
  const submission = assignment.submission;
  const selectedFileIcon = iconForFile(file);
  const SelectedFileIcon = selectedFileIcon;

  return (
    <div className="assignment-detail-page">
      <button
        className="assignment-back"
        type="button"
        onClick={() => navigate("/assignments")}
      >
        <ArrowLeft size={15} />
        Back to assignments
      </button>

      <PageHeader
        eyebrow="SCOTT · ASSIGNMENT"
        title={assignment.title}
        subtitle={assignment.description || "Complete and submit this assignment."}
        action={<Badge>{assignment.status}</Badge>}
      />

      <div className="assignment-meta-grid">
        <div className="assignment-meta-card">
          <span>Maximum marks</span>
          <strong>{assignment.max_marks}</strong>
          <small>marks</small>
        </div>

        <div className="assignment-meta-card">
          <span>Duration</span>
          <strong>{assignment.duration_minutes || "—"}</strong>
          <small>minutes</small>
        </div>

        <div className="assignment-meta-card">
          <span>Due date</span>
          <strong>
            {assignment.due_date
              ? new Date(assignment.due_date).toLocaleDateString()
              : "—"}
          </strong>
          <small>
            {assignment.due_date
              ? new Date(assignment.due_date).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit"
                })
              : ""}
          </small>
        </div>

        <div className="assignment-meta-card">
          <span>Submission</span>
          <strong>{submission ? submission.status : "Pending"}</strong>
          <small>
            {submission?.score != null
              ? `${submission.score}/${assignment.max_marks}`
              : "Not evaluated"}
          </small>
        </div>
      </div>

      <div className="assignment-detail-layout">
        <main className="assignment-instructions-card">
          <div className="assignment-section-heading">
            <div>
              <span>01</span>
              <h2>Assignment instructions</h2>
            </div>
          </div>

          <div className="assignment-description">
            {assignment.description || "No description provided."}
          </div>

          <div className="assignment-instructions">
            <h3>What you need to do</h3>
            <p>
              {assignment.instructions ||
                "Complete the assignment and submit your work before the due date."}
            </p>
          </div>

          {assignment.attachment && (
            <div className="assignment-reference-box">
              <div className="reference-icon">
                <FileText size={19} />
              </div>

              <div>
                <strong>Assignment reference file</strong>
                <span>
                  Download the file provided by your admin/faculty.
                </span>
              </div>

              <a
                href={assignment.attachment}
                target="_blank"
                rel="noreferrer"
                className="assignment-download-btn"
              >
                <Download size={15} />
                Download
              </a>
            </div>
          )}
        </main>

        <aside className="assignment-submission-card">
          <div className="assignment-section-heading">
            <div>
              <span>02</span>
              <h2>Your submission</h2>
            </div>
          </div>

          {submission && (
            <div className="existing-submission">
              <div className="existing-submission-top">
                <CheckCircle2 size={17} />
                <div>
                  <strong>{submission.status}</strong>
                  <span>
                    {submission.submitted_at
                      ? new Date(
                          submission.submitted_at
                        ).toLocaleString()
                      : "Submitted"}
                  </span>
                </div>
              </div>

              {submission.score != null && (
                <div className="submission-score">
                  <strong>{submission.score}</strong>
                  <span>/ {assignment.max_marks} marks</span>
                </div>
              )}

              {submission.feedback && (
                <div className="submission-feedback">
                  <small>Faculty feedback</small>
                  <p>{submission.feedback}</p>
                </div>
              )}
            </div>
          )}

          {canSubmit ? (
            <form
              className="assignment-submit-form"
              onSubmit={submit}
            >
              <label>
                <span>Your answer / explanation</span>
                <textarea
                  value={answer}
                  onChange={(event) =>
                    setAnswer(event.target.value)
                  }
                  placeholder="Write your answer here if required..."
                  rows={6}
                />
              </label>

              <div className="assignment-upload-section">
                <div className="assignment-upload-label">
                  <span>Upload your completed assignment</span>
                  <small>
                    Word, PDF, PowerPoint, Excel, images, ZIP and other
                    files are accepted.
                  </small>
                </div>

                <button
                  type="button"
                  className={`assignment-dropzone ${
                    file ? "has-file" : ""
                  }`}
                  onClick={() => inputRef.current?.click()}
                >
                  {file ? (
                    <>
                      <SelectedFileIcon size={24} />
                      <strong>{file.name}</strong>
                      <span>{formatSize(file.size)}</span>
                      <i
                        role="button"
                        tabIndex={0}
                        onClick={(event) => {
                          event.stopPropagation();
                          setFile(null);
                          if (inputRef.current) {
                            inputRef.current.value = "";
                          }
                        }}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            event.stopPropagation();
                            setFile(null);
                            if (inputRef.current) {
                              inputRef.current.value = "";
                            }
                          }
                        }}
                        aria-label="Remove selected file"
                      >
                        <X size={15} />
                      </i>
                    </>
                  ) : (
                    <>
                      <span className="upload-cloud">
                        <UploadCloud size={25} />
                      </span>
                      <strong>Click to choose your file</strong>
                      <span>Maximum file size: 25 MB</span>
                    </>
                  )}
                </button>

                <input
                  ref={inputRef}
                  type="file"
                  className="hidden-file-input"
                  onChange={chooseFile}
                />
              </div>

              {error && (
                <div className="assignment-form-error">
                  <AlertCircleIcon />
                  {error}
                </div>
              )}

              {message && (
                <div className="assignment-success">
                  <CheckCircle2 size={15} />
                  {message}
                </div>
              )}

              <button
                type="submit"
                className="assignment-submit-button"
                disabled={saving}
              >
                <UploadCloud size={16} />
                {saving
                  ? "Submitting..."
                  : submission
                  ? "Update submission"
                  : "Submit assignment"}
              </button>
            </form>
          ) : (
            <div className="assignment-closed-message">
              <Clock3 size={18} />
              <strong>This assignment is not open for submissions.</strong>
              <span>Check the assignment status above.</span>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function AlertCircleIcon() {
  return (
    <span className="assignment-alert-icon">!</span>
  );
}
