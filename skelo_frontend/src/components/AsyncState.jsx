import React from "react";
import {AlertTriangle,Inbox,LoaderCircle} from "lucide-react";
export function Loading({text="Loading..."}){return <div className="state-card"><LoaderCircle className="spin" size={24}/><span>{text}</span></div>}
export function Empty({title="Nothing here yet",text="No records are available for this account."}){return <div className="state-card"><Inbox size={26}/><strong>{title}</strong><span>{text}</span></div>}
export function ErrorState({text="Unable to load data. Please try again.",onRetry}){return <div className="state-card error"><AlertTriangle size={26}/><strong>Unable to load data</strong><span>{text}</span>{onRetry&&<button className="primary-btn" onClick={onRetry}>Retry</button>}</div>}
