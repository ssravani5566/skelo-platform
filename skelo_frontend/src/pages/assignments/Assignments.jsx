import React, { useEffect, useState } from "react";
import {
  CalendarDays,
  ChevronRight,
  Clock3,
  FileText,
  Search
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { Empty, ErrorState, Loading } from "../../components/AsyncState";
import { Badge } from "../../components/ModuleCard";
import { errorMessage, get, unwrapList } from "../../services/api";
import "./Assignments.css";

export default function Assignments() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const nav = useNavigate();

  const load = () => {
    setLoading(true);
    setError("");

    get(`/assignments/?page_size=100`)
      .then((data) => {
        let result = unwrapList(data);

        if (q) {
          result = result.filter((item) =>
            JSON.stringify(item)
              .toLowerCase()
              .includes(q.toLowerCase())
          );
        }

        if (status) {
          result = result.filter((item) => {
            const current = item.submission?.status;
            return status === "pending"
              ? !current
              : current?.toLowerCase() === status;
          });
        }

        setItems(result);
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const timer = setTimeout(load, 250);
    return () => clearTimeout(timer);
  }, [q, status]);

  return (
    <div className="assignments-page">
      <PageHeader
        eyebrow="SCOTT · LEARNING HUB"
        title="Assignments"
        subtitle="Complete your assignments and submit your work before the due date."
      />

      <div className="assignment-toolbar">
        <label className="assignment-search">
          <Search size={15} />
          <input
            value={q}
            onChange={(event) => setQ(event.target.value)}
            placeholder="Search assignments..."
          />
        </label>

        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          <option value="">All assignments</option>
          <option value="pending">Pending</option>
          <option value="submitted">Submitted</option>
          <option value="evaluated">Evaluated</option>
          <option value="late">Late</option>
        </select>
      </div>

      {loading ? (
        <Loading text="Loading assignments..." />
      ) : error ? (
        <ErrorState text={error} onRetry={load} />
      ) : !items.length ? (
        <Empty
          title="No assignments"
          text="No published assignments are available right now."
        />
      ) : (
        <div className="assignment-list-grid">
          {items.map((item) => (
            <article className="assignment-card" key={item.id}>
              <div className="assignment-card-top">
                <div className="assignment-file-icon">
                  <FileText size={20} />
                </div>

                <Badge
                  tone={
                    item.submission?.status === "EVALUATED"
                      ? "success"
                      : item.submission?.status
                      ? "warning"
                      : "muted"
                  }
                >
                  {item.submission?.status || "Pending"}
                </Badge>
              </div>

              <h2>{item.title}</h2>

              <p>
                {item.description ||
                  "Complete this assignment and submit your work."}
              </p>

              <div className="assignment-card-info">
                <span>
                  <FileText size={14} />
                  {item.max_marks} marks
                </span>

                <span>
                  <Clock3 size={14} />
                  {item.duration_minutes || "—"} min
                </span>

                <span>
                  <CalendarDays size={14} />
                  {item.due_date
                    ? new Date(item.due_date).toLocaleDateString()
                    : "No due date"}
                </span>
              </div>

              <div className="assignment-card-footer">
                <span>
                  {item.submission?.score != null
                    ? `${item.submission.score}/${item.max_marks} marks`
                    : "Not submitted"}
                </span>

                <button
                  type="button"
                  className="assignment-open-button"
                  onClick={() =>
                    nav(`/assignments/${item.id}`)
                  }
                >
                  Open
                  <ChevronRight size={15} />
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
