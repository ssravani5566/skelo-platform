import React,{useEffect,useState} from "react";
import {ArrowLeft,CheckCircle2,XCircle,MinusCircle,Trophy,Target,FileCheck2} from "lucide-react";
import {useNavigate,useParams} from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import {Badge,DetailPanel} from "../../components/ModuleCard";
import {ErrorState,Loading} from "../../components/AsyncState";
import {errorMessage,get} from "../../services/api";

export default function AssessmentResult(){
 const {attemptId}=useParams(),nav=useNavigate();
 const [a,setA]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState("");
 const load=()=>{setLoading(true);setError("");get(`/assessments/attempts/${attemptId}/result/`).then(setA).catch(e=>setError(errorMessage(e))).finally(()=>setLoading(false))};
 useEffect(load,[attemptId]);
 if(loading)return <Loading text="Loading result..."/>;
 if(error)return <ErrorState text={error} onRetry={load}/>;
 const passed=Boolean(a.passed);
 return <div>
   <button className="back-link" onClick={()=>nav("/assessments")}><ArrowLeft size={15}/> Assessments</button>
   <PageHeader eyebrow="SCOTT · ASSESSMENT RESULT" title={a.assessment_title} subtitle="Your result is calculated from the submitted answers and stored with this assessment attempt."/>
   <section className="result-hero">
     <div><span className="mini-eyebrow">FINAL SCORE</span><strong>{a.percentage}%</strong><span>{a.score} / {a.total_marks} marks</span></div>
     <div className="result-hero-badge"><Badge tone={passed?"success":"warning"}>{passed?"PASS":"REVIEW REQUIRED"}</Badge><small>{a.assessment_type} · {a.total_questions} questions</small></div>
   </section>
   <div className="result-summary-grid">
     <div className="result-summary-card"><CheckCircle2 className="result-correct" size={20}/><strong className="result-correct">{a.correct_answers}</strong><span>Correct answers</span></div>
     <div className="result-summary-card"><XCircle className="result-wrong" size={20}/><strong className="result-wrong">{a.wrong_answers}</strong><span>Wrong answers</span></div>
     <div className="result-summary-card"><MinusCircle className="result-unanswered" size={20}/><strong>{a.unanswered}</strong><span>Unanswered</span></div>
     <div className="result-summary-card"><Trophy className="result-score" size={20}/><strong className="result-score">{a.score}</strong><span>Marks awarded</span></div>
   </div>
   <DetailPanel title="Answer review">
    <div className="answer-review">{(a.answers||[]).map((x,i)=><div className="answer-review-row" key={x.id}>
      <div>{x.is_correct?<CheckCircle2 className="result-correct" size={18}/>:<XCircle className="result-wrong" size={18}/>}</div>
      <div><b>Question {i+1}</b><span>Your answer: {x.answer_text||"Not answered"}</span><small>{x.is_correct?"Correct":"Wrong"} · {x.marks_awarded} marks</small></div>
    </div>)}</div>
   </DetailPanel>
 </div>
}
