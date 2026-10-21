
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from courses.models import Course
from coding.external import is_external_problem, parse_external_tags, platform_label
from coding.models import Problem
from assessments.models import Assessment
from assignments.models import Assignment
from codeathons.models import Codeathon
from interviews.models import Interview


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({
                "courses": [], "problems": [], "external_problems": [],
                "assessments": [], "assignments": [], "codeathons": [], "interviews": []
            })

        result = {
            "courses": [], "problems": [], "external_problems": [],
            "assessments": [], "assignments": [], "codeathons": [], "interviews": []
        }

        term = Q(title__icontains=q) | Q(description__icontains=q)
        result["courses"] = list(
            Course.objects.filter(Q(is_published=True) & term)
            .values("id", "title", "category")[:10]
        )

        problems = Problem.objects.filter(
            Q(is_published=True) &
            (Q(title__icontains=q) | Q(description__icontains=q) | Q(topic__icontains=q))
        ).order_by("title")[:30]
        for problem in problems:
            meta = parse_external_tags(problem.tags)
            row = {
                "id": problem.id,
                "title": problem.title,
                "difficulty": problem.difficulty,
                "topic": problem.topic,
            }
            if is_external_problem(problem):
                row.update({
                    "platform": meta.get("platform"),
                    "platform_label": platform_label(meta.get("platform")),
                    "external_url": meta.get("url"),
                })
                result["external_problems"].append(row)
            else:
                result["problems"].append(row)

        result["assessments"] = list(
            Assessment.objects.filter(
                Q(is_published=True) &
                (Q(title__icontains=q) | Q(description__icontains=q))
            ).values("id", "title", "assessment_type")[:10]
        )
        result["assignments"] = list(
            Assignment.objects.filter(
                Q(status="PUBLISHED") &
                (Q(title__icontains=q) | Q(description__icontains=q) | Q(instructions__icontains=q))
            ).values("id", "title", "due_date")[:10]
        )
        result["codeathons"] = list(
            Codeathon.objects.filter(
                Q(is_published=True) &
                (Q(title__icontains=q) | Q(description__icontains=q))
            ).values("id", "title", "start_at", "end_at")[:10]
        )

        qs = Interview.objects.filter(Q(title__icontains=q) | Q(role__icontains=q))
        if request.user.role == "STUDENT":
            qs = qs.filter(student=request.user.student_profile)
        result["interviews"] = list(
            qs.values("id", "title", "scheduled_at", "status")[:10]
        )
        return Response(result)
