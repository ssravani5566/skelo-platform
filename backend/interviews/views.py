import json

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from students.services import get_student_profile
from core.api import paginated_response
from .models import Interview, InterviewQuestion, InterviewAnswer
from .serializers import InterviewAnswerSerializer, InterviewFeedbackSerializer, InterviewQuestionSerializer, InterviewSerializer
from .services import save_feedback, sync_status
from .interview_ai import ai_configured, evaluate_answer, make_final_report, make_question, question_limit


def _owned_interviews(request):
    qs = Interview.objects.select_related("student__user", "interviewer").prefetch_related("feedback")
    if getattr(request.user, "role", "") == "STUDENT":
        qs = qs.filter(student=get_student_profile(request.user))
    return qs


def _safe_duration(value):
    try:
        return max(5, min(120, int(value or 30)))
    except (TypeError, ValueError):
        return 30


def _safe_text(value, max_len=2000):
    return str(value or "").strip()[:max_len]


def _get_latest_or_create_answer(question, answer_text):
    answer = question.answers.order_by("-answered_at").first()
    if answer:
        answer.answer_text = answer_text
        answer.save(update_fields=["answer_text"])
        return answer
    return InterviewAnswer.objects.create(interview_question=question, answer_text=answer_text)


class PracticeStartView(APIView):
    """Create a student-owned practice session and its opening question."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if getattr(request.user, "role", "") != "STUDENT":
            return Response({"detail": "Student access required."}, status=status.HTTP_403_FORBIDDEN)

        profile = get_student_profile(request.user)
        payload = request.data
        interview_type = _safe_text(payload.get("interview_type", "MIXED"), 30).upper()
        if interview_type not in dict(Interview.TYPE_CHOICES):
            interview_type = "MIXED"
        difficulty = _safe_text(payload.get("difficulty", "INTERMEDIATE"), 20).upper()
        if difficulty not in {"BEGINNER", "INTERMEDIATE", "ADVANCED"}:
            difficulty = "INTERMEDIATE"
        interview_mode = _safe_text(payload.get("interview_mode", "TEXT"), 10).upper()
        if interview_mode not in {"TEXT", "VOICE", "VIDEO"}:
            interview_mode = "TEXT"

        type_labels = dict(Interview.TYPE_CHOICES)
        title = _safe_text(payload.get("title") or f"{payload.get('company') or 'General Placement'} · {type_labels[interview_type]} Practice", 200)
        obj = Interview.objects.create(
            title=title,
            interview_type=interview_type,
            student=profile,
            role=_safe_text(payload.get("role") or "Software Developer", 150),
            company=_safe_text(payload.get("company") or "General Placement", 120),
            difficulty=difficulty,
            duration_minutes=_safe_duration(payload.get("duration_minutes")),
            interview_mode=interview_mode,
            technical_topics=_safe_text(payload.get("technical_topics"), 2000),
            status="IN_PROGRESS",
            is_published=True,
        )
        opening, used_ai = make_question(obj, question_number=1)
        InterviewQuestion.objects.create(
            interview=obj,
            question_text=opening["question_text"],
            category=opening["category"],
            order=1,
        )
        data = InterviewSerializer(obj).data
        data.update({"ai_enabled": ai_configured(), "ai_used_for_opening": used_ai, "question_limit": question_limit(obj)})
        return Response(data, status=status.HTTP_201_CREATED)


class HealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok", "ai_configured": ai_configured()})


class InterviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = _owned_interviews(request)
        if getattr(request.user, "role", "") == "STUDENT":
            qs = qs.filter(is_published=True)
        data = []
        for item in qs.order_by("-created_at"):
            sync_status(item)
            data.append(InterviewSerializer(item).data)
        return paginated_response(request, data)

    def post(self, request):
        if getattr(request.user, "role", "") not in ("ADMIN", "FACULTY"):
            return Response({"detail": "Faculty or admin access required."}, status=status.HTTP_403_FORBIDDEN)
        from .serializers_admin import InterviewAdminSerializer
        serializer = InterviewAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interviewer = request.user if not request.data.get("interviewer") else serializer.validated_data.get("interviewer")
        obj = serializer.save(interviewer=interviewer)
        return Response(InterviewSerializer(obj).data, status=status.HTTP_201_CREATED)


class InterviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(_owned_interviews(request), pk=pk)
        sync_status(obj)
        data = InterviewSerializer(obj).data
        data["ai_enabled"] = ai_configured()
        data["question_limit"] = question_limit(obj)
        return Response(data)

    def patch(self, request, pk):
        if getattr(request.user, "role", "") not in ("ADMIN", "FACULTY"):
            return Response({"detail": "Faculty or admin access required."}, status=status.HTTP_403_FORBIDDEN)
        from .serializers_admin import InterviewAdminSerializer
        obj = get_object_or_404(Interview, pk=pk)
        serializer = InterviewAdminSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(InterviewSerializer(obj).data)

    def delete(self, request, pk):
        if getattr(request.user, "role", "") not in ("ADMIN", "FACULTY"):
            return Response({"detail": "Faculty or admin access required."}, status=status.HTTP_403_FORBIDDEN)
        get_object_or_404(Interview, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(_owned_interviews(request), pk=pk)
        return Response(InterviewQuestionSerializer(obj.questions.all(), many=True).data)

    def post(self, request, pk):
        if getattr(request.user, "role", "") not in ("ADMIN", "FACULTY"):
            return Response({"detail": "Faculty or admin access required."}, status=status.HTTP_403_FORBIDDEN)
        obj = get_object_or_404(Interview, pk=pk)
        question_text = _safe_text(request.data.get("question_text"), 8000)
        if not question_text:
            return Response({"detail": "Question text is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = int(request.data.get("order") or obj.questions.count() + 1)
        except (TypeError, ValueError):
            order = obj.questions.count() + 1
        question = InterviewQuestion.objects.create(
            interview=obj,
            question_text=question_text,
            category=_safe_text(request.data.get("category"), 100),
            order=max(1, order),
        )
        return Response(InterviewQuestionSerializer(question).data, status=status.HTTP_201_CREATED)


class AnswerView(APIView):
    """Backward-compatible answer save endpoint."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if getattr(request.user, "role", "") != "STUDENT":
            return Response({"detail": "Student access required."}, status=status.HTTP_403_FORBIDDEN)
        question = get_object_or_404(InterviewQuestion, pk=pk, interview__student=get_student_profile(request.user))
        answer_text = _safe_text(request.data.get("answer_text"), 12000)
        if not answer_text:
            return Response({"detail": "Write an answer before saving."}, status=status.HTTP_400_BAD_REQUEST)
        answer = _get_latest_or_create_answer(question, answer_text)
        return Response(InterviewAnswerSerializer(answer).data, status=status.HTTP_201_CREATED)


class InterviewTurnView(APIView):
    """Persist an answer, evaluate it, and create the next adaptive question."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if getattr(request.user, "role", "") != "STUDENT":
            return Response({"detail": "Student access required."}, status=status.HTTP_403_FORBIDDEN)
        interview = get_object_or_404(Interview.objects.filter(student=get_student_profile(request.user)), pk=pk)
        if interview.status == "COMPLETED":
            return Response({"detail": "This interview is already completed. View the report or start another attempt."}, status=status.HTTP_400_BAD_REQUEST)

        answer_text = _safe_text(request.data.get("answer_text"), 12000)
        if not answer_text:
            return Response({"detail": "Write or dictate an answer before continuing."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            question_id = int(request.data.get("question_id"))
        except (TypeError, ValueError):
            return Response({"detail": "Question ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        question = get_object_or_404(InterviewQuestion, pk=question_id, interview=interview)

        evaluation, evaluation_used_ai = evaluate_answer(interview, question.question_text, answer_text)
        answer = _get_latest_or_create_answer(question, answer_text)
        answer.score = evaluation["score"]
        answer.feedback = json.dumps(evaluation, ensure_ascii=False)
        answer.save(update_fields=["answer_text", "score", "feedback"])

        answered_count = InterviewAnswer.objects.filter(
            interview_question__interview=interview,
            answer_text__gt="",
        ).values("interview_question_id").distinct().count()
        limit = question_limit(interview)
        next_question = None
        next_question_used_ai = False

        if answered_count < limit:
            existing_next = interview.questions.filter(order__gt=question.order).exclude(
                answers__answer_text__gt=""
            ).order_by("order").first()
            if existing_next:
                next_question = existing_next
            else:
                max_order = interview.questions.order_by("-order").values_list("order", flat=True).first() or question.order
                generated, next_question_used_ai = make_question(
                    interview,
                    question_number=answered_count + 1,
                    previous_question=question.question_text,
                    previous_answer=answer_text,
                    evaluation=evaluation,
                )
                next_question = InterviewQuestion.objects.create(
                    interview=interview,
                    question_text=generated["question_text"],
                    category=generated["category"],
                    order=max_order + 1,
                )

        result = {
            "answer": InterviewAnswerSerializer(answer).data,
            "evaluation": evaluation,
            "evaluation_used_ai": evaluation_used_ai,
            "next_question": InterviewQuestionSerializer(next_question).data if next_question else None,
            "answered_count": answered_count,
            "question_limit": limit,
            "round_complete": next_question is None,
            "ai_enabled": ai_configured(),
            "next_question_used_ai": next_question_used_ai,
        }
        return Response(result, status=status.HTTP_200_OK)


class InterviewFinishView(APIView):
    """Create a persisted final report from the saved answer-by-answer evaluations."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if getattr(request.user, "role", "") != "STUDENT":
            return Response({"detail": "Student access required."}, status=status.HTTP_403_FORBIDDEN)
        interview = get_object_or_404(Interview.objects.filter(student=get_student_profile(request.user)), pk=pk)
        answer_rows = []
        for question in interview.questions.all().order_by("order"):
            answer = question.answers.order_by("-answered_at").first()
            if answer and answer.answer_text.strip():
                answer_rows.append((question, answer))
        report, report_used_ai = make_final_report(interview, answer_rows)
        feedback = save_feedback(interview, report)
        return Response({
            "interview": InterviewSerializer(interview).data,
            "feedback": InterviewFeedbackSerializer(feedback).data,
            "report_used_ai": report_used_ai,
            "question_count": len(answer_rows),
        }, status=status.HTTP_200_OK)


class FeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(_owned_interviews(request), pk=pk)
        feedback = getattr(obj, "feedback", None)
        return Response(InterviewFeedbackSerializer(feedback).data if feedback else None)

    def post(self, request, pk):
        if getattr(request.user, "role", "") not in ("ADMIN", "FACULTY"):
            return Response({"detail": "Faculty or admin access required."}, status=status.HTTP_403_FORBIDDEN)
        obj = get_object_or_404(Interview, pk=pk)
        from .serializers import InterviewFeedbackSerializer
        serializer = InterviewFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback = save_feedback(obj, serializer.validated_data)
        return Response(InterviewFeedbackSerializer(feedback).data)
