from django.shortcuts import get_object_or_404

from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from students.services import get_student_profile

from .models import Assignment, AssignmentSubmission
from .serializers import (
    AssignmentEvaluationSerializer,
    AssignmentSerializer,
    AssignmentSubmissionSerializer,
)
from .services import evaluate_assignment, submit_assignment
from core.api import paginated_response


class HealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok"})


class AssignmentListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        qs = (
            Assignment.objects
            .select_related("created_by")
            .order_by("due_date")
        )

        student = (
            get_student_profile(request.user)
            if request.user.role == "STUDENT"
            else None
        )

        # Students should only see assignments that admin/faculty published.
        if student is not None:
            qs = qs.filter(status="PUBLISHED")

        data = AssignmentSerializer(
            qs,
            many=True,
            context={
                "student": student,
                "request": request,
            },
        ).data

        return paginated_response(request, data)

    def post(self, request):
        if request.user.role not in ("ADMIN", "FACULTY"):
            return Response(
                {"detail": "Faculty or admin access required."},
                status=403,
            )

        serializer = AssignmentSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        obj = serializer.save(created_by=request.user)

        return Response(
            AssignmentSerializer(
                obj,
                context={"request": request},
            ).data,
            status=201,
        )


class AssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, pk):
        obj = get_object_or_404(Assignment, pk=pk)

        if (
            request.user.role == "STUDENT"
            and obj.status != "PUBLISHED"
        ):
            return Response(
                {"detail": "This assignment is not available."},
                status=404,
            )

        student = (
            get_student_profile(request.user)
            if request.user.role == "STUDENT"
            else None
        )

        return Response(
            AssignmentSerializer(
                obj,
                context={
                    "request": request,
                    "student": student,
                },
            ).data
        )

    def patch(self, request, pk):
        if request.user.role not in ("ADMIN", "FACULTY"):
            return Response(
                {"detail": "Faculty or admin access required."},
                status=403,
            )

        obj = get_object_or_404(Assignment, pk=pk)

        serializer = AssignmentSerializer(
            obj,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            AssignmentSerializer(
                obj,
                context={"request": request},
            ).data
        )

    def delete(self, request, pk):
        if request.user.role not in ("ADMIN", "FACULTY"):
            return Response(
                {"detail": "Faculty or admin access required."},
                status=403,
            )

        get_object_or_404(Assignment, pk=pk).delete()
        return Response(status=204)


class AssignmentSubmitView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response(
                {"detail": "Student access required."},
                status=403,
            )

        obj = get_object_or_404(
            Assignment,
            pk=pk,
            status="PUBLISHED",
        )
        student = get_student_profile(request.user)

        answer_text = str(
            request.data.get("answer_text", "")
        ).strip()

        submitted_file = request.FILES.get("submitted_file")

        # Accept Word documents, PDF, images, spreadsheets, ZIPs,
        # and other normal assignment files. Only enforce a safe size.
        if submitted_file and submitted_file.size > 25 * 1024 * 1024:
            return Response(
                {
                    "detail": (
                        "Submission file is too large. "
                        "Maximum allowed size is 25 MB."
                    )
                },
                status=400,
            )

        if not answer_text and not submitted_file:
            return Response(
                {
                    "detail": (
                        "Please write an answer or upload your "
                        "assignment file before submitting."
                    )
                },
                status=400,
            )

        submission = submit_assignment(
            student,
            obj,
            answer_text,
            submitted_file,
        )

        return Response(
            AssignmentSubmissionSerializer(submission).data
        )


class SubmissionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AssignmentSubmission.objects.select_related(
            "assignment",
            "student__user",
            "evaluation",
        )

        if request.user.role == "STUDENT":
            qs = qs.filter(
                student=get_student_profile(request.user)
            )

        return paginated_response(
            request,
            qs,
            AssignmentSubmissionSerializer,
        )


class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        qs = AssignmentSubmission.objects.select_related(
            "assignment",
            "student__user",
            "evaluation",
        )

        if request.user.role == "STUDENT":
            qs = qs.filter(
                student=get_student_profile(request.user)
            )

        return Response(
            AssignmentSubmissionSerializer(
                get_object_or_404(qs, pk=pk)
            ).data
        )

    def post(self, request, pk):
        if request.user.role not in ("ADMIN", "FACULTY"):
            return Response(
                {"detail": "Faculty or admin access required."},
                status=403,
            )

        sub = get_object_or_404(
            AssignmentSubmission,
            pk=pk,
        )

        serializer = AssignmentEvaluationSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            evaluation = evaluate_assignment(
                request.user,
                sub,
                float(serializer.validated_data["marks"]),
                serializer.validated_data.get("feedback", ""),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=400,
            )

        return Response(
            {
                "marks": evaluation.marks,
                "feedback": evaluation.feedback,
            }
        )
