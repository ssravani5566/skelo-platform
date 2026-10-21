import React, { useEffect, useMemo, useState } from "react";
import { CalendarDays, ChevronRight, Search, Trophy, Users, Radio, CheckCircle2, BellRing, SlidersHorizontal } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { Empty, ErrorState, Loading } from "../../components/AsyncState";
import { Badge } from "../../components/ModuleCard";
import { errorMessage, get, unwrapList } from "../../services/api";
import "./Codeathons.css";

const tabs = ["Explore Codeathons", "Upcoming", "Live Now", "My Codeathons", "Completed"];
const statusOf = (c) => c.status || "Upcoming";
const when = (v) => v ? new Date(v).toLocaleString([], {dateStyle:"medium",timeStyle:"short"}) : "Not specified";
export default function Codeathons() {
  const [items,setItems]=useState([]), [q,setQ]=useState(""), [tab,setTab]=useState(tabs[0]);
  const [type,setType]=useState("ALL"), [difficulty,setDifficulty]=useState("ALL"), [mode,setMode]=useState("ALL");
  const [loading,setLoading]=useState(true), [error,setError]=useState(""), [notice,setNotice]=useState("");
  const nav=useNavigate();
  const load=()=>{setLoading(true);setError("");get(`/codeathons/?q=${encodeURIComponent(q)}`).then(d=>setItems(unwrapList(d))).catch(e=>setError(errorMessage(e))).finally(()=>setLoading(false));};
  useEffect(()=>{const t=setTimeout(load,220);return()=>clearTimeout(t)},[q]);
  const filtered=useMemo(()=>items.filter(c=>{
    const st=statusOf(c).toLowerCase();
    if(tab==="Upcoming" && !(st.includes("upcoming")||st==="open"||st==="registration open"||st==="registration closed")) return false;
    if(tab==="Live Now" && st!=="live" && st!=="open") return false;
    if(tab==="My Codeathons" && !c.registered) return false;
    if(tab==="Completed" && st!=="completed") return false;
    if(type!=="ALL" && (c.event_type||"CODING")!==type) return false;
    if(difficulty!=="ALL" && (c.difficulty||"ALL")!==difficulty) return false;
    if(mode!=="ALL" && (c.mode||"ONLINE")!==mode) return false;
    return true;
  }),[items,tab,type,difficulty,mode]);
  const stats=useMemo(()=>({
    upcoming:items.filter(c=>["upcoming","open","registration open","registration closed"].includes(statusOf(c).toLowerCase())).length,
    registered:items.filter(c=>c.registered).length,
    live:items.filter(c=>["live","open"].includes(statusOf(c).toLowerCase()) && new Date(c.start_at)<=new Date()).length,
    completed:items.filter(c=>statusOf(c).toLowerCase()==="completed").length
  }),[items]);
  const notify=()=>nav("/notifications");
  return <div className="codeathons-page">
    <PageHeader eyebrow="SCOTT · BUILD · COMPETE · GROW" title="Codeathons" subtitle="Find coding competitions and hackathons, challenge yourself, and build projects with the SCOTT community."/>
    <div className="codeathon-stat-grid">
      {[["Upcoming events",stats.upcoming,CalendarDays],["My registrations",stats.registered,Users],["Live now",stats.live,Radio],["Completed",stats.completed,CheckCircle2]].map(([label,value,Icon])=><div className="codeathon-stat" key={label}><span className="codeathon-stat-icon"><Icon size={19}/></span><span><small>{label}</small><strong>{value}</strong></span></div>)}
    </div>
    <div className="codeathon-controls">
      <div className="codeathon-search"><Search size={17}/><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search events by title or description…"/></div>
      <div className="codeathon-filter"><SlidersHorizontal size={16}/><select aria-label="Event type" value={type} onChange={e=>setType(e.target.value)}><option value="ALL">All event types</option><option value="CODING">Coding competition</option><option value="HACKATHON">Hackathon</option></select>
      <select aria-label="Difficulty" value={difficulty} onChange={e=>setDifficulty(e.target.value)}><option value="ALL">All difficulty</option><option value="EASY">Easy</option><option value="MEDIUM">Medium</option><option value="HARD">Hard</option></select>
      <select aria-label="Mode" value={mode} onChange={e=>setMode(e.target.value)}><option value="ALL">All modes</option><option value="ONLINE">Online</option><option value="OFFLINE">Offline</option><option value="HYBRID">Hybrid</option></select></div>
    </div>
    <div className="codeathon-tabs" role="tablist">{tabs.map(t=><button role="tab" aria-selected={tab===t} className={tab===t?"active":""} key={t} onClick={()=>setTab(t)}>{t}{t==="My Codeathons"&&stats.registered>0?<span>{stats.registered}</span>:null}</button>)}</div>
    {notice&&<div className="codeathon-notice">{notice}</div>}
    {loading?<Loading text="Loading codeathons from SCOTT…"/>:error?<ErrorState text={error} onRetry={load}/>:!filtered.length?<div className="codeathon-empty"><div className="codeathon-empty-icon"><Trophy size={30}/></div><h3>{tab==="My Codeathons"?"You haven't registered for an event yet":"No published codeathons available"}</h3><p>{tab==="My Codeathons"?"Explore upcoming competitions and register to keep them in your workspace.":"New coding competitions and hackathons will appear here as soon as they are published."}</p><button className="outline-btn" onClick={notify}><BellRing size={15}/> Open notifications</button></div>:<div className="codeathon-card-grid">{filtered.map(c=><article className="codeathon-event-card" key={c.id}>
      <div className={`codeathon-card-banner ${c.event_type==="HACKATHON"?"hackathon":""}`}><div className="codeathon-banner-mark">{c.event_type==="HACKATHON"?"BUILD / SHIP":"CODE / SOLVE"}</div><Trophy size={28}/><span className="codeathon-status">{statusOf(c)}</span></div>
      <div className="codeathon-card-content"><div className="codeathon-tags"><span>{c.event_type==="HACKATHON"?"Hackathon":"Coding competition"}</span><span>{c.difficulty||"All levels"}</span><span>{c.mode||"Online"}</span></div><h3>{c.title}</h3><p className="codeathon-description">{c.description||"Explore the challenge details, eligibility and event schedule."}</p><div className="codeathon-meta"><span><CalendarDays size={15}/>{when(c.start_at)}</span><span><Users size={15}/>{c.participants||0}{c.max_participants?` / ${c.max_participants}`:""} participants</span></div>{c.prizes&&<div className="codeathon-prize"><Trophy size={14}/>{c.prizes}</div>}<div className="codeathon-card-footer">{c.registered&&<span className="registered-label"><CheckCircle2 size={14}/> Registered</span>}<button className="action-link" onClick={()=>nav(`/codeathons/${c.id}`)}>View details <ChevronRight size={15}/></button></div></div>
    </article>)}</div>}
  </div>;
}

