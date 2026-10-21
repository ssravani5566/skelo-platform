import React, { useMemo, useState } from "react";
import { CalendarDays, Code2, Plus, Save, Send, Trash2, Trophy, Users, RefreshCw } from "lucide-react";
import { DetailPanel, Badge } from "../../components/ModuleCard";
import { errorMessage, post, patch, del, get, unwrapList } from "../../services/api";
import "./CodeathonManager.css";

const blank={title:"",description:"",event_type:"CODING",category:"",difficulty:"ALL",participation_type:"INDIVIDUAL",mode:"ONLINE",registration_opens_at:"",registration_closes_at:"",start_at:"",end_at:"",max_participants:"",venue:"",instructions:"",prizes:"",is_published:false};
const localDate=(v)=>v?new Date(v).toISOString().slice(0,16):"";
const displayDate=(v)=>v?new Date(v).toLocaleString():"—";
export default function CodeathonManager({data=[],onDone}) {
 const [form,setForm]=useState(blank),[selected,setSelected]=useState(null),[busy,setBusy]=useState(false),[err,setErr]=useState(""),[search,setSearch]=useState("");
 const [availableProblems,setAvailableProblems]=useState([]),[attachedProblems,setAttachedProblems]=useState([]),[problemId,setProblemId]=useState(""),[points,setPoints]=useState(10);
 const rows=useMemo(()=>data.filter(x=>(x.title||"").toLowerCase().includes(search.toLowerCase())),[data,search]);
 const change=e=>setForm({...form,[e.target.name]:e.target.type==="checkbox"?e.target.checked:e.target.value});
 const edit=async c=>{setSelected(c);setForm({...blank,...c,registration_opens_at:localDate(c.registration_opens_at),registration_closes_at:localDate(c.registration_closes_at),start_at:localDate(c.start_at),end_at:localDate(c.end_at),max_participants:c.max_participants??"",is_published:!!c.is_published});setErr("");try{const [all,attached]=await Promise.all([get("/coding/problems/?page_size=100"),get(`/codeathons/${c.id}/problems/`)]);setAvailableProblems(unwrapList(all));setAttachedProblems(unwrapList(attached));}catch(e){setErr(errorMessage(e,"Event loaded, but coding problems could not be loaded."));}};
 const reset=()=>{setSelected(null);setForm(blank);setAttachedProblems([]);setProblemId("");setErr("");};
 const attachProblem=async(e)=>{e.preventDefault();if(!selected?.id||!problemId)return;setBusy(true);setErr("");try{await post(`/codeathons/${selected.id}/problems/`,{problem_id:Number(problemId),order:attachedProblems.length+1,points:Number(points)||10});const attached=await get(`/codeathons/${selected.id}/problems/`);setAttachedProblems(unwrapList(attached));setProblemId("");onDone("Problem attached to this Codeathon.");}catch(e){setErr(errorMessage(e));}finally{setBusy(false)}};
 const save=async(e,publishNow=false)=>{e?.preventDefault();setBusy(true);setErr("");try{
   const start=new Date(form.start_at),end=new Date(form.end_at);
   if(!form.title.trim())throw new Error("Enter an event title.");
   if(!form.start_at||!form.end_at||Number.isNaN(+start)||Number.isNaN(+end)||end<=start)throw new Error("Event end must be after its start.");
   if(form.registration_opens_at&&form.registration_closes_at&&new Date(form.registration_closes_at)<=new Date(form.registration_opens_at))throw new Error("Registration close must be after registration opens.");
   const payload={...form,is_published:publishNow?true:form.is_published,start_at:start.toISOString(),end_at:end.toISOString(),registration_opens_at:form.registration_opens_at?new Date(form.registration_opens_at).toISOString():null,registration_closes_at:form.registration_closes_at?new Date(form.registration_closes_at).toISOString():null,max_participants:form.max_participants===""?null:Number(form.max_participants)};
   const result=selected?await patch(`/codeathons/${selected.id}/`,payload):await post("/codeathons/",payload);
   onDone(selected?"Codeathon updated.":"Codeathon created.");if(result?.id)edit(result);else reset();
 }catch(e){setErr(errorMessage(e,e.message||"Could not save event."));}finally{setBusy(false)}};
 const publish=async(c)=>{setBusy(true);setErr("");try{await patch(`/codeathons/${c.id}/`,{is_published:!c.is_published});onDone(c.is_published?"Event moved to draft.":"Event published for students.");}catch(e){setErr(errorMessage(e))}finally{setBusy(false)}};
 const remove=async(c)=>{if(!window.confirm(`Delete "${c.title}"? This removes its event registrations and links.`))return;setBusy(true);try{await del(`/codeathons/${c.id}/`);if(selected?.id===c.id)reset();onDone("Codeathon deleted.");}catch(e){setErr(errorMessage(e))}finally{setBusy(false)}};
 const count=(fn)=>data.filter(fn).length;
 return <div className="ct-admin">
  <div className="ct-admin-stats">{[["Total events",data.length],["Drafts",count(x=>!x.is_published)],["Published",count(x=>x.is_published)],["Registrations",data.reduce((n,x)=>n+(x.participants||0),0)]].map(([l,v])=><div key={l}><small>{l}</small><strong>{v}</strong></div>)}</div>
  <div className="ct-admin-layout">
   <section className="ct-admin-main">
    <DetailPanel title={selected?`Edit event · ${selected.title}`:"Create a Codeathon"}>
     <form className="ct-admin-form" onSubmit={e=>save(e,false)}>
      <label className="wide">Event title<input name="title" value={form.title} onChange={change} required placeholder="e.g. SCOTT Algorithm Sprint"/></label>
      <label>Event type<select name="event_type" value={form.event_type} onChange={change}><option value="CODING">Coding competition</option><option value="HACKATHON">Hackathon</option></select></label>
      <label>Category<input name="category" value={form.category} onChange={change} placeholder="DSA, AI, Web development"/></label>
      <label className="wide">Description<textarea name="description" rows="3" value={form.description} onChange={change} placeholder="Describe the event, goals and who should participate."/></label>
      <label>Difficulty<select name="difficulty" value={form.difficulty} onChange={change}><option value="ALL">All levels</option><option value="EASY">Easy</option><option value="MEDIUM">Medium</option><option value="HARD">Hard</option></select></label>
      <label>Participation<select name="participation_type" value={form.participation_type} onChange={change}><option value="INDIVIDUAL">Individual</option><option value="TEAM">Team (metadata only)</option></select></label>
      <label>Event mode<select name="mode" value={form.mode} onChange={change}><option value="ONLINE">Online</option><option value="OFFLINE">Offline</option><option value="HYBRID">Hybrid</option></select></label>
      <label>Maximum participants<input type="number" min="1" name="max_participants" value={form.max_participants} onChange={change} placeholder="No limit"/></label>
      <label>Registration opens<input type="datetime-local" name="registration_opens_at" value={form.registration_opens_at} onChange={change}/></label>
      <label>Registration closes<input type="datetime-local" name="registration_closes_at" value={form.registration_closes_at} onChange={change}/></label>
      <label>Event starts<input type="datetime-local" name="start_at" value={form.start_at} onChange={change} required/></label>
      <label>Event ends<input type="datetime-local" name="end_at" value={form.end_at} onChange={change} required/></label>
      <label className="wide">Venue / meeting details<input name="venue" value={form.venue} onChange={change} placeholder="Online / room / venue"/></label>
      <label className="wide">Rules and instructions<textarea name="instructions" rows="3" value={form.instructions} onChange={change} placeholder="Rules, eligibility, submission instructions…"/></label>
      <label className="wide">Prizes and certificates<textarea name="prizes" rows="2" value={form.prizes} onChange={change} placeholder="Prizes, awards or participation certificates"/></label>
      <label className="ct-check wide"><input type="checkbox" name="is_published" checked={form.is_published} onChange={change}/> Save as published (visible to students)</label>
      {err&&<div className="ct-admin-error wide">{err}</div>}
      <div className="ct-admin-actions wide"><button type="submit" className="primary-btn" disabled={busy}><Save size={15}/>{busy?"Saving…":selected?"Save changes":"Save draft"}</button><button type="button" className="outline-btn" disabled={busy} onClick={()=>save(null,true)}><Send size={15}/>Save & publish</button>{selected&&<button type="button" className="outline-btn" onClick={reset}>New event</button>}</div>
     </form>
    </DetailPanel>
    {selected&&<DetailPanel title={`Problem selection · ${selected.title}`}>
     <form className="ct-problem-attach" onSubmit={attachProblem}><label>Published coding problem<select value={problemId} onChange={e=>setProblemId(e.target.value)} required><option value="">Choose a problem…</option>{availableProblems.filter(p=>!attachedProblems.some(a=>String(a.problem?.id||a.problem_id)===String(p.id))).map(p=><option key={p.id} value={p.id}>{p.title} · {p.difficulty||"Difficulty not set"}</option>)}</select></label><label>Points<input type="number" min="1" value={points} onChange={e=>setPoints(e.target.value)}/></label><button className="primary-btn" disabled={busy||!problemId}><Plus size={14}/>Attach problem</button></form>
     <div className="ct-attached-list">{attachedProblems.map(p=><div key={p.id}><span><Code2 size={14}/>{p.problem?.title||"Problem"}</span><b>{p.points} pts</b></div>)}{!attachedProblems.length&&<p className="muted-text">No problems attached to this event yet.</p>}</div>
    </DetailPanel>}
    <DetailPanel title="Event registrations and management">
     <div className="ct-admin-table-tools"><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search events…"/><button className="outline-btn" onClick={()=>onDone("Event list refreshed.")}><RefreshCw size={14}/>Refresh</button></div>
     <div className="table-scroll"><table className="data-table"><thead><tr><th>Event</th><th>Schedule</th><th>Registrations</th><th>Status</th><th>Actions</th></tr></thead><tbody>{rows.map(c=><tr key={c.id}><td><b>{c.title}</b><br/><span className="muted-text">{c.event_type==="HACKATHON"?"Hackathon":"Coding competition"} · {c.mode||"Online"}</span></td><td>{displayDate(c.start_at)}<br/><span className="muted-text">to {displayDate(c.end_at)}</span></td><td><Users size={13} style={{verticalAlign:"middle"}}/> {c.participants||0}{c.max_participants?` / ${c.max_participants}`:""}</td><td><Badge tone={c.is_published?"success":"muted"}>{c.is_published?"Published":"Draft"}</Badge></td><td><div className="ct-row-actions"><button className="outline-btn" onClick={()=>edit(c)}>Edit</button><button className="outline-btn" onClick={()=>publish(c)} disabled={busy}>{c.is_published?"Unpublish":"Publish"}</button><button className="ct-delete" title="Delete event" onClick={()=>remove(c)}><Trash2 size={14}/></button></div></td></tr>)}</tbody></table>{!rows.length&&<p className="muted-text">No events found. Create one using the form above.</p>}</div>
    </DetailPanel>
   </section>
   <aside className="ct-admin-aside"><DetailPanel title="Event workflow"><div className="ct-workflow"><span><Code2 size={17}/></span><div><b>1. Configure event</b><p>Set the type, schedule, registration limit and rules.</p></div></div><div className="ct-workflow"><span><Users size={17}/></span><div><b>2. Add problems</b><p>Use the existing Coding Arena question bank and attach problems to the event.</p></div></div><div className="ct-workflow"><span><Trophy size={17}/></span><div><b>3. Monitor results</b><p>Registered participants, submissions and leaderboard use the current backend records.</p></div></div><p className="ct-admin-note">Publishing makes the event visible to students. Backend date and registration checks remain authoritative.</p></DetailPanel></aside>
  </div>
 </div>;
}
