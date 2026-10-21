from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import IsFacultyOrAdmin
from coding.models import Problem
from coding.services import evaluate_submission
from core.api import paginated_response
from core.notifications import create_notification
from gamification.services import award_xp
from students.services import get_student_profile
from .models import Codeathon, CodeathonParticipant, CodeathonProblem, CodeathonSubmission
from .serializers import CodeathonProblemSerializer, CodeathonSerializer, ParticipantSerializer

class HealthView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({"status":"ok"})
class CodeathonListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        qs=Codeathon.objects.all().order_by("start_at")
        if request.user.role=="STUDENT": qs=qs.filter(is_published=True)
        student=get_student_profile(request.user) if request.user.role=="STUDENT" else None
        data=CodeathonSerializer(qs,many=True,context={"student":student}).data
        q=request.query_params.get("q","").strip().lower()
        if q: data=[x for x in data if q in x["title"].lower() or q in x["description"].lower()]
        return paginated_response(request,data)
    def post(self,request):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        s=CodeathonSerializer(data=request.data); s.is_valid(raise_exception=True); obj=s.save(created_by=request.user); return Response(CodeathonSerializer(obj).data,status=201)
class CodeathonDetailView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        obj=get_object_or_404(Codeathon,pk=pk,**({"is_published":True} if request.user.role=="STUDENT" else {})); student=get_student_profile(request.user) if request.user.role=="STUDENT" else None
        return Response(CodeathonSerializer(obj,context={"student":student}).data)
    def patch(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        obj=get_object_or_404(Codeathon,pk=pk); s=CodeathonSerializer(obj,data=request.data,partial=True); s.is_valid(raise_exception=True); s.save(); return Response(s.data)
    def delete(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        get_object_or_404(Codeathon,pk=pk).delete(); return Response(status=204)
class RegisterView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        obj=get_object_or_404(Codeathon,pk=pk,is_published=True); now=timezone.now()
        if now >= obj.start_at: return Response({"detail":"Registration is closed because the event has started."},status=400)
        if obj.registration_opens_at and now < obj.registration_opens_at: return Response({"detail":"Registration has not opened yet."},status=400)
        if obj.registration_closes_at and now > obj.registration_closes_at: return Response({"detail":"The registration deadline has passed."},status=400)
        student=get_student_profile(request.user)
        if obj.max_participants and obj.participants.count()>=obj.max_participants and not obj.participants.filter(student=student).exists(): return Response({"detail":"Participant limit reached."},status=400)
        p,created=CodeathonParticipant.objects.get_or_create(codeathon=obj,student=student)
        if created:
            create_notification(request.user,"Codeathon registered",f"You are registered for {obj.title}.","SYSTEM")
        return Response(ParticipantSerializer(p).data,status=201 if created else 200)
class LeaveView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        participant=get_object_or_404(CodeathonParticipant,codeathon_id=pk,student=get_student_profile(request.user))
        if timezone.now() >= participant.codeathon.start_at:
            return Response({"detail":"You cannot leave after the event has started."},status=400)
        if participant.codeathon.registration_closes_at and timezone.now() > participant.codeathon.registration_closes_at:
            return Response({"detail":"The withdrawal deadline has passed."},status=400)
        participant.delete(); return Response(status=204)
class ProblemsView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        c=get_object_or_404(Codeathon,pk=pk); student=get_student_profile(request.user) if request.user.role=="STUDENT" else None
        return Response(CodeathonProblemSerializer(c.problems.select_related("problem"),many=True,context={"student":student}).data)
    def post(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        c=get_object_or_404(Codeathon,pk=pk); problem=get_object_or_404(Problem,pk=request.data.get("problem_id"),is_published=True); obj,_=CodeathonProblem.objects.get_or_create(codeathon=c,problem=problem,defaults={"order":request.data.get("order",1),"points":request.data.get("points",problem.points)}); return Response(CodeathonProblemSerializer(obj).data,status=201)
class LeaderboardView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        qs=CodeathonParticipant.objects.filter(codeathon_id=pk).select_related("student__user").order_by("-score","registered_at")
        rows=list(qs); changed=False
        for i,row in enumerate(rows,1):
            if row.rank!=i: row.rank=i; row.save(update_fields=["rank"])
        return Response(ParticipantSerializer(rows,many=True).data)
class SubmitView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        c=get_object_or_404(Codeathon,pk=pk,is_published=True); p=get_object_or_404(CodeathonParticipant,codeathon=c,student=get_student_profile(request.user));
        if not c.start_at<=timezone.now()<=c.end_at: return Response({"detail":"Codeathon is not open."},status=400)
        problem_link=get_object_or_404(CodeathonProblem,codeathon=c,problem_id=request.data.get("problem_id"))
        sub=evaluate_submission(p.student,problem_link.problem,request.data.get("language"),request.data.get("source_code",""))
        already_awarded=CodeathonSubmission.objects.filter(participant=p,problem=problem_link.problem,points_awarded__gt=0).exists()
        points=problem_link.points if sub.status=="ACCEPTED" and not already_awarded else 0
        CodeathonSubmission.objects.create(participant=p,problem=problem_link.problem,submission=sub,points_awarded=points)
        if points:
            p.score = p.score + points
            p.save(update_fields=["score"])
            award_xp(p.student,"CODEATHON",points,f"Codeathon points: {c.title}",source_key=f"codeathon:{c.id}:problem:{problem_link.problem.id}")
        return Response({"submission_id":sub.id,"status":sub.status,"points_awarded":points})
