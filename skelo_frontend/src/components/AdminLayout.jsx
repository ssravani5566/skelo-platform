import React,{useEffect,useMemo,useState} from "react";
import {NavLink,useLocation,useNavigate} from "react-router-dom";
import {BarChart3,BookOpen,ClipboardCheck,Code2,Command,LogOut,Menu,Search,Settings2,ShieldCheck,Users,X,ChevronRight,FileCheck2} from "lucide-react";
import {auth,errorMessage,health} from "../services/api";

const links=[
 ["Overview","/admin",BarChart3,"Overview"],
 ["Users","/admin?tab=Users",Users,"Users"],
 ["Courses","/admin?tab=Courses",BookOpen,"Courses"],
 ["Assessments","/admin?tab=Assessments",ClipboardCheck,"Assessments"],
 ["Results","/admin?tab=Results",FileCheck2,"Results"],
 ["External Coding","/admin?tab=External Coding",Code2,"External Coding"],
];
export default function AdminLayout({children}){
 const navigate=useNavigate(),location=useLocation();
 const [open,setOpen]=useState(false),[status,setStatus]=useState("Connecting...");
 const user=useMemo(()=>{try{return JSON.parse(localStorage.getItem("skelo_user")||"{}")}catch{return {}}},[location.pathname,location.search]);
 const name=user.name||user.username||"Admin", initials=name.split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase()||"A";
 const activeTab=new URLSearchParams(location.search).get("tab")||"Overview";
 useEffect(()=>{let live=true;health().then(d=>live&&setStatus(d?.status==="ok"?"Connected":"Degraded")).catch(()=>live&&setStatus("Offline"));return()=>{live=false}},[]);
 const logout=async()=>{await auth.logout();navigate("/login",{replace:true})};
 const active=(key)=>location.pathname==="/admin" && activeTab===key;
 return <div className="app-shell admin-shell">
   <div className={`mobile-overlay ${open?"show":""}`} onClick={()=>setOpen(false)}/>
   <aside className={`sidebar admin-sidebar ${open?"open":""}`}>
    <div className="brand"><div className="brand-mark"><ShieldCheck size={20}/></div><div className="brand-copy"><b>SCOTT</b><span>ADMIN CONTROL CENTER</span></div><button className="mobile-close" onClick={()=>setOpen(false)}><X/></button></div>
    <div className="side-label">ADMIN WORKSPACE</div>
    <nav>{links.map(([label,path,Icon,key])=><NavLink key={label} to={path} end={key==="Overview"} onClick={()=>setOpen(false)} className={()=>`nav-item ${active(key)?"active":""}`}><span className="nav-icon"><Icon size={18}/></span><span>{label}</span></NavLink>)}</nav>
    <div className="sidebar-bottom">
      <div className="admin-side-note"><ShieldCheck size={16}/><div><b>Administrator</b><span>Manage live platform data.</span></div></div>
      <div className="mini-profile"><div className="avatar">{initials}</div><div><b>{name}</b><small>ADMIN</small></div><ChevronRight size={16}/></div>
      <button className="logout" onClick={logout}><LogOut size={17}/> Sign out</button>
    </div>
   </aside>
   <main className="main admin-main">
    <header className="topbar"><button className="menu" onClick={()=>setOpen(true)}><Menu/></button><div className="breadcrumb"><span>SCOTT</span><i>/</i>Admin Workspace</div><div className="global-search"><Search size={16}/><input placeholder="Search admin records..." disabled/><kbd><Command size={11}/> K</kbd></div><div className="top-actions"><div className={`api-status ${status.toLowerCase()}`}><span/>{status}</div><div className="top-avatar">{initials}</div></div></header>
    <section className="content">{children}</section>
   </main>
 </div>
}
