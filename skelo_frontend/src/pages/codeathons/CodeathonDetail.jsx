
import React, { useEffect, useState } from "react";
import {
  ArrowLeft,
  Code2,
  MapPin,
  Trophy,
  Users,
  Clock3,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import PageHeader from "../../components/PageHeader";
import { Badge, DetailPanel } from "../../components/ModuleCard";
import {
  Empty,
  ErrorState,
  Loading,
} from "../../components/AsyncState";
import { errorMessage, get, post } from "../../services/api";

import "./Codeathons.css";

// Format date and time
const dt = (value) =>
  value
    ? new Date(value).toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "Not specified";

export default function CodeathonDetail() {
  const { id } = useParams();
  const nav = useNavigate();

  // State management
  const [c, setC] = useState(null);
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Fetch codeathon details and problems
  const load = async () => {
    setLoading(true);
    setError("");

    try {
      const [a, p] = await Promise.all([
        get(`/codeathons/${id}/`),
        get(`/codeathons/${id}/problems/`),
      ]);

      setC(a);

      setProblems(
        Array.isArray(p)
          ? p
          : Array.isArray(p?.results)
          ? p.results
          : []
      );
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  // Load on mount and when ID changes
  useEffect(() => {
    load();
  }, [id]);

  // Register for codeathon
  const register = async () => {
    setBusy(true);
    setError("");

    try {
      await post(`/codeathons/${id}/register/`);
      await load();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  // Leave codeathon
  const leave = async () => {
    if (!window.confirm("Leave this event?")) return;

    setBusy(true);
    setError("");

    try {
      await post(`/codeathons/${id}/leave/`);
      await load();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  // Loading state
  if (loading) {
    return <Loading text="Loading codeathon…" />;
  }

  // Error state
  if (error && !c) {
    return <ErrorState text={error} onRetry={load} />;
  }

  if (!c) {
    return (
      <Empty
        title="Codeathon not found"
        text="The requested event could not be found."
      />
    );
  }

  const status = c.status || "Upcoming";

  // Registration availability
  const canRegister =
    !c.registered &&
    c.is_published &&
    new Date() <= new Date(c.start_at) &&
    (!c.registration_opens_at ||
      new Date() >= new Date(c.registration_opens_at)) &&
    (!c.registration_closes_at ||
      new Date() <= new Date(c.registration_closes_at)) &&
    (!c.max_participants ||
      Number(c.participants || 0) < Number(c.max_participants));

  // Event type
  const isHackathon = c.event_type === "HACKATHON";

  return (
    <div className="codeathons-page">

      {/* Back navigation */}
      <button
        className="back-link"
        onClick={() => nav("/codeathons")}
      >
        <ArrowLeft size={15} />
        Codeathons
      </button>

      {/* Event header */}
      <PageHeader
        eyebrow={`SCOTT · ${
          isHackathon ? "HACKATHON" : "CODING COMPETITION"
        }`}
        title={c.title}
        subtitle={
          c.description ||
          "Explore the event schedule, rules and challenge details."
        }
        action={
          <>
            {c.registered ? (
              <button
                className="outline-btn"
                disabled={busy}
                onClick={leave}
              >
                Leave event
              </button>
            ) : (
              <button
                className="primary-btn"
                disabled={!canRegister || busy}
                onClick={register}
              >
                <Users size={16} />

                {busy
                  ? "Saving…"
                  : canRegister
                  ? "Register now"
                  : "Registration unavailable"}
              </button>
            )}
          </>
        }
      />

      {/* Error notice */}
      {error && (
        <div className="codeathon-notice">
          {error}
        </div>
      )}

      {/* Event statistics */}
      <div className="codeathon-stat-grid">
        {[
          ["Event status", status, Clock3],
          [
            "Participants",
            `${c.participants || 0}${
              c.max_participants
                ? ` / ${c.max_participants}`
                : ""
            }`,
            Users,
          ],
          [
            "Format",
            c.participation_type === "TEAM"
              ? "Team event"
              : "Individual",
            ShieldCheck,
          ],
          [
            "Event type",
            isHackathon ? "Hackathon" : "Coding contest",
            Trophy,
          ],
        ].map(([label, value, Icon]) => (
          <div
            className="codeathon-stat"
            key={label}
          >
            <span className="codeathon-stat-icon">
              <Icon size={18} />
            </span>

            <span>
              <small>{label}</small>

              <strong style={{ fontSize: 17 }}>
                {value}
              </strong>
            </span>
          </div>
        ))}
      </div>

      {/* Details grid */}
      <div className="detail-grid">

        {/* Event overview */}
        <DetailPanel title="Event overview">

          <div className="kv">
            <span>Start</span>
            <b>{dt(c.start_at)}</b>
          </div>

          <div className="kv">
            <span>End</span>
            <b>{dt(c.end_at)}</b>
          </div>

          <div className="kv">
            <span>Registration opens</span>
            <b>{dt(c.registration_opens_at)}</b>
          </div>

          <div className="kv">
            <span>Registration closes</span>
            <b>{dt(c.registration_closes_at)}</b>
          </div>

          <div className="kv">
            <span>Difficulty</span>

            <Badge>
              {c.difficulty || "All levels"}
            </Badge>
          </div>

          <div className="kv">
            <span>Mode</span>
            <b>{c.mode || "Online"}</b>
          </div>

          {c.venue && (
            <div className="kv">
              <span>
                <MapPin size={14} />
                Venue
              </span>

              <b>{c.venue}</b>
            </div>
          )}

          {c.category && (
            <div className="kv">
              <span>Category</span>
              <b>{c.category}</b>
            </div>
          )}

        </DetailPanel>

        {/* Challenge details and problems */}
        <DetailPanel
          title={
            isHackathon
              ? "Challenge details"
              : "Problem statements"
          }
        >

          {/* Instructions */}
          {c.instructions ? (
            <p
              style={{
                whiteSpace: "pre-wrap",
                lineHeight: 1.7,
              }}
            >
              {c.instructions}
            </p>
          ) : (
            <p className="muted-text">
              Event instructions will be provided by
              the organizer.
            </p>
          )}

          {/* Hackathon information */}
          {isHackathon && (
            <p className="muted-text">
              Team formation and project submission
              options depend on the organizer's
              enabled workflow.
            </p>
          )}

          {/* UPDATED PROBLEM LIST SECTION */}
          <div className="module-list">
            {problems.length ? (
              problems.map((x) => (
                <div
                  className="lesson-row"
                  key={x.id}
                >
                  <span>
                    <Code2 size={16} />

                    {x.problem?.title ||
                      x.title ||
                      "Problem"}
                  </span>

                  <Badge>
                    {x.points} pts
                  </Badge>
                </div>
              ))
            ) : (
              <Empty
                title="No problems added yet"
                text="The organizer has not attached any coding problems to this event."
              />
            )}
          </div>

        </DetailPanel>

        {/* Prizes and certificates */}
        <DetailPanel title="Prizes and certificates">

          {c.prizes ? (
            <p
              style={{
                whiteSpace: "pre-wrap",
                lineHeight: 1.7,
              }}
            >
              {c.prizes}
            </p>
          ) : (
            <p className="muted-text">
              Prize and certificate information
              has not been published.
            </p>
          )}

          <div className="kv">
            <span>Registration</span>

            <Badge
              tone={
                c.registered
                  ? "success"
                  : "muted"
              }
            >
              {c.registered
                ? "You are registered"
                : "Not registered"}
            </Badge>
          </div>

        </DetailPanel>

      </div>

      {/* Registration confirmation */}
      {c.registered && (
        <div className="codeathon-notice">
          <CheckCircle2
            size={15}
            style={{
              verticalAlign: "middle",
              marginRight: 7,
            }}
          />

          You are registered for this event.
          Return here to access updates and
          the leaderboard.
        </div>
      )}

      {/* Leaderboard */}
      <div className="detail-actions">
        <button
          className="outline-btn"
          onClick={() =>
            nav(`/codeathons/${id}/leaderboard`)
          }
        >
          <Trophy size={15} />
          View leaderboard
        </button>
      </div>

    </div>
  );
}
