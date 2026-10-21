from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import paginated_response
from students.services import get_student_profile

from .external import PLATFORM_CHOICES, PLATFORM_HOME, is_external_problem, parse_external_tags, platform_label
from .external_sync import sync_platform
from .models import ExternalProblemProgress, Problem, Submission
from .serializers import (
    ExternalProblemCreateSerializer,
    ExternalProgressSerializer,
    ProblemDetailSerializer,
    ProblemListSerializer,
    SubmissionCreateSerializer,
    SubmissionSerializer,
)
from .services import evaluate_submission


class HealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok"})


def _is_staff(user):
    return user.role in {"ADMIN", "FACULTY"}


# The first Coding Arena visit should not require an administrator to perform
# a separate sync. When the requested live catalog is empty, SCOTT performs a
# one-time bootstrap from public platform metadata. Subsequent requests use
# the database normally. Set SCOTT_AUTO_SYNC=0 to disable this behavior.
AUTO_SYNC_LIMITS = {
    "LEETCODE": 5000,
    "HACKERRANK": 500,
    "CODECHEF": 500,
    "CODEFORCES": 5000,
}


def _has_external_for_platform(platform=None):
    for tags in Problem.objects.filter(is_published=True).values_list("tags", flat=True):
        meta = parse_external_tags(tags)
        if meta.get("external") and meta.get("platform") and meta.get("url"):
            if platform is None or meta.get("platform") == platform:
                return True
    return False


def _auto_bootstrap_external_catalog(platform=None):
    from os import getenv

    if getenv("SCOTT_AUTO_SYNC", "1").strip().lower() in {"0", "false", "no", "off"}:
        return {"started": False, "synced": {}, "errors": {}}

    targets = [platform] if platform else list(AUTO_SYNC_LIMITS)
    targets = [p for p in targets if p in AUTO_SYNC_LIMITS]
    if not targets:
        return {"started": False, "synced": {}, "errors": {}}

    needed = [p for p in targets if not _has_external_for_platform(p)]
    if not needed:
        return {"started": False, "synced": {}, "errors": {}}

    failure_key = "scott:coding:auto-sync-failed:" + (platform or "all")
    if cache.get(failure_key):
        return {"started": False, "syncing": False, "synced": {}, "errors": {"catalog": "Automatic sync is temporarily paused after a previous upstream failure. Check platform connectivity and retry later."}}

    lock_key = "scott:coding:auto-sync:" + (platform or "all")
    if not cache.add(lock_key, True, timeout=600):
        return {"started": False, "syncing": True, "synced": {}, "errors": {}}

    synced, errors = {}, {}
    try:
        for target in needed:
            try:
                synced[target] = sync_platform(target, AUTO_SYNC_LIMITS[target])
            except Exception as exc:
                errors[target] = str(exc)
    finally:
        cache.delete(lock_key)
    if errors and not synced:
        cache.set(failure_key, True, timeout=120)
    return {"started": True, "syncing": False, "synced": synced, "errors": errors}


class PlatformListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": key, "name": name, "homepage": PLATFORM_HOME[key], "live_sync": key != "GEEKSFORGEEKS"}
            for key, name in PLATFORM_CHOICES
        ])


class ExternalSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _is_staff(request.user):
            return Response({"detail": "Faculty or Admin access required."}, status=403)
        platform = str(request.data.get("platform", "")).upper()
        try:
            limit = max(1, min(int(request.data.get("limit", 5000)), 5000))
        except (TypeError, ValueError):
            limit = 5000
        live_platforms = ["LEETCODE", "HACKERRANK", "CODECHEF", "CODEFORCES"]
        if platform == "ALL":
            synced, errors = {}, {}
            for target in live_platforms:
                try:
                    synced[target] = sync_platform(target, limit)
                except Exception as exc:
                    errors[target] = str(exc)
            status_code = 200 if synced else 502
            return Response(
                {
                    "platform": "ALL",
                    "synced": synced,
                    "errors": errors,
                    "total_synced": sum(synced.values()),
                },
                status=status_code,
            )
        if platform not in dict(PLATFORM_CHOICES):
            return Response({"detail": "Unsupported coding platform."}, status=400)
        try:
            count = sync_platform(platform, limit)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=502)
        return Response({"platform": platform, "platform_label": platform_label(platform), "synced": count})


class ProblemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        source = request.query_params.get("source", "").upper()
        requested_platform = request.query_params.get("platform", "").upper() or None
        auto_sync = None
        if source == "EXTERNAL" or (not source and requested_platform):
            auto_sync = _auto_bootstrap_external_catalog(requested_platform)

        qs = Problem.objects.filter(is_published=True).order_by("id")
        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(topic__icontains=q) | Q(description__icontains=q))

        difficulty = request.query_params.get("difficulty")
        if difficulty:
            qs = qs.filter(difficulty=difficulty.upper())

        platform = request.query_params.get("platform", "").upper()
        rows = list(qs)
        if source in {"LOCAL", "EXTERNAL"}:
            want_external = source == "EXTERNAL"
            rows = [p for p in rows if is_external_problem(p) == want_external]
        if platform:
            rows = [p for p in rows if parse_external_tags(p.tags).get("platform") == platform]

        def number_value(problem):
            value = parse_external_tags(problem.tags).get("number") or parse_external_tags(problem.tags).get("id") or ""
            digits = "".join(ch for ch in str(value) if ch.isdigit())
            try:
                return int(digits) if digits else 10**12
            except ValueError:
                return 10**12

        def acceptance_value(problem):
            try:
                return float(parse_external_tags(problem.tags).get("acceptance") or parse_external_tags(problem.tags).get("success_rate") or -1)
            except (TypeError, ValueError):
                return -1

        sort_key = request.query_params.get("sort", "number_asc")
        if sort_key == "number_desc":
            rows.sort(key=number_value, reverse=True)
        elif sort_key == "acceptance_desc":
            rows.sort(key=acceptance_value, reverse=True)
        elif sort_key == "acceptance_asc":
            rows.sort(key=acceptance_value)
        elif sort_key == "title_asc":
            rows.sort(key=lambda x: x.title.lower())
        elif sort_key == "title_desc":
            rows.sort(key=lambda x: x.title.lower(), reverse=True)
        else:
            rows.sort(key=number_value)

        solved_filter = request.query_params.get("solved")
        student = get_student_profile(request.user) if request.user.role == "STUDENT" else None
        external_solved_ids = set()
        local_solved_ids = set()
        if student:
            row_ids = [p.id for p in rows]
            external_solved_ids = set(ExternalProblemProgress.objects.filter(student=student, problem_id__in=row_ids).values_list("problem_id", flat=True))
            local_solved_ids = set(Submission.objects.filter(student=student, problem_id__in=row_ids, status="ACCEPTED").values_list("problem_id", flat=True).distinct())

        serialized = ProblemListSerializer(
            rows,
            many=True,
            context={
                "request": request,
                "student": student,
                "external_solved_ids": external_solved_ids,
                "local_solved_ids": local_solved_ids,
            },
        ).data
        if solved_filter in {"true", "false"}:
            wanted = solved_filter == "true"
            serialized = [x for x in serialized if x["solved"] is not None and x["solved"] == wanted]

        response = paginated_response(request, serialized)
        response.data["solved_count"] = sum(1 for x in serialized if x.get("solved") is True)
        if auto_sync is not None:
            response.data["catalog_sync"] = auto_sync
        return response


class ProblemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        problem = get_object_or_404(Problem, pk=pk, is_published=True)
        student = get_student_profile(request.user) if request.user.role == "STUDENT" else None
        context = {"request": request, "student": student}
        if student and is_external_problem(problem):
            context["external_solved_ids"] = set(ExternalProblemProgress.objects.filter(student=student, problem=problem).values_list("problem_id", flat=True))
        return Response(ProblemDetailSerializer(problem, context=context).data)

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        problem = get_object_or_404(Problem, pk=pk, is_published=True)
        if is_external_problem(problem):
            meta = parse_external_tags(problem.tags)
            return Response(
                {
                    "detail": "External problems must be solved on the original platform.",
                    "platform": meta.get("platform"),
                    "platform_label": platform_label(meta.get("platform")),
                    "external_url": meta.get("url"),
                },
                status=400,
            )

        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = evaluate_submission(
            get_student_profile(request.user),
            problem,
            serializer.validated_data["language"],
            serializer.validated_data["source_code"],
        )
        return Response(SubmissionSerializer(submission).data, status=201)


class ExternalProblemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _is_staff(request.user):
            return Response({"detail": "Faculty or Admin access required."}, status=403)
        serializer = ExternalProblemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem = serializer.save()
        return Response(ProblemDetailSerializer(problem, context={"request": request}).data, status=201)


class ExternalProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        problem = get_object_or_404(Problem, pk=pk, is_published=True)
        if not is_external_problem(problem):
            return Response({"detail": "This is not an external problem."}, status=400)
        student = get_student_profile(request.user)
        progress, created = ExternalProblemProgress.objects.get_or_create(student=student, problem=problem)
        return Response({"solved": True, "progress": ExternalProgressSerializer(progress).data}, status=201 if created else 200)

    def delete(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        problem = get_object_or_404(Problem, pk=pk, is_published=True)
        if not is_external_problem(problem):
            return Response({"detail": "This is not an external problem."}, status=400)
        student = get_student_profile(request.user)
        ExternalProblemProgress.objects.filter(student=student, problem=problem).delete()
        return Response({"solved": False})


class SubmissionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Submission.objects.select_related("problem", "student__user")
        if request.user.role == "STUDENT":
            qs = qs.filter(student=get_student_profile(request.user))
        problem_id = request.query_params.get("problem")
        if problem_id:
            qs = qs.filter(problem_id=problem_id)
        return paginated_response(request, qs, SubmissionSerializer)


class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        qs = Submission.objects.select_related("problem", "student__user")
        if request.user.role == "STUDENT":
            qs = qs.filter(student=get_student_profile(request.user))
        return Response(SubmissionSerializer(get_object_or_404(qs, pk=pk)).data)
