import React, { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import AdminLayout from "./components/AdminLayout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/auth/ForgotPassword";
import ResetPassword from "./pages/auth/ResetPassword";
import VerifyEmail from "./pages/auth/VerifyEmail";
import Dashboard from "./pages/Dashboard";
import Calendar from "./pages/Calendar";
import Profile from "./pages/Profile";
import SearchResults from "./pages/SearchResults";
import Courses from "./pages/courses/Courses";
import CourseDetail from "./pages/courses/CourseDetail";
import Lesson from "./pages/courses/Lesson";
import Coding from "./pages/coding/Coding";
import ProblemDetail from "./pages/coding/ProblemDetail";
import SubmissionHistory from "./pages/coding/SubmissionHistory";
import Assessments from "./pages/assessments/Assessments";
import AssessmentDetail from "./pages/assessments/AssessmentDetail";
import AssessmentAttempt from "./pages/assessments/AssessmentAttempt";
import AssessmentResult from "./pages/assessments/AssessmentResult";
import Assignments from "./pages/assignments/Assignments";
import AssignmentDetail from "./pages/assignments/AssignmentDetail";
import Codeathons from "./pages/codeathons/Codeathons";
import CodeathonDetail from "./pages/codeathons/CodeathonDetail";
import Leaderboard from "./pages/codeathons/Leaderboard";
import Interviews from "./pages/interviews/Interviews";
import InterviewDetail from "./pages/interviews/InterviewDetail";
import Attendance from "./pages/attendance/Attendance";
import Gamification from "./pages/gamification/Gamification";
import Notifications from "./pages/notifications/Notifications";
import Reports from "./pages/reports/Reports";
import Management from "./pages/management/Management";
import { auth } from "./services/api";

function Protected({ children }) {
  if (!auth.isAuthenticated()) return <Navigate to="/login" replace />;
  let u=null; try { u=JSON.parse(localStorage.getItem("skelo_user")||"null"); } catch {}
  if (u?.role === "ADMIN") return <Navigate to="/admin" replace />;
  if (u?.role === "FACULTY") return <Navigate to="/manage" replace />;
  return <Layout>{children}</Layout>;
}
function RoleProtected({ children }) {
  let u = null;
  try { u = JSON.parse(localStorage.getItem("skelo_user") || "null"); } catch {}
  if (u?.role === "ADMIN") return <AdminLayout>{children}</AdminLayout>;
  if (u?.role === "FACULTY") return <Layout>{children}</Layout>;
  return <Navigate to="/" replace />;
}
export default function App() {
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem("skelo_user") || "null"); } catch { return null; } });
  useEffect(() => { const fn = () => { try { setUser(JSON.parse(localStorage.getItem("skelo_user") || "null")); } catch { setUser(null); } }; window.addEventListener("storage", fn); return () => window.removeEventListener("storage", fn); }, []);
  return <Routes>
    <Route path="/login" element={<Login onLogin={setUser} />} />
    <Route path="/register" element={<Register />} />
    <Route path="/forgot-password" element={<ForgotPassword />} />
    <Route path="/reset-password" element={<ResetPassword />} />
    <Route path="/verify-email" element={<VerifyEmail />} />
    <Route path="/" element={<Protected><Dashboard user={user} /></Protected>} />
    <Route path="/calendar" element={<Protected><Calendar /></Protected>} />
    <Route path="/profile" element={<Protected><Profile user={user} onUpdate={setUser} /></Protected>} />
    <Route path="/search" element={<Protected><SearchResults /></Protected>} />
    <Route path="/courses" element={<Protected><Courses /></Protected>} />
    <Route path="/courses/:id" element={<Protected><CourseDetail /></Protected>} />
    <Route path="/courses/:courseId/lessons/:lessonId" element={<Protected><Lesson /></Protected>} />
    <Route path="/coding" element={<Protected><Coding /></Protected>} />
    <Route path="/coding/problems/:id" element={<Protected><ProblemDetail /></Protected>} />
    <Route path="/coding/submissions" element={<Protected><SubmissionHistory /></Protected>} />
    <Route path="/assessments" element={<Protected><Assessments /></Protected>} />
    <Route path="/assessments/:id" element={<Protected><AssessmentDetail /></Protected>} />
    <Route path="/assessments/:id/attempt" element={<Protected><AssessmentAttempt /></Protected>} />
    <Route path="/assessments/attempts/:attemptId/result" element={<Protected><AssessmentResult /></Protected>} />
    <Route path="/assignments" element={<Protected><Assignments /></Protected>} />
    <Route path="/assignments/:id" element={<Protected><AssignmentDetail /></Protected>} />
    <Route path="/codeathons" element={<Protected><Codeathons /></Protected>} />
    <Route path="/codeathons/:id" element={<Protected><CodeathonDetail /></Protected>} />
    <Route path="/codeathons/:id/leaderboard" element={<Protected><Leaderboard /></Protected>} />
    <Route path="/interviews" element={<Protected><Interviews /></Protected>} />
    <Route path="/interviews/:id" element={<Protected><InterviewDetail /></Protected>} />
    <Route path="/attendance" element={<Protected><Attendance /></Protected>} />
    <Route path="/gamification" element={<Protected><Gamification /></Protected>} />
    <Route path="/notifications" element={<Protected><Notifications /></Protected>} />
    <Route path="/reports" element={<Protected><Reports /></Protected>} />
    <Route path="/manage" element={<RoleProtected><Management /></RoleProtected>} />
    <Route path="/admin" element={<RoleProtected><Management /></RoleProtected>} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
