import React from "react";
export function Badge({children,tone="info"}){return <span className={`badge ${tone}`}>{children}</span>}
export function Progress({value}){return <div className="live-progress"><i style={{width:`${Math.max(0,Math.min(100,Number(value)||0))}%`}}/></div>}
export function DetailPanel({title,children,actions}){return <section className="live-panel"><div className="live-panel-head"><h2>{title}</h2><div>{actions}</div></div>{children}</section>}
