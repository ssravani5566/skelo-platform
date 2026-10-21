import React from "react";
import {Search} from "lucide-react";
export default function ModuleHeader({eyebrow,title,subtitle,query,setQuery,actions}){return <div className="module-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div><div className="module-actions">{actions}<label className="module-search"><Search size={16}/><input value={query||""} onChange={e=>setQuery?.(e.target.value)} placeholder="Search..."/></label></div></div>}
