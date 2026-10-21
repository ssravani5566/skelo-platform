import React from "react";
export default function PageHeader({eyebrow,title,subtitle,action}){return <div className="page-header">
 <div><div className="eyebrow">{eyebrow||"SCOTT · STUDENT WORKSPACE"}</div><h1>{title}</h1>{subtitle&&<p>{subtitle}</p>}</div>{action&&<div className="page-header-action">{action}</div>}
</div>}