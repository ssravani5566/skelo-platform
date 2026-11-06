import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowRight, ArrowUpRight, Award, Bell, BookOpen, CalendarDays, CheckCircle2,
  ChevronRight, Clock3, Code2, Flame, GraduationCap, PlayCircle, Sparkles,
  Star, Target, Trophy, Zap
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Empty, ErrorState, Loading } from "../components/AsyncState";
import { errorMessage, get, post } from "../services/api";
import "../styles/overview.css";

const num = (value) => Number(value || 0);
const localDate = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

export default function Dashboard({ user }) {
  const [data, setData] = useState(null);
  const [studyPlan, setStudyPlan] = useState(null);
  const [streak, setStreak] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [checkedIn, setCheckedIn] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      // A daily check-in is idempotent on the server: repeat visits on the same
      // local date never increment the streak more than once.
      const streakResult = await post("/gamification/streak/", {}).catch(() => get("/gamification/streak/").catch(() => null));
      const [dashboard, schedule] = await Promise.all([
        get("/dashboard/"),
        get("/schedules/").catch(() => ({ plans: [] })),
      ]);
      setData(dashboard);
      const plans = schedule?.plans || [];
      setStudyPlan(plans.find((plan) => plan.status === "ACTIVE") || plans[0] || null);
      setStreak(num(streakResult?.current_streak ?? streakResult?.current ?? dashboard?.stats?.streak));
      setCheckedIn(Boolean(streakResult));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const stats = data?.stats || {};
  const courses = data?.courses || [];
  const focusTasks = data?.focus_tasks || [];
  const upcoming = data?.upcoming || [];
  const chart = data?.learning_chart || [];
  const fullName = data?.student?.name || user?.name || user?.first_name || "Student";
  const firstName = fullName.trim().split(/\s+/)[0] || "Student";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const lessonsCompleted = courses.reduce((total, course) => total + num(course.completed), 0);
  const overallProgress = courses.length
    ? Math.round(courses.reduce((total, course) => total + num(course.progress), 0) / courses.length)
    : 0;
  const activity = chart.slice(-7).map((item) => ({
    ...item,
    value: num(item.xp) + num(item.lessons) + num(item.submissions),
  }));
  const maxActivity = Math.max(...activity.map((item) => item.value), 1);
  const nextTask = studyPlan?.tasks?.find((task) => !task.completed);
  const todayTasks = useMemo(() => {
    const tasks = studyPlan?.tasks || [];
    const todays = tasks.filter((task) => task.scheduled_date === localDate());
    return (todays.length ? todays : tasks.filter((task) => !task.completed)).slice(0, 3);
  }, [studyPlan]);

  return (
    <div className="overview-page">
      <div className="overview-page-heading">
        <div>
          <span className="overview-eyebrow">SKelo · STUDENT WORKSPACE</span>
          <h1>{greeting}, {firstName}! <span aria-hidden="true">✦</span></h1>
          <p>Your learning journey, progress and next steps — all in one place.</p>
        </div>
        <div className="overview-heading-actions">
          <button className="overview-icon-btn" onClick={() => navigate("/notifications")} aria-label="Notifications"><Bell size={17} /></button>
          <button className="overview-outline-btn" onClick={() => navigate("/courses")}><BookOpen size={15} /> Explore courses</button>
        </div>
      </div>

      {loading ? <Loading text="Loading your learning overview..." /> : error ? <ErrorState text={error} onRetry={load} /> : (
        <>
          <section className="overview-hero">
            <div className="overview-hero-grid" />
            <div className="overview-hero-orb overview-hero-orb-a" />
            <div className="overview-hero-orb overview-hero-orb-b" />
            <div className="overview-hero-copy">
              <span className="overview-hero-kicker"><Sparkles size={13} /> YOUR NEXT MILESTONE STARTS TODAY</span>
              <h2>Small steps.<br /><em>Big career moves.</em></h2>
              <p>Stay consistent, follow your plan and turn today's effort into tomorrow's confidence.</p>
              <div className="overview-hero-actions">
                <button onClick={() => navigate("/schedule")}><CalendarDays size={15} /> Open study schedule <ArrowRight size={15} /></button>
                <button className="overview-hero-link" onClick={() => navigate("/coding")}>Practice coding <ArrowUpRight size={14} /></button>
              </div>
            </div>
            <div className="overview-streak-spotlight">
              <div className="overview-streak-flame"><Flame size={27} fill="currentColor" /></div>
              <span>DAILY STREAK</span>
              <strong>{streak}</strong>
              <small>{streak === 1 ? "day of consistency" : "days of consistency"}</small>
              <div className="overview-streak-note"><CheckCircle2 size={13} /> {checkedIn ? "Today's visit counted" : "Keep showing up daily"}</div>
            </div>
          </section>

          <section className="overview-stat-grid">
            <OverviewStat icon={BookOpen} label="Available courses" value={courses.length} note="Your learning library" tone="violet" />
            <OverviewStat icon={CheckCircle2} label="Lessons completed" value={lessonsCompleted} note="Every topic counts" tone="green" />
            <OverviewStat icon={Zap} label="XP earned" value={num(stats.xp).toLocaleString()} note="Experience points" tone="orange" />
            <OverviewStat icon={Flame} label="Longest streak" value={`${num(stats.longest_streak)} days`} note="Your personal best" tone="pink" />
          </section>

          <div className="overview-main-grid">
            <section className="overview-panel overview-activity-panel">
              <div className="overview-panel-head">
                <div><span className="overview-section-kicker">YOUR MOMENTUM</span><h2>Learning activity</h2><p>Recorded study and practice over the last seven days.</p></div>
                <button onClick={() => navigate("/reports")}>View report <ArrowUpRight size={14} /></button>
              </div>
              <div className="overview-activity-summary"><strong>{activity.reduce((total, item) => total + item.value, 0).toLocaleString()}</strong><span>activity points this week</span></div>
              <div className="overview-activity-chart" role="img" aria-label="Learning activity over the last seven days">
                {(activity.length ? activity : ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((date) => ({ date, value: 0 }))).map((item, index) => {
                  const label = item.date && item.date.includes("-")
                    ? new Date(`${item.date}T00:00:00`).toLocaleDateString(undefined, { weekday: "short" })
                    : item.date;
                  return <div className="overview-activity-day" key={`${item.date}-${index}`}>
                    <div className="overview-activity-track"><i style={{ height: `${Math.max(item.value ? 10 : 5, (item.value / maxActivity) * 100)}%` }} /></div>
                    <small>{label}</small>
                  </div>;
                })}
              </div>
              <div className="overview-chart-legend"><span><i /> Daily learning activity</span><span>Build a little momentum every day</span></div>
            </section>

            <section className="overview-panel overview-progress-panel">
              <div className="overview-panel-head">
                <div><span className="overview-section-kicker">BIG PICTURE</span><h2>Learning progress</h2><p>Your average course completion.</p></div>
                <span className="overview-soft-pill">Overview</span>
              </div>
              <div className="overview-progress-ring" style={{ "--overview-progress": `${overallProgress}%` }}>
                <div><strong>{overallProgress}%</strong><span>complete</span></div>
              </div>
              <div className="overview-progress-caption"><span>Across your courses</span><b>{courses.length} course{courses.length === 1 ? "" : "s"}</b></div>
              <div className="overview-progress-footer">
                <span><GraduationCap size={16} /> Keep your learning plan moving</span>
                <button onClick={() => navigate("/courses")}>View courses <ChevronRight size={14} /></button>
              </div>
            </section>
          </div>

          <section className="overview-plan-banner" onClick={() => navigate("/schedule")} role="button" tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter") navigate("/schedule"); }}>
            <div className="overview-plan-icon"><Target size={21} /></div>
            <div className="overview-plan-copy">
              <span className="overview-section-kicker">PERSONAL STUDY ROADMAP</span>
              <h2>{studyPlan ? studyPlan.course_title : "Build a learning plan that fits your goals"}</h2>
              <p>{studyPlan ? `${studyPlan.completed_count} of ${studyPlan.task_count} topics completed · ${studyPlan.hours_per_day} study hours per day` : "Choose any course, set your daily time and let SKelo organize your next steps."}</p>
            </div>
            {studyPlan ? <div className="overview-plan-progress"><strong>{studyPlan.progress}%</strong><div><i style={{ width: `${studyPlan.progress}%` }} /></div></div> : <span className="overview-plan-cta">Create schedule <ArrowRight size={15} /></span>}
            <ArrowUpRight className="overview-plan-arrow" size={18} />
          </section>

          <div className="overview-lower-grid">
            <section className="overview-panel overview-courses-panel">
              <div className="overview-panel-head">
                <div><span className="overview-section-kicker">KEEP THE MOMENTUM</span><h2>Continue learning</h2><p>Pick up where you left off.</p></div>
                <button onClick={() => navigate("/courses")}>All courses <ArrowUpRight size={14} /></button>
              </div>
              <div className="overview-course-list">
                {courses.slice(0, 3).map((course, index) => <button className="overview-course-item" key={course.id} onClick={() => navigate(`/courses/${course.id}`)}>
                  <span className={`overview-course-symbol tone-${index % 3}`}>{index === 0 ? <GraduationCap size={19} /> : index === 1 ? <Code2 size={19} /> : <BookOpen size={19} />}</span>
                  <span className="overview-course-info"><b>{course.title}</b><small>{num(course.completed)} of {num(course.lessons)} lessons complete</small><i><em style={{ width: `${Math.min(100, num(course.progress))}%` }} /></i></span>
                  <strong>{Math.round(num(course.progress))}%</strong><ChevronRight size={16} />
                </button>)}
                {!courses.length && <Empty title="No course progress yet" text="Browse the course library to start learning." />}
              </div>
            </section>

            <section className="overview-panel overview-focus-panel">
              <div className="overview-panel-head">
                <div><span className="overview-section-kicker">YOUR NEXT STEPS</span><h2>Today's focus</h2><p>Keep your next actions clear and manageable.</p></div>
                <span className="overview-today-pill">Today</span>
              </div>
              {todayTasks.length ? todayTasks.map((task) => <div className={`overview-focus-row ${task.completed ? "is-complete" : ""}`} key={task.id}>
                <span>{task.completed ? <CheckCircle2 size={17} /> : <PlayCircle size={17} />}</span>
                <div><b>{task.title}</b><small>{task.completed ? "Completed" : `${task.duration_minutes} min · Study schedule`}</small></div>
              </div>) : focusTasks.slice(0, 3).map((task, index) => <div className="overview-focus-row" key={`${task.type}-${index}`}>
                <span>{task.type === "assessment" ? <Trophy size={17} /> : task.type === "assignment" ? <Award size={17} /> : <BookOpen size={17} />}</span>
                <div><b>{task.title}</b><small>{task.meta || "Continue your learning"}</small></div>
              </div>)}
              {!todayTasks.length && !focusTasks.length && <div className="overview-focus-empty">Nothing urgent right now. Set a study schedule to plan your next topic.</div>}
              <button className="overview-focus-link" onClick={() => navigate("/schedule")}>View study plan <ArrowRight size={14} /></button>
            </section>
          </div>

          <div className="overview-footer-grid">
            <section className="overview-mini-panel">
              <span className="overview-mini-icon"><Trophy size={18} /></span>
              <div><small>ACHIEVEMENTS</small><b>{num(stats.xp).toLocaleString()} XP collected</b><span>{streak ? `You have shown up ${streak} day${streak === 1 ? "" : "s"} in a row. Keep going!` : "Start a daily streak by checking in and learning."}</span></div>
              <button onClick={() => navigate("/gamification")} aria-label="View achievements"><ArrowUpRight size={16} /></button>
            </section>
            <section className="overview-mini-panel overview-upcoming-panel">
              <span className="overview-mini-icon"><CalendarDays size={18} /></span>
              <div><small>COMING UP</small><b>{upcoming.length ? `${upcoming.length} upcoming item${upcoming.length === 1 ? "" : "s"}` : "You're all caught up"}</b><span>{upcoming[0]?.title || "New deadlines and events will appear here."}</span></div>
              <button onClick={() => navigate(upcoming[0]?.type === "interview" ? "/interviews" : upcoming[0]?.type === "assignment" ? "/assignments" : "/calendar")} aria-label="View upcoming items"><ArrowUpRight size={16} /></button>
            </section>
          </div>
        </>
      )}
    </div>
  );
}

function OverviewStat({ icon: Icon, label, value, note, tone }) {
  return <div className={`overview-stat-card stat-${tone}`}>
    <div className="overview-stat-top"><span>{label}</span><i><Icon size={18} /></i></div>
    <strong>{value}</strong>
    <small>{note}</small>
  </div>;
}
