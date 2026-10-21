from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from students.services import get_student_profile
from .models import Interview, InterviewQuestion, InterviewAnswer
from .serializers import InterviewAnswerSerializer, InterviewFeedbackSerializer, InterviewQuestionSerializer, InterviewSerializer
from .services import save_feedback, sync_status
from core.api import paginated_response

class HealthView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({"status":"ok"})
class InterviewListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        qs=Interview.objects.select_related("student__user","interviewer").prefetch_related("feedback")
        if request.user.role=="STUDENT": qs=qs.filter(student=get_student_profile(request.user))
        data=[]
        for x in qs.order_by("-scheduled_at"):
            sync_status(x); data.append(InterviewSerializer(x).data)
        return paginated_response(request,data)
    def post(self,request):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        from .serializers_admin import InterviewAdminSerializer
        s=InterviewAdminSerializer(data=request.data); s.is_valid(raise_exception=True); obj=s.save(interviewer=request.user if not request.data.get("interviewer") else s.validated_data.get("interviewer"));
        create_notification(obj.student.user,"Interview scheduled",f"{obj.title} is scheduled for {obj.scheduled_at}.","INTERVIEW")
        return Response(InterviewSerializer(obj).data,status=201)
class InterviewDetailView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        qs=Interview.objects.select_related("student__user","interviewer").prefetch_related("feedback")
        if request.user.role=="STUDENT": qs=qs.filter(student=get_student_profile(request.user))
        obj=get_object_or_404(qs,pk=pk); sync_status(obj); return Response(InterviewSerializer(obj).data)
    def patch(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        from .serializers_admin import InterviewAdminSerializer
        obj=get_object_or_404(Interview,pk=pk); s=InterviewAdminSerializer(obj,data=request.data,partial=True); s.is_valid(raise_exception=True); s.save(); return Response(InterviewSerializer(obj).data)
    def delete(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        get_object_or_404(Interview,pk=pk).delete(); return Response(status=204)
class QuestionsView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        qs=Interview.objects.all()
        if request.user.role=="STUDENT": qs=qs.filter(student=get_student_profile(request.user))
        obj=get_object_or_404(qs,pk=pk); return Response(InterviewQuestionSerializer(obj.questions.all(),many=True).data)
    def post(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        obj=get_object_or_404(Interview,pk=pk); q=InterviewQuestion.objects.create(interview=obj,question_text=request.data.get("question_text",""),category=request.data.get("category",""),order=request.data.get("order",obj.questions.count()+1)); return Response(InterviewQuestionSerializer(q).data,status=201)
class AnswerView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        q=get_object_or_404(InterviewQuestion,pk=pk,interview__student=get_student_profile(request.user)); s=InterviewAnswerSerializer(data={"interview_question":q.id,"answer_text":request.data.get("answer_text",""),"audio_url":request.data.get("audio_url","")}); s.is_valid(raise_exception=True); return Response(InterviewAnswerSerializer(InterviewAnswer.objects.create(**s.validated_data)).data,status=201)
class FeedbackView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        qs=Interview.objects.all();
        if request.user.role=="STUDENT": qs=qs.filter(student=get_student_profile(request.user))
        obj=get_object_or_404(qs,pk=pk); return Response(InterviewFeedbackSerializer(getattr(obj,"feedback",None)).data if getattr(obj,"feedback",None) else None)
    def post(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        obj=get_object_or_404(Interview,pk=pk); s=InterviewFeedbackSerializer(data=request.data); s.is_valid(raise_exception=True); return Response(InterviewFeedbackSerializer(save_feedback(obj,s.validated_data)).data)
