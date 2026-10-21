from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import User
from core.api import paginated_response
from core.notifications import create_notification
from students.models import StudentProfile
from students.services import get_student_profile
from .models import TrainingSession, Attendance
from .serializers import AttendanceSerializer, SessionSerializer

class HealthView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({"status":"ok"})
class AttendanceListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        qs=Attendance.objects.select_related("session__trainer","student__user").order_by("-session__session_date")
        if request.user.role=="STUDENT": qs=qs.filter(student=get_student_profile(request.user))
        status_filter=request.query_params.get("status")
        if status_filter: qs=qs.filter(status=status_filter.upper())
        return paginated_response(request,qs,AttendanceSerializer)
class AttendanceSummaryView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        qs=Attendance.objects.filter(student=get_student_profile(request.user)) if request.user.role=="STUDENT" else Attendance.objects.all()
        total=qs.count(); present=qs.filter(status__in=["PRESENT","LATE"]).count(); absent=qs.filter(status="ABSENT").count(); pct=round(present/total*100,2) if total else 0
        return Response({"total_sessions":total,"present":present,"late":qs.filter(status="LATE").count(),"absent":absent,"percentage":pct})
class SessionListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        qs=TrainingSession.objects.select_related("trainer").order_by("-session_date","-start_time")
        return paginated_response(request,qs,SessionSerializer)
    def post(self,request):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        data=dict(request.data)
        data["trainer"]=request.data.get("trainer") or request.user.id
        s=SessionSerializer(data=data); s.is_valid(raise_exception=True); obj=s.save(); return Response(SessionSerializer(obj).data,status=201)
class SessionDetailView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        obj=get_object_or_404(TrainingSession,pk=pk); s=SessionSerializer(obj,data=request.data,partial=True); s.is_valid(raise_exception=True); s.save(); return Response(s.data)
class MarkAttendanceView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        if request.user.role not in ("ADMIN","FACULTY"): return Response({"detail":"Faculty or admin access required."},status=403)
        session=get_object_or_404(TrainingSession,pk=pk); student=get_object_or_404(StudentProfile,pk=request.data.get("student_id")); status_value=request.data.get("status","ABSENT").upper()
        if status_value not in {"PRESENT","ABSENT","LATE"}: return Response({"detail":"Invalid attendance status."},status=400)
        obj,_=Attendance.objects.update_or_create(session=session,student=student,defaults={"status":status_value,"remarks":request.data.get("remarks","")})
        create_notification(student.user,"Attendance updated",f"{session.title}: {status_value.title()}.","ATTENDANCE")
        return Response(AttendanceSerializer(obj).data)
