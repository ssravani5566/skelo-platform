import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CalendarDays, Clock3, Sparkles, Target, BookOpen, CheckCircle2, Circle, Flame, Trophy, Brain, ArrowRight, Loader2, PartyPopper, PencilLine } from 'lucide-react';
import { get, post, patch, errorMessage } from '../services/api';
import './Schedule.css';

const today = () => {
 const d = new Date();
 return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
};

const COURSE_GROUPS = {
 'Programming & development': [
  'Python Programming','Java Programming','C Programming','C++ Programming','C# Programming','JavaScript','TypeScript','HTML & CSS','React.js','Node.js','Django','Flask','Full Stack Web Development','Android Development','iOS Development','PHP','.NET Development','Software Testing & QA','Git & GitHub'
 ],
 'Data & artificial intelligence': [
  'SQL','DBMS','Data Structures & Algorithms','Data Science','Machine Learning','Artificial Intelligence','Generative AI','Deep Learning','Natural Language Processing','Data Analytics','Power BI','Tableau','Advanced Excel'
 ],
 'Computer science fundamentals': [
  'Object-Oriented Programming','Operating Systems','Computer Networks','Computer Organization','Software Engineering','System Design','Cloud Computing','AWS','Microsoft Azure','DevOps','Cybersecurity','Linux','Computer Architecture'
 ],
 'Career & professional skills': [
  'Aptitude & Logical Reasoning','Verbal Ability','Communication Skills','Interview Preparation','Resume Building','Public Speaking','Business Analysis','Project Management'
 ]
};

export default function Schedule(){
 const [plans,setPlans]=useState([]),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [form,setForm]=useState({course_choice:'',custom_course_title:'',start_date:today(),duration_days:30,hours_per_day:2,goal:'Build a strong understanding and practice consistently'});
 const [testBusy,setTestBusy]=useState(false); const navigate=useNavigate();
 const load=async()=>{setLoading(true);setError('');try{const p=await get('/schedules/');setPlans(p.plans||[])}catch(e){setError(errorMessage(e))}finally{setLoading(false)}};
 useEffect(()=>{load()},[]);
 const active=plans.find(p=>p.status==='ACTIVE')||plans[0];
 const nextTask=active?.tasks?.find(t=>!t.completed);
 const completed=active?.completed_count||0,total=active?.task_count||0;
 const pendingCheck=active?.checks?.find(c=>c.response==='PENDING');
 const isCustom=form.course_choice==='__custom';
 const selectedCourse=isCustom?form.custom_course_title.trim():form.course_choice;
 const update=(k,v)=>setForm(f=>({...f,[k]:v}));
 const generate=async e=>{
  e.preventDefault();setBusy(true);setError('');setNotice('');
  try{
   const p=await post('/schedules/',{course_title:selectedCourse,start_date:form.start_date,duration_days:Number(form.duration_days),hours_per_day:Number(form.hours_per_day),goal:form.goal});
   setPlans(old=>[p,...old.filter(x=>x.id!==p.id)]);setNotice(`Your ${selectedCourse} learning path is ready. Let’s make progress! ✨`);
  }catch(e){setError(errorMessage(e))}finally{setBusy(false)}
 };
 const mark=async task=>{try{const d=await patch(`/schedules/tasks/${task.id}/complete/`,{completed:true});setPlans(ps=>ps.map(p=>p.id===d.plan.id?d.plan:p));if(d.test_available)setNotice('Topic completed! You unlocked an optional knowledge check. 🎉')}catch(e){setError(errorMessage(e))}};
 const respond=async response=>{if(!pendingCheck)return;setTestBusy(true);try{const d=await post(`/schedules/checks/${pendingCheck.id}/response/`,{response});setNotice(d.message);await load();if(response==='WILLING')navigate('/assessments')}catch(e){setError(errorMessage(e))}finally{setTestBusy(false)}};
 const grouped=useMemo(()=>{const map={};(active?.tasks||[]).forEach(t=>(map[t.scheduled_date]??=[]).push(t));return Object.entries(map)},[active]);

 return <div className="study-page">
  <div className="study-hero"><div className="study-hero-copy"><span className="study-kicker"><Sparkles size={14}/> YOUR PERSONAL LEARNING PATH</span><h1>Study smarter.<br/><em>Grow every day.</em></h1><p>Choose any subject you want to master. SKelo will turn it into a clear, achievable plan — even when the course is not listed in the course library.</p><div className="study-hero-points"><span><Target size={15}/> Your goals</span><span><CalendarDays size={15}/> Your pace</span><span><Trophy size={15}/> Your wins</span></div></div><div className="study-orbit"><div className="orbit-ring orbit-one"/><div className="orbit-ring orbit-two"/><div className="orbit-core"><Brain size={42}/><Sparkles className="orbit-spark" size={20}/></div><span className="orbit-tag tag-top">PERSONALIZED</span><span className="orbit-tag tag-bottom">SMART STUDY PLAN</span></div></div>
  {error&&<div className="study-alert error">{error}</div>}{notice&&<div className="study-alert success">{notice}</div>}
  <div className="study-layout">
   <section className="study-panel study-create"><div className="study-panel-head"><div className="study-icon purple"><Sparkles size={19}/></div><div><h2>Create your study plan</h2><p>Select a subject, set your pace and let SKelo map out your learning journey.</p></div></div>
    <form onSubmit={generate} className="study-form">
     <label>What do you want to learn?<span><BookOpen size={14}/> Choose a popular course or enter your own</span>
      <select required value={form.course_choice} onChange={e=>update('course_choice',e.target.value)}>
       <option value="">Choose a learning path</option>
       {Object.entries(COURSE_GROUPS).map(([group,items])=><optgroup label={group} key={group}>{items.map(item=><option value={item} key={item}>{item}</option>)}</optgroup>)}
       <option value="__custom">＋ Enter another course / skill</option>
      </select>
     </label>
     {isCustom&&<label className="study-custom-course"><span><PencilLine size={14}/> Your course or skill name</span><input required maxLength="200" value={form.custom_course_title} onChange={e=>update('custom_course_title',e.target.value)} placeholder="Example: Ethical Hacking, SAP, UI/UX Design..." autoFocus /></label>}
     <label>What is your learning goal?<textarea value={form.goal} onChange={e=>update('goal',e.target.value)} rows="3" placeholder="Example: Become job-ready, prepare for interviews, or build a project..."/></label>
     <div className="study-form-grid"><label><span><CalendarDays size={14}/> Start date</span><input type="date" required min={today()} value={form.start_date} onChange={e=>update('start_date',e.target.value)}/></label><label><span><Clock3 size={14}/> Plan duration</span><select value={form.duration_days} onChange={e=>update('duration_days',e.target.value)}><option value="7">7 days</option><option value="14">14 days</option><option value="30">30 days</option><option value="45">45 days</option><option value="60">60 days</option><option value="90">90 days</option><option value="120">120 days</option><option value="180">180 days</option></select></label><label><span><Clock3 size={14}/> Study time per day</span><select value={form.hours_per_day} onChange={e=>update('hours_per_day',e.target.value)}>{[0.5,1,1.5,2,2.5,3,4,5,6,8,10,12].map(v=><option key={v} value={v}>{v} {v===1?'hour':'hours'}</option>)}</select></label></div>
     <button className="study-primary" disabled={busy||!selectedCourse}>{busy?<><Loader2 className="spin" size={17}/> Building your plan...</>:<><Sparkles size={17}/> Generate my study schedule <ArrowRight size={17}/></>}</button>
     <small className="study-footnote">You can choose from the catalogue or type any subject. A topic-by-topic starter roadmap is created for every selection.</small>
    </form>
   </section>
   <section className="study-panel study-progress"><div className="study-panel-head"><div className="study-icon orange"><Flame size={19}/></div><div><h2>Your learning flow</h2><p>See where you are and what comes next.</p></div></div>{active?<><div className="study-current-course"><span>ACTIVE LEARNING PLAN</span><h3>{active.course_title}</h3><p>{active.goal}</p></div><div className="study-progress-line"><div className="study-progress-meta"><b>{active.progress}% complete</b><span>{completed} of {total} topics</span></div><div className="study-track"><i style={{width:`${active.progress}%`}}/></div></div><div className="study-mini-stats"><div><b>{total-completed}</b><span>Topics left</span></div><div><b>{active.hours_per_day}h</b><span>Daily target</span></div><div><b>{new Date(active.end_date).toLocaleDateString(undefined,{month:'short',day:'numeric'})}</b><span>Target finish</span></div></div>{nextTask&&<div className="study-next"><span className="study-next-icon"><BookOpen size={17}/></span><div><small>UP NEXT</small><b>{nextTask.title}</b><span>{new Date(nextTask.scheduled_date+'T00:00:00').toLocaleDateString(undefined,{month:'short',day:'numeric'})} · {nextTask.duration_minutes} min</span></div></div>}{pendingCheck&&<div className="study-test"><div className="study-test-title"><Brain size={18}/><div><b>Knowledge check unlocked!</b><span>Want to test what you’ve learned?</span></div></div><div className="study-test-actions"><button disabled={testBusy} onClick={()=>respond('WILLING')}>I’m ready</button><button disabled={testBusy} onClick={()=>respond('LATER')}>Remind me later</button></div><small>Taking the test is optional. Your learning plan continues either way.</small></div>}</>:<div className="study-empty"><div><CalendarDays size={30}/></div><h3>Your journey starts here</h3><p>Generate your first schedule and your progress, next topic and target date will appear here.</p></div>}</section>
  </div>
  {active&&<section className="study-panel study-timeline"><div className="study-panel-head"><div className="study-icon green"><CalendarDays size={19}/></div><div><h2>Your topic-by-topic roadmap</h2><p>Complete each topic to keep your learning journey moving.</p></div><span className="study-reminder"><Sparkles size={13}/> Reminder every 2 days</span></div>{grouped.map(([date,tasks],i)=><div className="study-day" key={date}><div className="study-day-date"><span>DAY {i+1}</span><b>{new Date(date+'T00:00:00').toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'})}</b></div><div className="study-day-tasks">{tasks.map(t=><div className={`study-task ${t.completed?'is-done':''}`} key={t.id}><span className="study-task-check">{t.completed?<CheckCircle2 size={20}/>:<Circle size={20}/>}</span><div className="study-task-copy"><b>{t.title}</b><span>{t.description||'Study and practice this topic'} · {t.duration_minutes} min</span></div>{t.completed?<span className="study-done-label">Completed</span>:<button onClick={()=>mark(t)}>Mark complete</button>}</div>)}</div></div>)}{active.status==='COMPLETED'&&<div className="study-celebrate"><PartyPopper size={24}/><div><b>You did it! Learning plan completed.</b><span>Every completed topic is a step forward. Keep that momentum going!</span></div><Trophy size={24}/></div>}</section>}
  <div className="study-reminder-note"><Sparkles size={16}/><span><b>Gentle nudges, not pressure.</b> We’ll create an in-app notification every two days for active plans. If you’re not ready for a knowledge check, choose “Remind me later” — no penalty.</span></div>
 </div>
}
