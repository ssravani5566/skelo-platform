import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  User,
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
  CheckCircle2,
} from "lucide-react";

import { auth } from "../services/api";
import "../styles/login.css";

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    password: "",
    role: "STUDENT",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const update = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setError("");
  };

  const submit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.first_name.trim() || !form.username.trim() || !form.email.trim() || !form.password) {
      setError("Please fill in all required fields.");
      return;
    }

    if (!form.email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }

    if (form.password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      await auth.register({
        ...form,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        username: form.username.trim(),
        email: form.email.trim(),
      });

      navigate("/login", {
        replace: true,
        state: { registered: true },
      });
    } catch (err) {
      console.error("Registration error:", err);

      const data = err.response?.data;
      const backendError =
        data?.detail ||
        data?.email?.[0] ||
        data?.username?.[0] ||
        data?.password?.[0] ||
        (typeof data === "string" ? data : null);

      setError(
        backendError ||
          "Registration failed. Please check your details and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scott-login-page scott-register-page">
      <div className="scott-grid-background" />
      <div className="scott-glow scott-glow-one" />
      <div className="scott-glow scott-glow-two" />
      <div className="scott-glow scott-glow-three" />

      <div className="floating-icon floating-icon-one">
        <Code2 size={19} />
      </div>
      <div className="floating-icon floating-icon-two">
        <GraduationCap size={19} />
      </div>
      <div className="floating-icon floating-icon-three">
        <Trophy size={18} />
      </div>

      <div className="scott-login-container scott-register-container">
        <section className="scott-company-panel">
          <div className="scott-company-content scott-register-company-content">
            <div className="scott-brand">
              <div className="scott-brand-logo">
                <Sparkles size={21} />
              </div>
              <div className="scott-brand-name">
                <strong>SCOTT</strong>
                <span>Student Career & Learning Platform</span>
              </div>
            </div>

            <div className="scott-brand-statement">
              Learn smarter. Build stronger. Get career-ready.
            </div>

            <div className="scott-company-badge">
              <span className="scott-live-dot" />
              JOIN THE LEARNING COMMUNITY
            </div>

            <div className="scott-company-heading scott-register-hero">
              <h1>
                Start.
                <br />
                Learn.
                <br />
                <span>Build Your Future.</span>
              </h1>

              <p>
                Create your student account and unlock structured learning,
                coding practice, assessments and career preparation in one place.
              </p>
            </div>

            <div className="scott-register-benefits">
              <div>
                <CheckCircle2 size={17} />
                <span>Personal learning dashboard</span>
              </div>
              <div>
                <CheckCircle2 size={17} />
                <span>Hands-on coding practice</span>
              </div>
              <div>
                <CheckCircle2 size={17} />
                <span>Assessment & interview preparation</span>
              </div>
              <div>
                <CheckCircle2 size={17} />
                <span>Career-focused learning tracks</span>
              </div>
            </div>

            <div className="scott-register-security-note">
              <ShieldCheck size={17} />
              <div>
                <strong>Secure student account</strong>
                <span>Your details are used only for your SCOTT learning profile.</span>
              </div>
            </div>
          </div>
        </section>

        <section className="scott-login-panel scott-register-panel">
          <div className="scott-login-card scott-register-card">
            <div className="scott-mobile-brand">
              <div className="scott-brand-logo">
                <Sparkles size={19} />
              </div>
              <div className="scott-brand-name">
                <strong>SCOTT</strong>
                <span>Student Career & Learning Platform</span>
              </div>
            </div>

            <div className="scott-login-heading scott-register-heading">
              <div className="scott-heading-label">CREATE ACCOUNT</div>
              <h2>
                Join <span>SCOTT.</span>
              </h2>
              <p>Create your student profile and begin your learning journey.</p>
            </div>

            <form className="scott-login-form" onSubmit={submit} noValidate>
              <div className="scott-register-name-grid">
                <div className="scott-form-group">
                  <label htmlFor="first_name">First name *</label>
                  <div className="scott-input-wrapper">
                    <User className="scott-input-icon" size={18} />
                    <input
                      id="first_name"
                      name="first_name"
                      value={form.first_name}
                      onChange={update}
                      placeholder="Kiran"
                      autoComplete="given-name"
                      required
                    />
                  </div>
                </div>

                <div className="scott-form-group">
                  <label htmlFor="last_name">Last name</label>
                  <div className="scott-input-wrapper">
                    <User className="scott-input-icon" size={18} />
                    <input
                      id="last_name"
                      name="last_name"
                      value={form.last_name}
                      onChange={update}
                      placeholder="K"
                      autoComplete="family-name"
                    />
                  </div>
                </div>
              </div>

              <div className="scott-form-group">
                <label htmlFor="username">Username *</label>
                <div className="scott-input-wrapper">
                  <User className="scott-input-icon" size={18} />
                  <input
                    id="username"
                    name="username"
                    value={form.username}
                    onChange={update}
                    placeholder="Choose a username"
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              <div className="scott-form-group">
                <label htmlFor="register-email">Email address *</label>
                <div className="scott-input-wrapper">
                  <Mail className="scott-input-icon" size={18} />
                  <input
                    id="register-email"
                    name="email"
                    type="email"
                    value={form.email}
                    onChange={update}
                    placeholder="student@example.com"
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <div className="scott-form-group">
                <label htmlFor="register-password">Password *</label>
                <div className="scott-input-wrapper">
                  <Lock className="scott-input-icon" size={18} />
                  <input
                    id="register-password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={form.password}
                    onChange={update}
                    placeholder="Minimum 8 characters"
                    autoComplete="new-password"
                    minLength={8}
                    required
                  />
                  <button
                    type="button"
                    className="scott-password-toggle"
                    onClick={() => setShowPassword((prev) => !prev)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="scott-message scott-error" role="alert">
                  <span className="scott-message-icon">!</span>
                  <p>{error}</p>
                </div>
              )}

              <button
                type="submit"
                className="scott-login-button"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="scott-spinner" />
                    <span>Creating your account...</span>
                  </>
                ) : (
                  <>
                    <span>Create student account</span>
                    <ArrowRight className="scott-button-arrow" size={18} />
                  </>
                )}
              </button>
            </form>

            <div className="scott-auth-method">
              <span />
              <p>Already registered?</p>
              <span />
            </div>

            <div className="scott-register-section scott-back-to-login">
              <span>Already have an account?</span>
              <Link to="/login">
                Sign in
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </section>
      </div>

      <div className="scott-login-footer">
        <span>© 2026 SCOTT Student Platform</span>
        <span className="footer-dot">•</span>
        <span>Secure student registration</span>
      </div>
    </div>
  );
}
