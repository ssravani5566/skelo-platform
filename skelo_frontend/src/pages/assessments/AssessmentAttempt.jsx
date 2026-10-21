import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleCheck,
  Clock3,
  Code2,
  Flag,
  Send
} from "lucide-react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ErrorState, Loading } from "../../components/AsyncState";
import { errorMessage, get, post } from "../../services/api";
import "./Assessment.css";
export default function AssessmentAttempt() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const attemptId = params.get("attempt");
  const navigate = useNavigate();

  const [attempt, setAttempt] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [answers, setAnswers] = useState({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState("");
  const [codeResult, setCodeResult] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const autoSubmitted = useRef(false);

  const questions = assessment?.questions_data || [];
  const currentQuestion = questions[currentIndex];

  const answeredCount = useMemo(
    () =>
      questions.filter((question) => {
        const value = answers[question.id];
        return value !== undefined && String(value).trim() !== "";
      }).length,
    [questions, answers]
  );

  const unansweredCount = Math.max(questions.length - answeredCount, 0);
  const progress = questions.length
    ? Math.round((answeredCount / questions.length) * 100)
    : 0;
  const allAnswered = questions.length > 0 && unansweredCount === 0;

  const loadAssessment = async () => {
    setLoading(true);
    setError("");

    try {
      const [attemptData, assessmentData] = await Promise.all([
        get(`/assessments/attempts/${attemptId}/`),
        get(`/assessments/${id}/`)
      ]);

      setAttempt(attemptData);
      setAssessment(assessmentData);

      const restoredAnswers = {};

      (attemptData.answers || []).forEach((saved) => {
        const question = assessmentData.questions_data?.find(
          (item) => item.id === saved.question
        );

        if (question?.question_type === "CODING") {
          try {
            restoredAnswers[saved.question] =
              JSON.parse(saved.answer_text || "{}").source_code || "";
          } catch {
            restoredAnswers[saved.question] = saved.answer_text || "";
          }
        } else {
          restoredAnswers[saved.question] = saved.answer_text || "";
        }
      });

      setAnswers(restoredAnswers);

      if (attemptData.started_at && assessmentData.duration_minutes) {
        const startedAt = new Date(attemptData.started_at).getTime();
        const durationMs = Number(assessmentData.duration_minutes) * 60 * 1000;
        setTimeLeft(
          Math.max(
            0,
            Math.floor((startedAt + durationMs - Date.now()) / 1000)
          )
        );
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (attemptId) loadAssessment();
  }, [id, attemptId]);

  const formatTime = (seconds) => {
    if (seconds === null) return "--:--";
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const saveAnswer = async (question = currentQuestion, value = null) => {
    if (!question || !attemptId) return false;

    const answer =
      value !== null ? value : answers[question.id] ?? "";

    try {
      await post(`/assessments/attempts/${attemptId}/answer/`, {
        question: question.id,
        answer_text: answer
      });
      return true;
    } catch (err) {
      setError(errorMessage(err));
      return false;
    }
  };

  const updateAnswer = (value) => {
    if (!currentQuestion) return;

    setAnswers((previous) => ({
      ...previous,
      [currentQuestion.id]: value
    }));
    setSubmitMessage("");
  };

  const selectMcqOption = async (option) => {
    updateAnswer(option);
    setSaving(true);
    await saveAnswer(currentQuestion, option);
    setSaving(false);
  };

  const goToQuestion = async (nextIndex) => {
    if (
      nextIndex < 0 ||
      nextIndex >= questions.length ||
      nextIndex === currentIndex ||
      saving ||
      submitting
    ) {
      return;
    }

    setSaving(true);

    if (currentQuestion?.question_type !== "CODING") {
      await saveAnswer();
    }

    setCurrentIndex(nextIndex);
    setCodeResult(null);
    setSubmitMessage("");
    setSaving(false);
  };

  const runCode = async () => {
    if (!currentQuestion) return;

    setSaving(true);
    setCodeResult(null);

    try {
      const result = await post(
        `/assessments/attempts/${attemptId}/coding-answer/`,
        {
          question: currentQuestion.id,
          language: currentQuestion.coding_language || "PYTHON",
          source_code:
            answers[currentQuestion.id] ||
            currentQuestion.starter_code ||
            ""
        }
      );

      setCodeResult(result);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const submitTest = async (fromTimer = false) => {
    if (submitting) return;

    if (!fromTimer && !allAnswered) {
      setSubmitMessage(
        `You still have ${unansweredCount} unanswered question${
          unansweredCount === 1 ? "" : "s"
        }.`
      );
      return;
    }

    setSubmitting(true);
    setSubmitMessage("");

    try {
      if (currentQuestion?.question_type === "CODING") {
        await saveAnswer();
      } else {
        await saveAnswer();
      }

      const result = await post(
        `/assessments/attempts/${attemptId}/submit/`
      );

      navigate(
        `/assessments/attempts/${result.id || attemptId}/result`,
        { replace: true }
      );
    } catch (err) {
      setError(errorMessage(err));
      setSubmitting(false);
    }
  };

  useEffect(() => {
    if (
      timeLeft === null ||
      attempt?.status === "EVALUATED" ||
      submitting
    ) {
      return;
    }

    if (timeLeft <= 0) {
      if (!autoSubmitted.current) {
        autoSubmitted.current = true;
        submitTest(true);
      }
      return;
    }

    const timer = window.setInterval(() => {
      setTimeLeft((value) =>
        value === null ? null : Math.max(0, value - 1)
      );
    }, 1000);

    return () => window.clearInterval(timer);
  }, [timeLeft, attempt?.status, submitting]);

  if (loading) {
    return <Loading text="Loading assessment..." />;
  }

  if (error && !attempt) {
    return <ErrorState text={error} onRetry={loadAssessment} />;
  }

  if (!assessment || !currentQuestion) {
    return (
      <ErrorState
        text="This assessment does not contain any questions."
        onRetry={loadAssessment}
      />
    );
  }

  const questionAnswered = (question) => {
    const value = answers[question.id];
    return value !== undefined && String(value).trim() !== "";
  };

  const questionState = (question, questionIndex) => {
    if (questionIndex === currentIndex) return "active";
    if (questionAnswered(question)) return "answered";
    return "unanswered";
  };

  const questionOptions = [
    ["A", currentQuestion.option_a],
    ["B", currentQuestion.option_b],
    ["C", currentQuestion.option_c],
    ["D", currentQuestion.option_d]
  ].filter(([, text]) => text);

  const isTimerDanger = timeLeft !== null && timeLeft <= 300;

  return (
    <>
      <div className="exam-page">
        <header className="exam-header">
          <div className="exam-header-left">
            <div className="exam-brand-mark">S</div>
            <div className="exam-title-wrap">
              <h1>{assessment.title}</h1>
              <div className="exam-subtitle">
                <span>{questions.length} Questions</span>
                <span className="exam-separator">•</span>
                <span>{assessment.duration_minutes || 0} Minutes</span>
              </div>
            </div>
          </div>

          <div className="exam-header-right">
            <div className="exam-progress-chip">
              <span>Progress</span>
              <strong>
                {answeredCount}/{questions.length}
              </strong>
            </div>

            <div className={`exam-timer ${isTimerDanger ? "danger" : ""}`}>
              <Clock3 size={17} />
              <div>
                <small>Time left</small>
                <strong>{formatTime(timeLeft)}</strong>
              </div>
            </div>
          </div>
        </header>

        <div className="exam-progress-line">
          <div style={{ width: `${progress}%` }} />
        </div>

        <div className="exam-body">
          <main className="exam-main-column">
            <section className="exam-question-card">
              <div className="exam-question-header">
                <div className="exam-question-meta">
                  <span className="exam-question-index">
                    QUESTION {String(currentIndex + 1).padStart(2, "0")}
                  </span>
                  <span className="exam-type-badge">
                    {currentQuestion.question_type}
                  </span>
                </div>

                <div className="exam-marks">
                  {currentQuestion.marks ?? 0} Mark
                  {Number(currentQuestion.marks ?? 0) === 1 ? "" : "s"}
                </div>
              </div>

              <div className="exam-question-content">
                <h2>{currentQuestion.text}</h2>

                {currentQuestion.question_type === "MCQ" && (
                  <div className="exam-options">
                    {questionOptions.map(([letter, text]) => {
                      const selected =
                        answers[currentQuestion.id] === letter;

                      return (
                        <button
                          key={letter}
                          type="button"
                          className={`exam-option ${
                            selected ? "selected" : ""
                          }`}
                          disabled={saving || submitting}
                          onClick={() => selectMcqOption(letter)}
                        >
                          <span
                            className={`exam-option-radio ${
                              selected ? "selected" : ""
                            }`}
                          >
                            {selected && <i />}
                          </span>

                          <span
                            className={`exam-option-letter ${
                              selected ? "selected" : ""
                            }`}
                          >
                            {letter}
                          </span>

                          <span className="exam-option-text">
                            {text}
                          </span>

                          {selected && (
                            <CheckCircle2
                              size={19}
                              className="exam-option-check"
                            />
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}

                {currentQuestion.question_type === "TRUE_FALSE" && (
                  <div className="exam-options">
                    {["True", "False"].map((value) => {
                      const selected =
                        answers[currentQuestion.id] === value;

                      return (
                        <button
                          key={value}
                          type="button"
                          className={`exam-option ${
                            selected ? "selected" : ""
                          }`}
                          disabled={saving || submitting}
                          onClick={() => selectMcqOption(value)}
                        >
                          <span
                            className={`exam-option-radio ${
                              selected ? "selected" : ""
                            }`}
                          >
                            {selected && <i />}
                          </span>
                          <span
                            className={`exam-option-letter ${
                              selected ? "selected" : ""
                            }`}
                          >
                            {value === "True" ? "T" : "F"}
                          </span>
                          <span className="exam-option-text">
                            {value}
                          </span>
                          {selected && (
                            <CheckCircle2
                              size={19}
                              className="exam-option-check"
                            />
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}

                {currentQuestion.question_type === "CODING" && (
                  <div className="exam-coding">
                    <div className="exam-coding-toolbar">
                      <div>
                        <Code2 size={16} />
                        <strong>Code your solution</strong>
                      </div>
                      <span>
                        {currentQuestion.coding_language || "PYTHON"}
                      </span>
                    </div>

                    {currentQuestion.input_format && (
                      <div className="exam-format-block">
                        <strong>Input</strong>
                        <pre>{currentQuestion.input_format}</pre>
                      </div>
                    )}

                    {currentQuestion.output_format && (
                      <div className="exam-format-block">
                        <strong>Output</strong>
                        <pre>{currentQuestion.output_format}</pre>
                      </div>
                    )}

                    <textarea
                      className="exam-code-editor"
                      value={
                        answers[currentQuestion.id] !== undefined
                          ? answers[currentQuestion.id]
                          : currentQuestion.starter_code || ""
                      }
                      onChange={(event) =>
                        updateAnswer(event.target.value)
                      }
                      spellCheck="false"
                      placeholder="Write your solution here..."
                    />

                    <div className="exam-code-actions">
                      <button
                        type="button"
                        className="exam-secondary-btn"
                        disabled={saving || submitting}
                        onClick={runCode}
                      >
                        <Code2 size={15} />
                        Compile & Run
                      </button>
                    </div>

                    {codeResult && (
                      <div
                        className={
                          codeResult.status === "ACCEPTED"
                            ? "exam-success"
                            : "exam-error"
                        }
                      >
                        {codeResult.status} · {codeResult.passed}/
                        {codeResult.total} tests passed
                        {codeResult.error
                          ? ` · ${codeResult.error}`
                          : ""}
                      </div>
                    )}
                  </div>
                )}

                {currentQuestion.question_type !== "MCQ" &&
                  currentQuestion.question_type !== "TRUE_FALSE" &&
                  currentQuestion.question_type !== "CODING" && (
                    <textarea
                      className="exam-short-answer"
                      value={answers[currentQuestion.id] || ""}
                      onChange={(event) =>
                        updateAnswer(event.target.value)
                      }
                      placeholder="Write your answer here..."
                    />
                  )}
              </div>

              {submitMessage && (
                <div className="exam-warning">
                  <AlertCircle size={17} />
                  <span>{submitMessage}</span>
                </div>
              )}

              {error && <div className="exam-error">{error}</div>}

              <div className="exam-footer-actions">
                <button
                  type="button"
                  className="exam-secondary-btn"
                  disabled={
                    currentIndex === 0 || saving || submitting
                  }
                  onClick={() =>
                    goToQuestion(currentIndex - 1)
                  }
                >
                  <ChevronLeft size={17} />
                  Previous
                </button>

                {currentIndex < questions.length - 1 ? (
                  <button
                    type="button"
                    className="exam-primary-btn"
                    disabled={saving || submitting}
                    onClick={() =>
                      goToQuestion(currentIndex + 1)
                    }
                  >
                    Save & Next
                    <ChevronRight size={17} />
                  </button>
                ) : (
                  <button
                    type="button"
                    className="exam-submit-btn"
                    disabled={!allAnswered || saving || submitting}
                    onClick={() => setShowSubmitConfirm(true)}
                  >
                    <Send size={16} />
                    Submit Test
                  </button>
                )}
              </div>
            </section>
          </main>

          <aside className="exam-sidebar">
            <section className="exam-palette-card">
              <div className="exam-palette-header">
                <div>
                  <h2>Question Palette</h2>
                  <p>Click a number to jump to a question</p>
                </div>

                <div className="exam-palette-score">
                  <strong>{answeredCount}</strong>
                  <span>/{questions.length}</span>
                </div>
              </div>

              <div className="exam-status-row">
                <span>
                  <i className="status-dot current" />
                  Current
                </span>
                <span>
                  <i className="status-dot answered" />
                  Answered
                </span>
                <span>
                  <i className="status-dot unanswered" />
                  Pending
                </span>
              </div>

              <div className="exam-question-grid">
                {questions.map((question, questionIndex) => (
                  <button
                    type="button"
                    key={question.id}
                    className={`exam-question-number ${questionState(
                      question,
                      questionIndex
                    )}`}
                    disabled={saving || submitting}
                    onClick={() => goToQuestion(questionIndex)}
                    aria-label={`Question ${questionIndex + 1}`}
                  >
                    {questionIndex + 1}
                  </button>
                ))}
              </div>
            </section>

            <section className="exam-submit-card">
              <div className="exam-submit-card-icon">
                <Flag size={17} />
              </div>

              <div className="exam-submit-card-copy">
                <h3>Ready to submit?</h3>
                <p>
                  {allAnswered
                    ? "All questions are answered."
                    : `${unansweredCount} question${
                        unansweredCount === 1 ? "" : "s"
                      } remaining.`}
                </p>
              </div>

              <button
                type="button"
                className="exam-submit-btn full"
                disabled={!allAnswered || saving || submitting}
                onClick={() => setShowSubmitConfirm(true)}
              >
                <Send size={16} />
                Submit Test
              </button>
            </section>
          </aside>
        </div>
      </div>

      {showSubmitConfirm && (
        <div className="exam-modal-backdrop">
          <div className="exam-submit-modal">
            <div className="exam-modal-icon">
              <CircleCheck size={25} />
            </div>
            <h2>Submit this test?</h2>
            <p>
              You have answered all {questions.length} questions.
              Once submitted, you cannot change your answers.
            </p>

            <div className="exam-modal-actions">
              <button
                type="button"
                className="exam-secondary-btn"
                disabled={submitting}
                onClick={() => setShowSubmitConfirm(false)}
              >
                Continue Test
              </button>

              <button
                type="button"
                className="exam-submit-btn"
                disabled={submitting}
                onClick={() => {
                  setShowSubmitConfirm(false);
                  submitTest(false);
                }}
              >
                <Send size={16} />
                {submitting ? "Submitting..." : "Yes, Submit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
