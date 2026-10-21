from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from students.services import get_student_profile
from .models import Badge, XPTransaction, StudentStreak, StudentBadge
from .serializers import XPTransactionSerializer
from .serializers import BadgeSerializer, StreakSerializer, StudentBadgeSerializer
from .services import gamification_summary
from core.api import paginated_response
class HealthView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({"status":"ok"})
class SummaryView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        student=get_student_profile(request.user); summary=gamification_summary(student)
        return Response({"xp":summary["xp"],"streak":{"current":summary["streak"]["current"],"longest":summary["streak"]["longest"],"last_activity_date":summary["streak"]["last_activity_date"]},"badges":StudentBadgeSerializer(summary["badges"],many=True).data})
class XPView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        qs=XPTransaction.objects.filter(student=get_student_profile(request.user)).order_by("-created_at"); return paginated_response(request,qs,XPTransactionSerializer)
class BadgeListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        student=get_student_profile(request.user); return Response(BadgeSerializer(Badge.objects.filter(is_active=True),many=True,context={"student":student,"request":request}).data)
class StreakView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        return Response(StreakSerializer(StudentStreak.objects.get_or_create(student=get_student_profile(request.user))[0]).data)
class StudentBadgeView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role!="STUDENT": return Response({"detail":"Student access required."},status=403)
        return Response(StudentBadgeSerializer(StudentBadge.objects.filter(student=get_student_profile(request.user)).select_related("badge"),many=True).data)
