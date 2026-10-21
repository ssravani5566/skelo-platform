
import React, { useEffect, useState } from "react";
import { ExternalLink } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import { Empty, ErrorState, Loading } from "../components/AsyncState";
import { errorMessage, get } from "../services/api";

export default function SearchResults() {
  const [params] = useSearchParams();
  const q = params.get("q") || "";
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    get(`/search/?q=${encodeURIComponent(q)}`)
      .then(setData)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [q]);

  if (loading) return <Loading text="Searching the platform..." />;
  if (error) return <ErrorState text={error} />;

  const sections = [
    ["courses", "Courses"],
    ["problems", "SCOTT coding problems"],
    ["external_problems", "External coding platforms"],
    ["assessments", "Assessments"],
    ["assignments", "Assignments"],
    ["codeathons", "Codeathons"],
    ["interviews", "Interviews"],
  ];

  const total = sections.reduce((n, [key]) => n + (data[key]?.length || 0), 0);

  return (
    <div>
      <PageHeader
        eyebrow="SCOTT · SEARCH"
        title={`Search: ${q}`}
        subtitle="Results come from published/authorized backend records across the platform."
      />

      {!total ? (
        <Empty title="No matches" text="No published records matched your search." />
      ) : (
        sections.map(([key, label]) => data[key]?.length ? (
          <section className="search-group" key={key}>
            <h2>{label}</h2>
            <div className="search-results">
              {data[key].map((x) => key === "external_problems" ? (
                <div key={x.id} className="search-result external-search-result">
                  <Link to={`/coding/problems/${x.id}`}>
                    <b>{x.title}</b>
                    <span>{x.platform_label} · {x.difficulty} · {x.topic || "Coding"}</span>
                  </Link>
                  <a href={x.external_url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${x.title} on ${x.platform_label}`}>
                    <ExternalLink size={14} />
                  </a>
                </div>
              ) : (
                <Link key={x.id} to={routeFor(key, x.id)} className="search-result">
                  <b>{x.title}</b>
                  <span>{x.category || x.topic || x.assessment_type || x.status || x.due_date || ""}</span>
                </Link>
              ))}
            </div>
          </section>
        ) : null)
      )}
    </div>
  );
}

function routeFor(key, id) {
  return {
    courses: `/courses/${id}`,
    problems: `/coding/problems/${id}`,
    assessments: `/assessments/${id}`,
    assignments: `/assignments/${id}`,
    codeathons: `/codeathons/${id}`,
    interviews: `/interviews/${id}`,
  }[key] || "/";
}
