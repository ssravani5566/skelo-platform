import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  Mail,
  Lock,
  ArrowRight,
  Sparkles,
  Eye,
  EyeOff,
  ShieldCheck,
  GraduationCap,
  Code2,
  Trophy,
  BriefcaseBusiness,
  CheckCircle2,
  Target,
  Zap,
  Star,
  X,
  KeyRound,
} from "lucide-react";

import { auth } from "../services/api";
import "../styles/login.css";

export default function Login({ onLogin }) {
  const navigate = useNavigate();

  /* =========================================================
     LOGIN STATE
  ========================================================= */

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  /* =========================================================
     FORGOT PASSWORD STATE
  ========================================================= */

  const [showForgotPassword, setShowForgotPassword] =
    useState(false);

  const [forgotEmail, setForgotEmail] = useState("");

  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotError, setForgotError] = useState("");
  const [forgotSuccess, setForgotSuccess] = useState("");

  const [isEmailFocused, setIsEmailFocused] = useState(false);

  /* =========================================================
     REMEMBERED EMAIL
  ========================================================= */

  useEffect(() => {
    const savedEmail = localStorage.getItem(
      "scott_remember_email"
    );

    if (savedEmail) {
      setForm((prev) => ({
        ...prev,
        email: savedEmail,
      }));

      setRememberMe(true);
    }
  }, []);

  /* =========================================================
     UPDATE LOGIN FIELD
  ========================================================= */

  const updateField = (field, value) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));

    setError("");
    setSuccess("");
  };

  /* =========================================================
     LOGIN
  ========================================================= */

  const submit = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess("");

    const identifier = form.email.trim();
    const password = form.password;

    if (!identifier || !password) {
      setError("Please enter your email / Admin ID and password.");
      return;
    }

    setLoading(true);

    try {
      // The backend accepts either a student's email or an Admin ID.
      // Keep the payload explicit so Admin login never gets confused with
      // the email-only student validation used by older versions.
      const response = await auth.login({
        identifier,
        password,
      });

      /* Remember email only */
      if (rememberMe) {
        localStorage.setItem(
          "scott_remember_email",
          identifier
        );
      } else {
        localStorage.removeItem(
          "scott_remember_email"
        );
      }

      const isAdmin = response.user?.role === "ADMIN";
      const isFaculty = response.user?.role === "FACULTY";

      setSuccess(
        isAdmin
          ? "Admin login successful. Opening Admin Console..."
          : "Welcome back! Redirecting to your dashboard..."
      );

      onLogin?.(response.user);

      // Admins must enter the management console after authentication.
      // Students continue to the normal learning dashboard.
      setTimeout(() => {
        navigate(isAdmin || isFaculty ? "/admin" : "/");
      }, 250);
    } catch (err) {
      console.error("Login error:", err);

      const backendError =
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.email?.[0] ||
        err.response?.data?.password?.[0];

      setError(
        backendError ||
          "Incorrect email or password. Please check your details and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  /* =========================================================
     OPEN FORGOT PASSWORD
  ========================================================= */

  const openForgotPassword = () => {
    setForgotEmail(form.email.trim());

    setForgotError("");
    setForgotSuccess("");

    setShowForgotPassword(true);
  };

  /* =========================================================
     CLOSE FORGOT PASSWORD
  ========================================================= */

  const closeForgotPassword = () => {
    if (forgotLoading) return;

    setShowForgotPassword(false);

    setForgotError("");
    setForgotSuccess("");
  };

  /* =========================================================
     SEND RESET LINK
  ========================================================= */

  const handleForgotPassword = async (e) => {
    e.preventDefault();

    setForgotError("");
    setForgotSuccess("");

    const email = forgotEmail.trim();

    if (!email) {
      setForgotError(
        "Please enter your registered email address."
      );
      return;
    }

    if (!email.includes("@")) {
      setForgotError(
        "Please enter a valid email address."
      );
      return;
    }

    setForgotLoading(true);

    try {
      /*
       * REAL PASSWORD RESET API
       *
       * Your services/api.js should contain:
       *
       * forgotPassword: (email) =>
       *   api.post("/auth/forgot-password/", { email })
       */

      await auth.forgotPassword({
        email,
      });

      setForgotSuccess(
        "Reset instructions have been sent to your email."
      );
    } catch (err) {
      console.error(
        "Forgot password error:",
        err
      );

      const backendError =
        err.response?.data?.detail ||
        err.response?.data?.email?.[0];

      setForgotError(
        backendError ||
          "Unable to send reset instructions. Please try again."
      );
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="scott-login-page">

      {/* =====================================================
          BACKGROUND
      ===================================================== */}

      <div className="scott-grid-background" />

      <div className="scott-glow scott-glow-one" />
      <div className="scott-glow scott-glow-two" />
      <div className="scott-glow scott-glow-three" />

      {/* =====================================================
          FLOATING ICONS
      ===================================================== */}

      <div className="floating-icon floating-icon-one">
        <Code2 size={19} />
      </div>

      <div className="floating-icon floating-icon-two">
        <Target size={19} />
      </div>

      <div className="floating-icon floating-icon-three">
        <GraduationCap size={19} />
      </div>

      <div className="floating-icon floating-icon-four">
        <Trophy size={18} />
      </div>

      {/* =====================================================
          MAIN LOGIN CONTAINER
      ===================================================== */}

      <div className="scott-login-container">

        {/* ===================================================
            LEFT SIDE
        =================================================== */}

        <section className="scott-company-panel">

          <div className="scott-company-content">

            {/* BRAND */}

            <div className="scott-brand">

              <div className="scott-brand-logo">
                <Sparkles size={21} />
              </div>

              <div className="scott-brand-name">
                <strong>SCOTT</strong>
                <span>
                  Student Career & Learning Platform
                </span>
              </div>

            </div>

            {/* BRAND STATEMENT */}

            <div className="scott-brand-statement">
              Learn smarter. Build stronger. Get career-ready.
            </div>

            {/* BADGE */}

            <div className="scott-company-badge">
              <span className="scott-live-dot" />
              Student Career Platform
            </div>

            {/* HERO */}

            <div className="scott-company-heading">

              <h1>
                Learn.
                <br />
                Practice.
                <br />
                <span>Get Career-Ready.</span>
              </h1>

              <p>
                Build industry skills, practice real coding
                challenges, prepare for assessments and gain
                the confidence you need to launch your career.
              </p>

            </div>

            {/* =================================================
                CAREER JOURNEY
            ================================================= */}

            <div className="scott-journey-section">

              <div className="scott-section-label">
                YOUR JOURNEY WITH SCOTT
              </div>

              <div className="scott-journey">

                <div className="scott-journey-item">

                  <div className="scott-journey-number">
                    01
                  </div>

                  <div className="scott-journey-icon">
                    <GraduationCap size={17} />
                  </div>

                  <div className="scott-journey-content">
                    <strong>Learn</strong>
                    <span>
                      Build your foundation
                    </span>
                  </div>

                </div>

                <div className="scott-journey-line" />

                <div className="scott-journey-item">

                  <div className="scott-journey-number">
                    02
                  </div>

                  <div className="scott-journey-icon purple">
                    <Code2 size={17} />
                  </div>

                  <div className="scott-journey-content">
                    <strong>Practice</strong>
                    <span>
                      Solve real challenges
                    </span>
                  </div>

                </div>

                <div className="scott-journey-line" />

                <div className="scott-journey-item">

                  <div className="scott-journey-number">
                    03
                  </div>

                  <div className="scott-journey-icon orange">
                    <Trophy size={17} />
                  </div>

                  <div className="scott-journey-content">
                    <strong>Compete</strong>
                    <span>
                      Test your skills
                    </span>
                  </div>

                </div>

                <div className="scott-journey-line" />

                <div className="scott-journey-item">

                  <div className="scott-journey-number">
                    04
                  </div>

                  <div className="scott-journey-icon green">
                    <BriefcaseBusiness size={17} />
                  </div>

                  <div className="scott-journey-content">
                    <strong>Prepare</strong>
                    <span>
                      Get interview ready
                    </span>
                  </div>

                </div>

              </div>
            </div>

            {/* =================================================
                ACHIEVEMENT CARD
            ================================================= */}

            <div className="scott-achievement-card">

              <div className="scott-achievement-icon">
                <Star size={20} />
              </div>

              <div className="scott-achievement-main">

                <strong>
                  Your career journey starts here
                </strong>

                <span>
                  Learn, practice and build confidence
                  for your next opportunity.
                </span>

              </div>

              <div className="scott-achievement-stats">

                <div>
                  <strong>10K+</strong>
                  <span>Learners</span>
                </div>

                <div>
                  <strong>50+</strong>
                  <span>Tracks</span>
                </div>

              </div>

            </div>

            {/* FEATURES */}

            <div className="scott-feature-mini-grid">

              <div className="scott-mini-feature">
                <CheckCircle2 size={15} />
                <span>
                  Skill-based learning
                </span>
              </div>

              <div className="scott-mini-feature">
                <CheckCircle2 size={15} />
                <span>
                  Coding practice
                </span>
              </div>

              <div className="scott-mini-feature">
                <CheckCircle2 size={15} />
                <span>
                  Mock assessments
                </span>
              </div>

              <div className="scott-mini-feature">
                <CheckCircle2 size={15} />
                <span>
                  Interview preparation
                </span>
              </div>

            </div>

            {/* STATS */}

            <div className="scott-company-stats">

              <div>
                <strong>10K+</strong>
                <span>Students</span>
              </div>

              <div>
                <strong>50+</strong>
                <span>Learning Tracks</span>
              </div>

              <div>
                <strong>100+</strong>
                <span>Coding Challenges</span>
              </div>

            </div>

            <div className="scott-company-note">
              <Zap size={14} />
              <span>
                SCOTT learning platform overview.
              </span>
            </div>

          </div>

        </section>

        {/* ===================================================
            RIGHT LOGIN PANEL
        =================================================== */}

        <section className="scott-login-panel">

          <div className="scott-login-card">

            {/* MOBILE BRAND */}

            <div className="scott-mobile-brand">

              <div className="scott-brand-logo">
                <Sparkles size={19} />
              </div>

              <div className="scott-brand-name">
                <strong>SCOTT</strong>
                <span>
                  Student Career & Learning Platform
                </span>
              </div>

            </div>

            {/* LOGIN HEADER */}

            <div className="scott-login-heading">

              <div className="scott-heading-label">
                STUDENT LOGIN
              </div>

              <h2>
                Welcome
                <span> back.</span>
              </h2>

              <p>
                Continue your learning and career journey.
              </p>

            </div>

            {/* =================================================
                LOGIN FORM
            ================================================= */}

            <form
              className="scott-login-form"
              onSubmit={submit}
              noValidate
            >

              {/* EMAIL */}

              <div className="scott-form-group">

                <label htmlFor="email">
                  Email address
                </label>

                <div className="scott-input-wrapper">

                  <Mail
                    className="scott-input-icon"
                    size={18}
                  />

                  <input
                    id="email"
                    name="email"
                    type="text"
                    autoComplete="username"
                    placeholder="student@example.com or Admin"
                    value={form.email}
                    onFocus={() =>
                      setIsEmailFocused(true)
                    }
                    onBlur={() =>
                      setIsEmailFocused(false)
                    }
                    onChange={(e) =>
                      updateField(
                        "email",
                        e.target.value
                      )
                    }
                    aria-label="Email address"
                  />

                  <div
                    className={`scott-cartoon-avatar ${
                      isEmailFocused
                        ? "eyes-closed"
                        : ""
                    }`}
                    aria-hidden="true"
                  >

                    <div className="cartoon-face">

                      <div className="cartoon-eyes">
                        <div className="cartoon-eye" />
                        <div className="cartoon-eye" />
                      </div>

                      <div className="cartoon-blush left" />
                      <div className="cartoon-blush right" />

                      <div className="cartoon-mouth" />

                    </div>

                  </div>

                </div>

              </div>

              {/* PASSWORD */}

              <div className="scott-form-group">

                <div className="scott-label-row">

                  <label htmlFor="password">
                    Password
                  </label>

                  <button
                    type="button"
                    className="scott-forgot-button"
                    onClick={openForgotPassword}
                  >
                    Forgot password?
                  </button>

                </div>

                <div className="scott-input-wrapper">

                  <Lock
                    className="scott-input-icon"
                    size={18}
                  />

                  <input
                    id="password"
                    name="password"
                    type={
                      showPassword
                        ? "text"
                        : "password"
                    }
                    autoComplete="current-password"
                    placeholder="Enter your password"
                    value={form.password}
                    onChange={(e) =>
                      updateField(
                        "password",
                        e.target.value
                      )
                    }
                    aria-label="Password"
                  />

                  <button
                    type="button"
                    className="scott-password-toggle"
                    onClick={() =>
                      setShowPassword(
                        (prev) => !prev
                      )
                    }
                    aria-label={
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                  >
                    {showPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>

                </div>

              </div>

              {/* REMEMBER ME */}

              <div className="scott-form-options">

                <label className="scott-remember">

                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) =>
                      setRememberMe(
                        e.target.checked
                      )
                    }
                  />

                  <span className="scott-custom-checkbox">
                    <CheckCircle2 size={13} />
                  </span>

                  <span>
                    Remember me
                  </span>

                </label>

                <span className="scott-login-helper">
                  Secure student access
                </span>

              </div>

              {/* ERROR */}

              {error && (
                <div
                  className="scott-message scott-error"
                  role="alert"
                >
                  <span className="scott-message-icon">
                    !
                  </span>

                  <p>{error}</p>
                </div>
              )}

              {/* SUCCESS */}

              {success && (
                <div
                  className="scott-message scott-success"
                  role="status"
                >
                  <span className="scott-success-icon">
                    <CheckCircle2 size={16} />
                  </span>

                  <p>{success}</p>
                </div>
              )}

              {/* LOGIN BUTTON */}

              <button
                type="submit"
                className="scott-login-button"
                disabled={loading}
              >

                {loading ? (
                  <>
                    <span className="scott-spinner" />
                    <span>
                      Signing you in...
                    </span>
                  </>
                ) : (
                  <>
                    <span>
                      Sign in
                    </span>

                    <ArrowRight
                      className="scott-button-arrow"
                      size={18}
                    />
                  </>
                )}

              </button>

            </form>

            {/* DIVIDER */}

            <div className="scott-auth-method">
              <span />
              <p>
                Secure account authentication
              </p>
              <span />
            </div>

            {/* REGISTER */}

            <div className="scott-register-section">

              <span>
                Don't have an account?
              </span>

              <Link to="/register">
                Create student account
                <ArrowRight size={14} />
              </Link>

            </div>

            {/* SECURITY */}

            <div className="scott-security">

              <div className="scott-security-icon">
                <ShieldCheck size={16} />
              </div>

              <div>
                <strong>
                  Secure student authentication
                </strong>

                <span>
                  Your SCOTT account protects
                  your learning journey.
                </span>
              </div>

            </div>

          </div>

        </section>

      </div>

      {/* =====================================================
          FOOTER
      ===================================================== */}

      <div className="scott-login-footer">

        <span>
          © 2026 SCOTT Student Platform
        </span>

        <span className="footer-dot">
          •
        </span>

        <span>
          Live student portal · Django API connected
        </span>

      </div>

      {/* =====================================================
          FORGOT PASSWORD MODAL
      ===================================================== */}

      {showForgotPassword && (
        <div
          className="scott-modal-overlay"
          onMouseDown={(e) => {
            if (
              e.target === e.currentTarget &&
              !forgotLoading
            ) {
              closeForgotPassword();
            }
          }}
        >

          <div
            className="scott-forgot-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="forgot-password-title"
          >

            {/* CLOSE */}

            <button
              type="button"
              className="scott-modal-close"
              onClick={closeForgotPassword}
              disabled={forgotLoading}
              aria-label="Close password reset"
            >
              <X size={19} />
            </button>

            {/* ICON */}

            <div className="scott-forgot-icon">
              <KeyRound size={25} />
            </div>

            {/* TITLE */}

            <div className="scott-forgot-heading">

              <div className="scott-heading-label">
                PASSWORD RESET
              </div>

              <h3 id="forgot-password-title">
                Reset your password
              </h3>

              <p>
                Enter your registered email address
                and we'll send you instructions to
                create a new password.
              </p>

            </div>

            {/* SUCCESS */}

            {forgotSuccess ? (
              <div className="scott-reset-success">

                <div className="scott-reset-success-icon">
                  <CheckCircle2 size={22} />
                </div>

                <strong>
                  Check your inbox
                </strong>

                <p>
                  {forgotSuccess}
                </p>

                <button
                  type="button"
                  onClick={closeForgotPassword}
                  className="scott-reset-back-button"
                >
                  Back to login
                </button>

              </div>
            ) : (

              /* RESET FORM */

              <form
                className="scott-forgot-form"
                onSubmit={handleForgotPassword}
              >

                <div className="scott-form-group">

                  <label htmlFor="forgot-email">
                    Registered email address
                  </label>

                  <div className="scott-input-wrapper">

                    <Mail
                      className="scott-input-icon"
                      size={18}
                    />

                    <input
                      id="forgot-email"
                      type="email"
                      placeholder="student@example.com"
                      value={forgotEmail}
                      onChange={(e) => {
                        setForgotEmail(
                          e.target.value
                        );

                        setForgotError("");
                      }}
                      autoComplete="email"
                      autoFocus
                      required
                    />

                  </div>

                </div>

                {/* ERROR */}

                {forgotError && (
                  <div
                    className="scott-message scott-error"
                    role="alert"
                  >
                    <span className="scott-message-icon">
                      !
                    </span>

                    <p>
                      {forgotError}
                    </p>
                  </div>
                )}

                {/* SEND BUTTON */}

                <button
                  type="submit"
                  className="scott-login-button"
                  disabled={forgotLoading}
                >

                  {forgotLoading ? (
                    <>
                      <span className="scott-spinner" />

                      <span>
                        Sending instructions...
                      </span>
                    </>
                  ) : (
                    <>
                      <span>
                        Send reset instructions
                      </span>

                      <ArrowRight
                        size={18}
                      />
                    </>
                  )}

                </button>

                {/* BACK */}

                <button
                  type="button"
                  className="scott-modal-back"
                  onClick={closeForgotPassword}
                  disabled={forgotLoading}
                >
                  ← Back to login
                </button>

              </form>

            )}

          </div>

        </div>
      )}

    </div>
  );
}