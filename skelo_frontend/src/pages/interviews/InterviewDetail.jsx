import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, CheckCircle2, CirclePause, CirclePlay, Clock3, FileText, Mic, MicOff, Send, Sparkles, Video, VideoOff } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { Badge } from "../../components/ModuleCard";
import { ErrorState, Loading } from "../../components/AsyncState";
import { errorMessage, get, post } from "../../services/api";
import "./Interview.css";

function friendlyError(error) {
  const data = error?.response?.data;
  const html = typeof data === "string" && (data.includes("<!DOCTYPE html") || data.includes("<html"));
  if (html || error?.response?.status === 404) {
    return "The Django interview endpoint returned a 404/HTML error page. Install the updated interviews/urls.py and interviews/views.py from the backend update, run migrations, and restart Django.";
  }
  return errorMessage(error, "The interview action could not be completed. Please try again.");
}

function readEvaluation(raw) {
  if (!raw) return null;
  if (typeof raw === "object") return raw;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return { strengths: raw };
  }
}

function formatClock(seconds) {
  const safe = Math.max(0, Number(seconds) || 0);
  return `${String(Math.floor(safe / 60)).padStart(2, "0")}:${String(safe % 60).padStart(2, "0")}`;
}

export default function InterviewDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [interview, setInterview] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answerText, setAnswerText] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [roomError, setRoomError] = useState("");
  const [latestEvaluation, setLatestEvaluation] = useState(null);
  const [report, setReport] = useState(null);
  const [roundComplete, setRoundComplete] = useState(false);
  const [progress, setProgress] = useState({ answered_count: 0, question_limit: 0 });
  const [remaining, setRemaining] = useState(0);
  const [paused, setPaused] = useState(false);
  const [recording, setRecording] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  const [mediaNotice, setMediaNotice] = useState("");
  const recognitionRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const deadlineRef = useRef(null);
  const autoFinishRef = useRef(false);
  const finishBusyRef = useRef(false);
  const finishHandlerRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    setRoomError("");
    try {
      const [interviewData, questionData] = await Promise.all([
        get(`/interviews/${id}/`),
        get(`/interviews/${id}/questions/`),
      ]);
      const questionList = Array.isArray(questionData) ? questionData : questionData?.results || [];
      setInterview(interviewData);
      setQuestions(questionList);
      setReport(interviewData.feedback || null);
      const answered = questionList.filter((question) => Boolean(question.latest_answer?.answer_text?.trim())).length;
      setProgress({ answered_count: answered, question_limit: interviewData.question_limit || 0 });
      setRoundComplete(interviewData.status === "COMPLETED" || (questionList.length > 0 && answered === questionList.length && answered >= (interviewData.question_limit || Infinity)));
      if (interviewData.created_at && !deadlineRef.current) {
        const startedAt = new Date(interviewData.created_at).getTime();
        deadlineRef.current = Number.isFinite(startedAt) ? startedAt + Number(interviewData.duration_minutes || 30) * 60_000 : Date.now() + Number(interviewData.duration_minutes || 30) * 60_000;
      }
    } catch (error) {
      setRoomError(friendlyError(error));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const completedQuestions = useMemo(
    () => questions.filter((question) => Boolean(question.latest_answer?.answer_text?.trim())),
    [questions],
  );
  const currentQuestion = useMemo(
    () => (roundComplete || interview?.status === "COMPLETED" ? null : questions.find((question) => !question.latest_answer?.answer_text?.trim()) || null),
    [questions, roundComplete, interview?.status],
  );
  const questionLimit = progress.question_limit || interview?.question_limit || Math.max(3, Math.min(10, Math.ceil(Number(interview?.duration_minutes || 30) / 5)));
  const questionNumber = currentQuestion ? currentQuestion.order : completedQuestions.length;

  useEffect(() => { setAnswerText(""); }, [currentQuestion?.id]);

  const finishInterview = useCallback(async () => {
    if (finishBusyRef.current || !interview || report) return;
    finishBusyRef.current = true;
    setFinishing(true);
    setRoomError("");
    try {
      const result = await post(`/interviews/${id}/finish/`, {});
      setReport(result.feedback || null);
      setInterview(result.interview || interview);
      setRoundComplete(true);
      setProgress((current) => ({ ...current, answered_count: result.question_count ?? current.answered_count }));
      if (result.report_used_ai === false) {
        setMediaNotice("This report was generated in offline practice mode. Add OPENAI_API_KEY to Django for AI-generated evaluation and personalized reporting.");
      } else {
        setMediaNotice("");
      }
    } catch (error) {
      setRoomError(friendlyError(error));
      autoFinishRef.current = false;
    } finally {
      setFinishing(false);
      finishBusyRef.current = false;
    }
  }, [id, interview, report]);
  finishHandlerRef.current = finishInterview;

  useEffect(() => {
    if (!interview || interview.status === "COMPLETED" || report || !deadlineRef.current) return undefined;
    const tick = () => {
      if (paused) return;
      const seconds = Math.max(0, Math.ceil((deadlineRef.current - Date.now()) / 1000));
      setRemaining(seconds);
      if (seconds === 0 && !autoFinishRef.current) {
        autoFinishRef.current = true;
        finishHandlerRef.current?.();
      }
    };
    tick();
    const timerId = window.setInterval(tick, 1000);
    return () => window.clearInterval(timerId);
  }, [interview?.id, interview?.status, report, paused]);

  useEffect(() => {
    if (interview?.interview_mode !== "VOICE" || !currentQuestion || typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(currentQuestion.question_text);
    utterance.lang = "en-US";
    utterance.rate = 0.96;
    window.speechSynthesis.speak(utterance);
    return () => window.speechSynthesis?.cancel();
  }, [interview?.interview_mode, currentQuestion?.id]);

  useEffect(() => () => {
    try { recognitionRef.current?.stop(); } catch { /* speech recognition may already be stopped */ }
    streamRef.current?.getTracks()?.forEach((track) => track.stop());
    if (typeof window !== "undefined") window.speechSynthesis?.cancel();
  }, []);

  const submitAnswer = async (event) => {
    event?.preventDefault?.();
    if (!currentQuestion || !answerText.trim() || busy) return;
    setBusy(true);
    setRoomError("");
    try {
      const result = await post(`/interviews/${id}/turn/`, {
        question_id: currentQuestion.id,
        answer_text: answerText.trim(),
      });
      setLatestEvaluation({ ...result.evaluation, question_text: currentQuestion.question_text, answer_text: answerText.trim(), used_ai: result.evaluation_used_ai });
      setProgress({ answered_count: result.answered_count || 0, question_limit: result.question_limit || questionLimit });
      setRoundComplete(Boolean(result.round_complete));
      const freshQuestions = await get(`/interviews/${id}/questions/`);
      setQuestions(Array.isArray(freshQuestions) ? freshQuestions : freshQuestions?.results || []);
      setAnswerText("");
      setMediaNotice(result.evaluation_used_ai
        ? "AI feedback is based on the answer content and should be treated as a practice indicator."
        : "Offline practice feedback is a heuristic and does not fact-check technical correctness.");
    } catch (error) {
      setRoomError(friendlyError(error));
    } finally {
      setBusy(false);
    }
  };

  const retryInterview = async () => {
    if (!interview || retrying) return;
    setRetrying(true);
    setRoomError("");
    try {
      const created = await post("/interviews/practice/start/", {
        title: `${interview.company || "General Placement"} · Retry`,
        interview_type: interview.interview_type || "MIXED",
        company: interview.company || "General Placement",
        role: interview.role || "Software Developer",
        difficulty: interview.difficulty || "INTERMEDIATE",
        duration_minutes: Number(interview.duration_minutes || 30),
        interview_mode: interview.interview_mode || "TEXT",
        technical_topics: interview.technical_topics || "",
      });
      nav(`/interviews/${created.id}`);
    } catch (error) {
      setRoomError(friendlyError(error));
    } finally {
      setRetrying(false);
    }
  };

  const startDictation = () => {
    setMediaNotice("");
    const SpeechRecognitionAPI = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
    if (!SpeechRecognitionAPI) {
      setMediaNotice("Speech recognition is not available in this browser. You can still type your answer, or try a Chromium-based browser with microphone permission enabled.");
      return;
    }
    try {
      const recognition = new SpeechRecognitionAPI();
      recognition.lang = "en-US";
      recognition.interimResults = true;
      recognition.continuous = false;
      recognition.onresult = (event) => {
        let transcript = "";
        for (let index = 0; index < event.results.length; index += 1) transcript += `${event.results[index][0]?.transcript || ""} `;
        setAnswerText(transcript.trim());
      };
      recognition.onerror = (event) => setMediaNotice(`Microphone transcription could not continue${event?.error ? ` (${event.error})` : ""}. You can type your answer instead.`);
      recognition.onend = () => setRecording(false);
      recognitionRef.current = recognition;
      recognition.start();
      setRecording(true);
    } catch {
      setMediaNotice("Could not start microphone access. Check the browser permission and type your answer if needed.");
      setRecording(false);
    }
  };

  const stopDictation = () => {
    try { recognitionRef.current?.stop(); } catch { /* no active recognizer */ }
    setRecording(false);
  };

  const toggleCamera = async () => {
    setMediaNotice("");
    if (cameraOn) {
      streamRef.current?.getTracks()?.forEach((track) => track.stop());
      streamRef.current = null;
      setCameraOn(false);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setMediaNotice("Camera preview is not supported here. Browsers generally require HTTPS or localhost and camera permission.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setCameraOn(true);
    } catch {
      setMediaNotice("Camera permission was denied or no camera was found. You can continue the interview without video.");
    }
  };

  if (loading) return <Loading text="Preparing your interview room…" />;
  if (!interview) return <ErrorState text={roomError || "Could not load this interview."} onRetry={load} />;

  const isCompleted = interview.status === "COMPLETED" || Boolean(report);
  const answerCount = Math.max(progress.answered_count, completedQuestions.length);
  const progressPercent = Math.min(100, Math.round((answerCount / Math.max(questionLimit, 1)) * 100));

  return (
    <div className="interview-room-page">
      <button className="interview-back-link" onClick={() => nav("/interviews")}><ArrowLeft size={15} /> Interviews</button>
      <PageHeader eyebrow="SKelo · INTERVIEW ROOM" title={interview.title} subtitle={`${interview.company || "General Placement"} · ${interview.role || "Interview practice"} · ${interview.difficulty || "INTERMEDIATE"}`} action={<Badge tone={isCompleted ? "success" : "info"}>{isCompleted ? "COMPLETED" : "IN PROGRESS"}</Badge>} />

      <section className="room-toolbar">
        <div className="room-mode"><span className="room-ai-dot" /><div><b>{interview.ai_enabled ? "AI interviewer enabled" : "Guided practice room"}</b><small>{interview.ai_enabled ? "Adaptive questions and answer analysis are available" : "Add OPENAI_API_KEY to Django to enable live model evaluation"}</small></div></div>
        <div className={`room-clock ${remaining < 60 && !isCompleted ? "urgent" : ""}`}><Clock3 size={17} /><span>{isCompleted ? "Report ready" : formatClock(remaining)}</span>{!isCompleted && <button title={paused ? "Resume timer" : "Pause timer"} onClick={() => setPaused((value) => !value)}>{paused ? <CirclePlay size={17} /> : <CirclePause size={17} />}</button>}</div>
      </section>

      <div className="room-progress"><div><span>Interview progress</span><b>{Math.min(answerCount, questionLimit)} of {questionLimit} questions</b></div><div className="room-progress-track"><span style={{ width: `${progressPercent}%` }} /></div></div>

      <div className="room-layout">
        <main className="room-main-column">
          {!isCompleted && currentQuestion ? (
            <section className="room-question-panel">
              <div className="room-question-top"><span className="room-question-badge">QUESTION {questionNumber}</span><Badge tone="info">{currentQuestion.category || interview.interview_type}</Badge><span className="room-question-difficulty">{interview.difficulty?.toLowerCase()} level</span></div>
              <div className="room-interviewer-row"><div className="room-interviewer-avatar"><Sparkles size={24} /></div><div><b>SKelo AI Interviewer</b><span>{interview.ai_enabled ? "Listening to your explanation" : "Practice interviewer"}</span></div></div>
              <h2 className="room-question-text">{currentQuestion.question_text}</h2>
              <p className="room-question-hint">Take a moment to structure your answer. Explain your reasoning and add a concrete example where it helps.</p>
              {interview.interview_mode === "VIDEO" && <div className="room-video-preview"><video ref={videoRef} autoPlay muted playsInline className={cameraOn ? "camera-visible" : "camera-hidden"} /><div className="room-video-placeholder" style={{ display: cameraOn ? "none" : "flex" }}><Video size={24} /><span>Camera is optional. Your camera feed stays in this browser preview.</span></div></div>}
              <form className="room-answer-form" onSubmit={submitAnswer}>
                <label htmlFor="interview-answer">Your answer</label>
                <textarea id="interview-answer" value={answerText} onChange={(event) => setAnswerText(event.target.value)} placeholder={interview.interview_mode === "VOICE" ? "Use the microphone button to dictate, or type your answer here…" : "Explain your answer as you would to an interviewer…"} rows={6} maxLength={12000} disabled={busy} />
                <div className="room-answer-meta"><span>{answerText.trim().split(/\s+/).filter(Boolean).length} words · Your answer is saved to this session</span><div className="room-answer-actions">
                  {(interview.interview_mode === "VOICE" || interview.interview_mode === "VIDEO") && <button type="button" className={`room-secondary-btn ${recording ? "recording" : ""}`} onClick={recording ? stopDictation : startDictation} title={recording ? "Stop microphone" : "Dictate answer"}>{recording ? <MicOff size={16} /> : <Mic size={16} />}{recording ? "Stop" : "Dictate"}</button>}
                  {interview.interview_mode === "VIDEO" && <button type="button" className="room-secondary-btn" onClick={toggleCamera}>{cameraOn ? <VideoOff size={16} /> : <Video size={16} />}{cameraOn ? "Turn camera off" : "Enable camera"}</button>}
                  <button type="submit" className="interview-primary" disabled={busy || !answerText.trim()}>{busy ? "Evaluating answer…" : "Submit answer & continue"} <Send size={15} /></button>
                </div></div>
              </form>
            </section>
          ) : !isCompleted ? (
            <section className="room-complete-panel"><div className="room-complete-icon"><CheckCircle2 size={28} /></div><h2>{roundComplete ? "You've reached the end of this round" : "Ready to wrap up?"}</h2><p>Your answers are saved. Generate your report to review strengths, missing concepts, and next steps.</p><button className="interview-primary" onClick={finishInterview} disabled={finishing}>{finishing ? "Generating report…" : "Finish & generate report"} <FileText size={16} /></button></section>
          ) : (
            <section className="room-complete-panel"><div className="room-complete-icon"><CheckCircle2 size={28} /></div><h2>{report ? "Interview report ready" : "Interview marked complete"}</h2><p>{report ? "Your report and question-by-question feedback are saved in your interview history." : "This session was marked complete but has no saved report yet. Generate one from the answers already saved."}</p>{report ? <button className="interview-primary" onClick={() => nav("/interviews")}>Return to interview history <ArrowLeft size={16} /></button> : <button className="interview-primary" onClick={finishInterview} disabled={finishing}>{finishing ? "Generating report…" : "Generate report"} <FileText size={16} /></button>}</section>
          )}

          {roomError && <div className="interview-error" role="alert"><b>Interview action failed</b><span>{roomError}</span><button onClick={() => setRoomError("")}>Dismiss</button></div>}
          {mediaNotice && <div className="room-notice"><span>{mediaNotice}</span><button onClick={() => setMediaNotice("")}>Dismiss</button></div>}
          {latestEvaluation && !isCompleted && <section className="room-feedback-card"><div className="room-feedback-heading"><Sparkles size={18} /><div><b>Feedback on your last answer</b><span>{latestEvaluation.used_ai ? "AI content evaluation" : "Offline practice feedback"}</span></div><strong>{Math.round(Number(latestEvaluation.score || 0))}/100</strong></div><p><b>What worked:</b> {latestEvaluation.strengths}</p><p><b>Improve next:</b> {latestEvaluation.improvement_advice}</p></section>}
        </main>

        <aside className="room-side-column">
          <section className="room-side-card"><div className="room-side-title"><h3>Session details</h3><Clock3 size={16} /></div><div className="room-kv"><span>Interview type</span><b>{interview.interview_type?.replaceAll("_", " ")}</b></div><div className="room-kv"><span>Company</span><b>{interview.company || "General Placement"}</b></div><div className="room-kv"><span>Topics</span><b>{interview.technical_topics || "Role fundamentals"}</b></div><div className="room-kv"><span>Mode</span><b>{interview.interview_mode}</b></div><div className="room-kv"><span>Duration</span><b>{interview.duration_minutes} minutes</b></div></section>
          <section className="room-side-card"><div className="room-side-title"><h3>Conversation</h3><span>{completedQuestions.length} answered</span></div>{completedQuestions.length ? <div className="room-conversation-list">{completedQuestions.map((question) => { const evaluation = readEvaluation(question.latest_answer?.feedback); return <details className="room-conversation-item" key={question.id}><summary><span>Q{question.order}</span><b>{question.question_text}</b><CheckCircle2 size={15} /></summary><p className="room-conversation-answer">{question.latest_answer?.answer_text}</p>{evaluation && <div className="room-mini-evaluation"><span>Practice score <b>{Math.round(Number(evaluation.score || question.latest_answer?.score || 0))}/100</b></span>{evaluation.strengths && <p><b>Strengths:</b> {evaluation.strengths}</p>}{evaluation.missing_concepts && <p><b>Missing concepts:</b> {evaluation.missing_concepts}</p>}{evaluation.technical_mistakes && <p><b>Technical review:</b> {evaluation.technical_mistakes}</p>}{evaluation.expected_answer && <p><b>Expected answer guidance:</b> {evaluation.expected_answer}</p>}{evaluation.improvement_advice && <p><b>Next attempt:</b> {evaluation.improvement_advice}</p>}</div>}</details>; })}</div> : <p className="room-muted-copy">Your completed questions and answers will appear here.</p>}</section>
        </aside>
      </div>

      {report && <section className="room-report-panel"><div className="room-report-header"><div><span className="interview-kicker">YOUR PRACTICE REPORT</span><h2>Review, learn, and try again</h2></div><div className="room-report-actions"><Badge tone="success">Saved report</Badge><button className="interview-primary" onClick={retryInterview} disabled={retrying}>{retrying ? "Preparing retry…" : "Retry this interview"} <CirclePlay size={16} /></button></div></div><div className="room-score-grid"><div><span>Technical accuracy</span><b>{Math.round(Number(report.technical_score || 0))}<small>/100</small></b></div><div><span>Communication clarity</span><b>{Math.round(Number(report.communication_score || 0))}<small>/100</small></b></div><div><span>Overall practice score</span><b>{Math.round(Number(interview.overall_score || ((Number(report.technical_score || 0) + Number(report.communication_score || 0) + Number(report.confidence_score || 0)) / 3)))}<small>/100</small></b></div></div><div className="room-report-columns"><article><h3><CheckCircle2 size={17} /> Strengths</h3><p>{report.strengths || "Review the question-level feedback above for your strengths."}</p></article><article><h3><Sparkles size={17} /> Areas to improve</h3><p>{report.improvement_areas || "Practise the missing concepts listed under each question."}</p></article></div><div className="room-report-overall"><h3>Coach summary</h3><p>{report.overall_feedback || "Use the question-by-question analysis to guide your next attempt."}</p><p className="simulation-note">Scores are practice indicators, not validated predictions of hiring success. The assessment is based on answer content, not appearance, accent or inferred emotion.</p></div></section>}
    </div>
  );
}
