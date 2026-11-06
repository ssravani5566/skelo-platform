import React,{useEffect,useMemo,useState} from "react";
import {useSearchParams} from "react-router-dom";
import {BookOpen,Code2,ClipboardCheck,FileText,Trophy,Mic2,CalendarCheck,Medal,Bell,BarChart3,Search,Plus,CheckCircle2,PlayCircle,Clock3,Sparkles,Filter,Download,ExternalLink,Check,Lock,Target,Send} from "lucide-react";
import {get} from "../services/api"; import {demo} from "../data"; import PageHeader from "../components/PageHeader";

const config={
 Courses:{icon:BookOpen,sub:"Your structured learning paths, lessons and progress.",key:"courses",tabs:["All","In progress","Completed"]},
 "Coding Arena":{icon:Code2,sub:"Sharpen problem-solving skills with interview-ready coding practice.",key:"problems",tabs:["All","Unsolved","Solved"]},
 Assessments:{icon:ClipboardCheck,sub:"Timed assessments designed to measure your readiness.",key:"assessments",tabs:["All","Open","Completed"]},
 Assignments:{icon:FileText,sub:"Stay ahead of coursework, submissions and deadlines.",key:"assignments",tabs:["All","Pending","Submitted"]},
 Codeathons:{icon:Trophy,sub:"Compete, collaborate and showcase what you can build.",key:"codeathons",tabs:["All","Open","Upcoming"]},
 Interviews:{icon:Mic2,sub:"Prepare for real conversations with structured mock interviews.",key:"interviews",tabs:["All","Scheduled","Completed"]},
 Attendance:{icon:CalendarCheck,sub:"Track every session and keep your attendance healthy.",key:"attendance",tabs:["All","Present","Late"]},
 Gamification:{icon:Medal,sub:"Turn consistency into XP, badges and visible milestones.",key:"badges",tabs:["All","Earned","Locked"]},
 Notifications:{icon:Bell,sub:"Important updates from your learning workspace.",key:"notifications",tabs:["All","Unread","Read"]},
 Reports:{icon:BarChart3,sub:"A clear snapshot of learning, coding and placement readiness.",key:"stats",tabs:["Overview","Learning","Placement"]}
};

export default function GenericPage({title,apiPath}){
 const c=config[title]||config.Courses,Icon=c.icon,[searchParams]=useSearchParams();
 const [items,setItems]=useState(demo[c.key]||[]),[query,setQuery]=useState(searchParams.get("search")||""),[tab,setTab]=useState("All"),[loading,setLoading]=useState(false),[toast,setToast]=useState("");
 useEffect(()=>{let mounted=true;setLoading(true);get(apiPath,undefined).then(d=>{const a=Array.isArray(d)?d:(d?.results||d?.data||[]);if(mounted&&a.length)setItems(a)}).catch(()=>{}).finally(()=>mounted&&setLoading(false));return()=>{mounted=false}},[apiPath]);
 const filtered=useMemo(()=>items.filter(x=>{const q=query.toLowerCase().trim(); const text=JSON.stringify(x).toLowerCase(); if(q&&!text.includes(q))return false;
   if(tab==="All"||tab==="Overview"||tab==="Learning"||tab==="Placement")return true;
   if(title==="Courses")return tab==="In progress"?Number(x.progress)<100:Number(x.progress)>=100;
   if(title==="Coding Arena")return tab==="Solved"?x.solved:!x.solved;
   if(title==="Notifications")return tab==="Unread"?!x.read:x.read;
   if(title==="Gamification")return tab==="Earned"?x.earned:!x.earned;
   if(["Assignments","Assessments","Codeathons","Interviews","Attendance"].includes(title))return String(x.status||"").toLowerCase()===tab.toLowerCase();
   return true;
 }),[items,query,tab,title]);
 const notify=m=>{setToast(m);setTimeout(()=>setToast(""),2200)};
 const markRead=()=>{if(title!=="Notifications")return;setItems(a=>a.map(x=>({...x,read:true})));notify("All notifications marked as read.")};
 return <div className="module-page">
  {toast&&<div className="toast"><CheckCircle2 size={17}/>{toast}</div>}
  <PageHeader eyebrow={`SCOTT · ${title.toUpperCase()}`} title={title} subtitle={c.sub}
   action={<div className="header-actions">{title==="Notifications"?<button className="outline-btn" onClick={markRead}><Check size={16}/> Mark all read</button>:<button className="primary-btn" onClick={()=>notify(`${title} action is ready.`)}><Plus size={16}/> Add new</button>}</div>}/>
  <section className="module-banner"><div className="module-banner-icon"><Icon size={26}/></div><div><span><Sparkles size={12}/> STUDENT WORKSPACE</span><h2>{title==="Gamification"?"Level up your learning":`Manage your ${title.toLowerCase()}`}</h2><p>{loading?"Syncing with Django backend...":`${filtered.length} ${filtered.length===1?"item":"items"} visible in your workspace.`}</p></div><div className="banner-number"><b>{items.length}</b><span>Total</span></div></section>
  <section className="module-panel">
   <div className="module-toolbar"><div className="tabs">{c.tabs.map(t=><button key={t} className={tab===t?"active":""} onClick={()=>setTab(t)}>{t}</button>)}</div>
    <div className="toolbar-right"><label className="module-search"><Search size={16}/><input placeholder="Search..." value={query} onChange={e=>setQuery(e.target.value)}/></label><button className="icon-btn" onClick={()=>notify("Filter options are applied through the tabs.")}><Filter size={16}/></button><button className="icon-btn" onClick={()=>notify("Export is ready for this view.")}><Download size={16}/></button></div>
   </div>
   <div className="data-area">{title==="Courses"&&<CourseGrid items={filtered}/>} {title==="Coding Arena"&&<CodingGrid items={filtered} notify={notify}/>} {title==="Assessments"&&<AssessmentGrid items={filtered} notify={notify}/>} {title==="Assignments"&&<AssignmentGrid items={filtered}/>} {title==="Codeathons"&&<CodeathonGrid items={filtered} notify={notify}/>} {title==="Interviews"&&<InterviewGrid items={filtered}/>} {title==="Attendance"&&<AttendanceTable items={filtered}/>} {title==="Gamification"&&<BadgeGrid items={filtered}/>} {title==="Notifications"&&<NotificationList items={filtered}/>} {title==="Reports"&&<ReportGrid items={filtered}/>}</div>
   {!filtered.length&&<div className="empty-state"><div><Search size={22}/></div><h3>No results found</h3><p>Try another search or change the selected filter.</p></div>}
  </section>
 </div>
}
function CourseGrid({items}){return <div className="card-grid">{items.map(c=><article className="course-card" key={c.id}><div className={`course-cover ${c.color||"violet"}`}><span>{c.category||"Learning"}</span><BookOpen size={25}/></div><div className="card-body"><div className="card-title-row"><h3>{c.title}</h3><b>{c.progress}%</b></div><p>{c.completed}/{c.lessons} lessons completed</p><div className="progress big"><i style={{width:`${c.progress}%`}}/></div><div className="card-footer"><span><Clock3 size={13}/> Self paced</span><button>Continue <ArrowUp/></button></div></div></article>)}</div>}
function CodingGrid({items,notify}){return <div className="card-grid compact">{items.map(x=><article className="problem-card" key={x.id}><div className="problem-top"><span className={`difficulty ${String(x.difficulty).toLowerCase()}`}>{x.difficulty}</span><span>{x.points} XP</span></div><h3>{x.title}</h3><p>{x.topic}</p><div className="problem-footer">{x.solved?<span className="status success"><CheckCircle2 size={14}/> Solved</span>:<button className="action-link" onClick={()=>notify(`Opening ${x.title}`)}><PlayCircle size={15}/> Practice</button>}<span>#{String(x.id).padStart(2,"0")}</span></div></article>)}</div>}
function AssessmentGrid({items,notify}){return <div className="card-grid compact">{items.map(x=><article className="assessment-card" key={x.id}><div className="assessment-icon"><ClipboardCheck/></div><span className={`status ${x.status==="Completed"?"success":"info"}`}>{x.status}</span><h3>{x.title}</h3><p>{x.type} assessment</p><div className="assessment-meta"><span>{x.questions} questions</span><span>{x.duration}</span></div><button onClick={()=>notify(x.status==="Completed"?"Result details opened.":"Assessment launched.")}>{x.status==="Completed"?"View result":"Start assessment"} <ExternalLink size={14}/></button></article>)}</div>}
function AssignmentGrid({items}){return <div className="table-wrap"><table className="data-table"><thead><tr><th>Assignment</th><th>Course</th><th>Due</th><th>Status</th><th>Score</th></tr></thead><tbody>{items.map(x=><tr key={x.id}><td><b>{x.title}</b></td><td>{x.course}</td><td>{x.due}</td><td><Status value={x.status}/></td><td><b>{x.score}</b></td></tr>)}</tbody></table></div>}
function CodeathonGrid({items,notify}){return <div className="card-grid compact">{items.map(x=><article className="event-card" key={x.id}><div className="event-art"><Trophy size={29}/><span>{x.status}</span></div><div className="card-body"><h3>{x.name}</h3><p><CalendarCheck size={14}/>{x.date}</p><div className="event-stats"><span><b>{x.participants}</b> participants</span><span><b>{x.prize}</b> prize</span></div><button onClick={()=>notify(`${x.name} registration selected.`)}>View challenge <ArrowUp/></button></div></article>)}</div>}
function InterviewGrid({items}){return <div className="card-grid compact">{items.map(x=><article className="interview-card" key={x.id}><div className="interview-avatar"><Mic2/></div><div><span className="status info">{x.status}</span><h3>{x.title}</h3><p>{x.role}</p><div className="interview-time"><Clock3 size={14}/>{x.date}</div></div><button className="icon-btn"><ExternalLink size={16}/></button></article>)}</div>}
function AttendanceTable({items}){return <div className="table-wrap"><table className="data-table"><thead><tr><th>Date</th><th>Session</th><th>Trainer</th><th>Status</th></tr></thead><tbody>{items.map((x,i)=><tr key={i}><td><b>{x.date}</b></td><td>{x.session}</td><td>{x.trainer}</td><td><Status value={x.status}/></td></tr>)}</tbody></table></div>}
function BadgeGrid({items}){return <div className="badge-grid">{items.map((x,i)=><article className={`badge-card ${x.earned?"earned":"locked"}`} key={i}><div className="badge-medal">{x.icon||"🏆"}{!x.earned&&<Lock size={13}/>}</div><h3>{x.name}</h3><p>{x.desc}</p><span className={`status ${x.earned?"success":"muted"}`}>{x.earned?"Earned":"Locked"}</span></article>)}</div>}
function NotificationList({items}){return <div className="notification-list">{items.map(x=><article className={`notification-card ${!x.read?"unread":""}`} key={x.id}><div className="notification-icon"><Bell size={17}/></div><div><div className="notification-title"><h3>{x.title}</h3>{!x.read&&<i/>}</div><p>{x.message}</p><span>{x.type} · {x.time}</span></div><button className="icon-btn"><ChevronRight/></button></article>)}</div>}
function ReportGrid({items}){const fallback=items.length?items:[{metric:"Learning completion",current:"68%",target:"80%",trend:"+12%"},{metric:"Coding solved",current:"27",target:"40",trend:"+4"},{metric:"Attendance",current:"92%",target:"90%",trend:"Above target"},{metric:"Placement readiness",current:"74%",target:"85%",trend:"+8%"}];return <div className="report-grid">{fallback.map((x,i)=><article className="report-card" key={i}><div><span>{x.metric||x.name}</span><BarChart3 size={18}/></div><b>{x.current}</b><p>Target <strong>{x.target}</strong></p><em>{x.trend}</em></article>)}</div>}
function Status({value}){const cls=String(value||"").toLowerCase().includes("present")||String(value||"").toLowerCase().includes("submitted")||String(value||"").toLowerCase().includes("completed")?"success":String(value||"").toLowerCase().includes("late")||String(value||"").toLowerCase().includes("pending")?"warning":"info";return <span className={`status ${cls}`}>{value||"—"}</span>}
function ArrowUp(){return <ExternalLink size={14}/>}