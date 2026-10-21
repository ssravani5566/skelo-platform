import csv
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import report_overview
from .serializers import ReportSerializer
class HealthView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({"status":"ok"})
class ReportOverviewView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role!="STUDENT": return Response({"detail":"Student reports are available only for student accounts."},status=403)
        return Response(ReportSerializer(report_overview(request.user)).data)
class ReportCSVView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role!="STUDENT": return Response({"detail":"Student reports are available only for student accounts."},status=403)
        data=report_overview(request.user)
        response=HttpResponse(content_type="text/csv")
        response["Content-Disposition"]='attachment; filename="skelo-report.csv"'
        writer=csv.writer(response); writer.writerow(["Metric","Value"])
        for key in ["course_completion","coding_solved","assessment_performance","assignment_performance","attendance","interview_performance","codeathon_participation","xp","streak","longest_streak","placement_readiness","enrolled_courses"]: writer.writerow([key,data[key]])
        return response
