import React, { useEffect, useState } from "react";
import {
  ArrowUpDown,
  Check,
  CheckCircle2,
  ExternalLink,
  Filter,
  Globe2,
  LoaderCircle,
  Search,
  Shuffle,
} from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { Empty, ErrorState, Loading } from "../../components/AsyncState";
import { Badge } from "../../components/ModuleCard";
import { errorMessage, del, get, post, unwrapList } from "../../services/api";

const PLATFORMS = [
  { key: "LEETCODE", label: "LeetCode", url: "https://leetcode.com/problemset/all/" },
  { key: "HACKERRANK", label: "HackerRank", url: "https://www.hackerrank.com/domains/algorithms" },
  { key: "CODECHEF", label: "CodeChef", url: "https://www.codechef.com/practice" },
  { key: "CODEFORCES", label: "Codeforces", url: "https://codeforces.com/problemset" },
  { key: "GEEKSFORGEEKS", label: "GeeksforGeeks", url: "https://www.geeksforgeeks.org/explore" },
];

function openExternal(url) {
  if (!url || !/^https:\/\//i.test(url)) return;
  window.open(url, "_blank", "noopener,noreferrer");
}

function formatMetric(problem) {
  if (problem.acceptance_rate != null) return `${Number(problem.acceptance_rate).toFixed(1)}%`;
  if (problem.success_rate != null) return `${Number(problem.success_rate).toFixed(1)}%`;
  if (problem.platform === "CODEFORCES" && problem.platform_metric_value != null) {
    const n = Number(problem.platform_metric_value);
    return `${n.toLocaleString()} solved`;
  }
  return "—";
}

function platformColorClass(platform) {
  return `platform-dot platform-${String(platform || "external").toLowerCase()}`;
}

export default function Coding() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const [q, setQ] = useState(params.get("search") || "");
  const [source, setSource] = useState("EXTERNAL");
  const [platform, setPlatform] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [solved, setSolved] = useState("");
  const [sort, setSort] = useState("number_asc");
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [solvedCount, setSolvedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [progressBusy, setProgressBusy] = useState(null);
  const [catalogSyncing, setCatalogSyncing] = useState(false);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const query = new URLSearchParams();
      if (q.trim()) query.set("q", q.trim());
      if (source) query.set("source", source);
      if (platform) query.set("platform", platform);
      if (difficulty) query.set("difficulty", difficulty);
      if (solved) query.set("solved", solved);
      query.set("sort", sort);
      query.set("page", String(page));
      query.set("page_size", "100");
      const data = await get(`/coding/problems/?${query.toString()}`);
      setCatalogSyncing(Boolean(data?.catalog_sync?.syncing));
      const rows = unwrapList(data);
      setItems(rows);
      setCount(Number(data?.count ?? rows.length));
      setPages(Number(data?.pages ?? (data?.count ? Math.ceil(Number(data.count) / 100) : 0)));
      setSolvedCount(Number(data?.solved_count ?? rows.filter((x) => x.solved === true).length));
    } catch (e) {
      setCatalogSyncing(false);
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
  }, [q, source, platform, difficulty, solved, sort]);

  useEffect(() => {
    const id = setTimeout(load, 250);
    return () => clearTimeout(id);
  }, [q, source, platform, difficulty, solved, sort, page]);

  const toggleSolved = async (problem) => {
    setProgressBusy(problem.id);
    try {
      if (problem.solved) {
        await del(`/coding/problems/${problem.id}/progress/`);
      } else {
        await post(`/coding/problems/${problem.id}/progress/`, {});
      }
      await load();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setProgressBusy(null);
    }
  };

  const externalMode = source === "EXTERNAL";

  return (
    <div className="coding-page">
      <PageHeader
        eyebrow="SCOTT · CODING ARENA"
        title="Coding questions"
        subtitle="Browse real questions from coding platforms and solve each question on its original website."
        action={
          <button className="outline-btn" onClick={() => nav("/coding/submissions")}>
            <CheckCircle2 size={15} /> Submission history
          </button>
        }
      />

      <section className="coding-source-bar">
        <div className="coding-source-copy">
          <div className="mini-eyebrow"><Globe2 size={13} /> EXTERNAL PLATFORM CATALOG</div>
          <strong>Questions stay on their original platform</strong>
          <span>SCOTT stores public metadata, your local progress and the official question URL.</span>
        </div>
        <div className="coding-platform-links">
          {PLATFORMS.map((p) => (
            <button key={p.key} className="platform-mini-link" onClick={() => openExternal(p.url)} title={`Open ${p.label} problem set`}>
              <span className={platformColorClass(p.key)} /> {p.label} <ExternalLink size={12} />
            </button>
          ))}
        </div>
      </section>

      <section className="coding-toolbar-shell">
        <div className="coding-platform-tabs">
          <button className={source === "EXTERNAL" && !platform ? "active" : ""} onClick={() => { setSource("EXTERNAL"); setPlatform(""); }}>
            All external
          </button>
          {PLATFORMS.map((p) => (
            <button key={p.key} className={platform === p.key ? "active" : ""} onClick={() => { setSource("EXTERNAL"); setPlatform(p.key); }}>
              {p.label}
            </button>
          ))}
          <button className={source === "LOCAL" ? "active" : ""} onClick={() => { setSource("LOCAL"); setPlatform(""); setSolved(""); }}>
            SCOTT practice
          </button>
        </div>

        <div className="coding-search-row">
          <label className="coding-search-box">
            <Search size={16} />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search questions" />
          </label>
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} aria-label="Difficulty">
            <option value="">All difficulty</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
          </select>
          <select value={solved} onChange={(e) => setSolved(e.target.value)} aria-label="Solved status">
            <option value="">All status</option>
            <option value="true">Solved</option>
            <option value="false">Unsolved</option>
          </select>
          <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort questions">
            <option value="number_asc">Question no. ↑</option>
            <option value="number_desc">Question no. ↓</option>
            <option value="acceptance_desc">Acceptance ↓</option>
            <option value="acceptance_asc">Acceptance ↑</option>
            <option value="title_asc">Title A–Z</option>
          </select>
          <button className="icon-filter-btn" title="Refresh live catalog" onClick={load} disabled={loading}>
            {loading ? <LoaderCircle className="spin" size={17} /> : <ArrowUpDown size={17} />}
          </button>
        </div>
      </section>

      {catalogSyncing && !items.length && (
        <div className="coding-sync-banner">
          Loading real questions from the coding platforms… Refresh after the first sync completes.
        </div>
      )}

      <div className="coding-summary-row">
        <div className="coding-count">
          <strong>{solvedCount}/{count}</strong> Solved
        </div>
        <div className="coding-count-actions">
          <span><Filter size={13} /> {count.toLocaleString()} questions match your filters</span>
          <Shuffle size={14} />
        </div>
      </div>

      {loading ? (
        <Loading text="Loading real coding questions..." />
      ) : error ? (
        <ErrorState text={error} onRetry={load} />
      ) : !items.length ? (
        <Empty
          title={catalogSyncing ? "Live catalog is syncing…" : (q.trim() || platform || difficulty || solved) ? "No questions match your filters" : externalMode ? "No live external questions are available" : "No SCOTT coding questions"}
          text={catalogSyncing
            ? "SCOTT is loading real question metadata from the selected coding platforms. Refresh this page in a moment."
            : (q.trim() || platform || difficulty || solved)
              ? "Clear the filters to see more questions, or switch to another coding platform."
              : externalMode
                ? "The live catalog could not be loaded. Check the Django server connection and try Refresh again."
                : "No published SCOTT coding questions are available."}
        />
      ) : (
        <section className="coding-list-panel">
          <div className="coding-list-header">
            <span>#</span>
            <span>Question</span>
            <span>Platform</span>
            <span>Acceptance / Success</span>
            <span>Difficulty</span>
            <span>My status</span>
            <span />
          </div>
          {items.map((problem, index) => {
            const external = Boolean(problem.is_external);
            const number = problem.external_number || (index + 1);
            return (
              <article className="coding-row" key={problem.id}>
                <div className="coding-number">{number}</div>
                <div className="coding-question-cell">
                  {external ? (
                    <button className="coding-question-link" onClick={() => openExternal(problem.external_url)}>
                      <span className="question-title">{problem.title}</span>
                      {problem.topic && <span className="question-topic">{problem.topic}</span>}
                    </button>
                  ) : (
                    <button className="coding-question-link" onClick={() => nav(`/coding/problems/${problem.id}`)}>
                      <span className="question-title">{problem.title}</span>
                      {problem.topic && <span className="question-topic">{problem.topic}</span>}
                    </button>
                  )}
                </div>
                <div className="coding-platform-cell">
                  {external ? <><span className={platformColorClass(problem.platform)} />{problem.platform_label}</> : "SCOTT"}
                  {problem.premium && <span className="premium-badge">Premium</span>}
                </div>
                <div className="coding-metric-cell">
                  <strong>{formatMetric(problem)}</strong>
                  {problem.platform_metric_label && <span>{problem.platform_metric_label}</span>}
                </div>
                <div className="coding-difficulty-cell">
                  <span className={`difficulty-text ${String(problem.difficulty).toLowerCase()}`}>
                    {problem.difficulty_label || problem.difficulty}
                  </span>
                </div>
                <div className="coding-status-cell">
                  {external ? (
                    <button
                      className={`external-solved-toggle ${problem.solved ? "done" : ""}`}
                      onClick={() => toggleSolved(problem)}
                      disabled={progressBusy === problem.id}
                      title={problem.solved ? "Mark unsolved" : "Mark solved after completing it on the original platform"}
                    >
                      {progressBusy === problem.id ? <LoaderCircle className="spin" size={15} /> : problem.solved ? <Check size={15} /> : null}
                      {problem.solved ? "Solved" : "To do"}
                    </button>
                  ) : problem.solved ? (
                    <span className="status success">Solved</span>
                  ) : (
                    <span className="status muted">To do</span>
                  )}
                </div>
                <div className="coding-action-cell">
                  {external ? (
                    <button className="solve-external-btn" onClick={() => openExternal(problem.external_url)}>
                      Solve <ExternalLink size={14} />
                    </button>
                  ) : (
                    <button className="solve-external-btn" onClick={() => nav(`/coding/problems/${problem.id}`)}>
                      Open
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </section>
      )}

      {!loading && !error && count > 0 && pages > 1 && (
        <div className="coding-pagination">
          <span>Page {page} of {pages}</span>
          <div>
            <button onClick={() => setPage(1)} disabled={page === 1}>First</button>
            <button onClick={() => setPage((v) => Math.max(1, v - 1))} disabled={page === 1}>Previous</button>
            <button onClick={() => setPage((v) => Math.min(pages, v + 1))} disabled={page === pages}>Next</button>
            <button onClick={() => setPage(pages)} disabled={page === pages}>Last</button>
          </div>
        </div>
      )}
    </div>
  );
}
