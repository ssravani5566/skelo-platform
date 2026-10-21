import React,{useEffect,useMemo,useState} from "react";
import {NavLink,useLocation,useNavigate} from "react-router-dom";
import {Activity,ArrowUpRight,BarChart3,Bell,BookOpen,CalendarCheck,ChevronRight,ClipboardCheck,Code2,Command,FileText,LayoutDashboard,LogOut,Medal,Menu,Mic2,Sparkles,Trophy,UserCircle,X,Search,Settings2} from "lucide-react";
import {auth,errorMessage,get,health} from "../services/api";
const links=[
 ["Overview","/",LayoutDashboard],["Courses","/courses",BookOpen],["Coding Arena","/coding",Code2],["Assessments","/assessments",ClipboardCheck],["Assignments","/assignments",FileText],["Codeathons","/codeathons",Trophy],["Interviews","/interviews",Mic2],["Attendance","/attendance",CalendarCheck],["Achievements","/gamification",Medal],["Notifications","/notifications",Bell],["Reports","/reports",BarChart3]
];
export default function Layout({children}){
 const [open,setOpen]=useState(false),[search,setSearch]=useState(""),[status,setStatus]=useState("Connecting..."); const navigate=useNavigate(); const location=useLocation();
 const user=useMemo(()=>{try{return JSON.parse(localStorage.getItem("skelo_user")||"{}")}catch{return {}}},[location.pathname]);
 const name=user.name||[user.first_name,user.last_name].filter(Boolean).join(" ")||"Student", initials=name.split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase();
 useEffect(()=>{let live=true; const check=async()=>{try{const d=await health(); if(live)setStatus(d?.status==="ok"?"Connected":"Degraded")}catch{if(live)setStatus("Offline")}};check();const id=setInterval(check,30000);return()=>{live=false;clearInterval(id)}},[]);
 const logout=async()=>{await auth.logout();navigate("/login",{replace:true})};
 const submitSearch=e=>{e.preventDefault();const q=search.trim();if(q)navigate(`/search?q=${encodeURIComponent(q)}`)};
 const pageName=links.find(x=>x[1]===location.pathname)?.[0]|| (location.pathname.startsWith("/courses/")?"Courses":location.pathname.startsWith("/coding/")?"Coding Arena":"Workspace");
 return <div className="app-shell"><div className={`mobile-overlay ${open?"show":""}`} onClick={()=>setOpen(false)}/><aside className={`sidebar ${open?"open":""}`}>
   <div className="brand"><div className="brand-mark"><Sparkles size={20}/></div><div className="brand-copy"><b>SCOTT</b><span>Student Career OS</span></div><button className="mobile-close" onClick={()=>setOpen(false)}><X/></button></div>
   <div className="side-label">LEARNING HUB</div><nav>{links.map(([label,path,Icon])=><NavLink key={path} to={path} end={path==="/"} onClick={()=>setOpen(false)} className={({isActive})=>`nav-item ${isActive?"active":""}`}><span className="nav-icon"><Icon size={18}/></span><span>{label}</span>{label==="Notifications"&&<span className="nav-live-dot"/>}</NavLink>)}</nav>
   {(user.role==="ADMIN"||user.role==="FACULTY")&&<><div className="side-label">MANAGEMENT</div><NavLink to={user.role==="ADMIN"?"/admin":"/manage"} className={({isActive})=>`nav-item ${isActive?"active":""}`} onClick={()=>setOpen(false)}><span className="nav-icon"><Settings2 size={18}/></span><span>{user.role==="ADMIN"?"Admin Console":"Management"}</span></NavLink></>}
   <div className="sidebar-bottom"><div className="side-tip"><Sparkles size={16}/><div><b>Real-time workspace</b><span>All data is loaded from Django.</span></div></div><NavLink to="/profile" className="mini-profile" onClick={()=>setOpen(false)}><div className="avatar">{initials}</div><div><b>{name}</b><small>{user.role||"STUDENT"}</small></div><ChevronRight size={16}/></NavLink><button className="logout" onClick={logout}><LogOut size={17}/> Sign out</button></div>
 </aside><main className="main"><header className="topbar"><button className="menu" onClick={()=>setOpen(true)}><Menu/></button><div className="breadcrumb"><span>SCOTT</span><i>/</i>{pageName}</div><form className="global-search" onSubmit={submitSearch}><Search size={16}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search courses, problems..."/><kbd><Command size={11}/> K</kbd></form><div className="top-actions"><div className={`api-status ${status.toLowerCase()}`}><span/>{status}</div><NavLink to="/profile" className="top-avatar" title="Profile">{initials}</NavLink></div></header><section className="content">{children}</section></main></div>
}
