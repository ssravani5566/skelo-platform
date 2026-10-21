from django.db import connection
from django.db.models import Count
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import User
from .services import student_dashboard
from .serializers import DashboardSerializer

class HealthView(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        try:
            connection.ensure_connection(); db_ok=connection.is_usable()
        except Exception: db_ok=False
        return Response({"status":"ok" if db_ok else "degraded","database":db_ok})

class DashboardView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role!="STUDENT": return Response({"detail":"Student dashboard is currently available for student accounts."},status=403)
        return Response(DashboardSerializer(student_dashboard(request.user)).data)

class AdminOverviewView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        if request.user.role != User.ROLE_ADMIN:
            return Response({"detail": "Admin access required."}, status=403)
        from assessments.models import Assessment, Question, StudentAssessment
        from assignments.models import Assignment
        from coding.models import Problem, Submission
        from courses.models import Course, Lesson
        from students.models import StudentProfile
        return Response({
            "students": User.objects.filter(role=User.ROLE_STUDENT).count(),
            "faculty": User.objects.filter(role=User.ROLE_FACULTY).count(),
            "admins": User.objects.filter(role=User.ROLE_ADMIN).count(),
            "courses": Course.objects.count(),
            "published_courses": Course.objects.filter(is_published=True).count(),
            "lessons": Lesson.objects.count(),
            "assessments": Assessment.objects.count(),
            "published_assessments": Assessment.objects.filter(is_published=True).count(),
            "questions": Question.objects.count(),
            "attempts": StudentAssessment.objects.count(),
            "evaluated_attempts": StudentAssessment.objects.filter(status="EVALUATED").count(),
            "coding_problems": Problem.objects.count(),
            "coding_submissions": Submission.objects.count(),
            "assignments": Assignment.objects.count(),
            "student_profiles": StudentProfile.objects.count(),
        })

class CalendarView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        from assignments.models import Assignment
        from codeathons.models import Codeathon
        from interviews.models import Interview
        from assessments.models import Assessment
        from django.utils import timezone
        events=[]; now=timezone.now()
        if request.user.role=="STUDENT":
            student=request.user.student_profile
            for x in Interview.objects.filter(student=student,scheduled_at__isnull=False,scheduled_at__gte=now): events.append({"id":f"interview-{x.id}","type":"Interview","title":x.title,"start":x.scheduled_at.isoformat()})
        for x in Codeathon.objects.filter(is_published=True,end_at__gte=now): events.append({"id":f"codeathon-{x.id}","type":"Codeathon","title":x.title,"start":x.start_at.isoformat()})
        for x in Assignment.objects.filter(status="PUBLISHED",due_date__gte=now): events.append({"id":f"assignment-{x.id}","type":"Assignment","title":x.title,"start":x.due_date.isoformat()})
        for x in Assessment.objects.filter(is_published=True,end_at__gte=now): events.append({"id":f"assessment-{x.id}","type":"Assessment","title":x.title,"start":(x.start_at or now).isoformat()})
        return Response(sorted(events,key=lambda e:e["start"]))
