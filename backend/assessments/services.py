from django.db import transaction
from django.utils import timezone
from core.notifications import create_notification
from gamification.services import award_xp
from .models import Assessment, StudentAssessment, StudentAnswer


def is_open(assessment):
    now = timezone.now()
    return assessment.is_published and (not assessment.start_at or now >= assessment.start_at) and (not assessment.end_at or now <= assessment.end_at)


def get_or_create_attempt(student, assessment):
    attempt, created = StudentAssessment.objects.get_or_create(student=student, assessment=assessment)
    if created or attempt.status == "NOT_STARTED":
        attempt.status = "IN_PROGRESS"; attempt.started_at = timezone.now(); attempt.save(update_fields=["status", "started_at"])
    return attempt


@transaction.atomic
def submit_attempt(attempt):
    assessment = attempt.assessment
    assessment_questions = {
        aq.question_id: (aq.marks if aq.marks is not None else aq.question.marks)
        for aq in assessment.assessment_questions.select_related("question")
    }
    total = sum(assessment_questions.values())
    score = 0
    for answer in attempt.answers.select_related("question"):
        q = answer.question
        correct = False
        if q.question_type in {"MCQ", "TRUE_FALSE", "SHORT"}:
            correct = answer.answer_text.strip().casefold() == q.correct_answer.strip().casefold()
        elif q.question_type == "CODING":
            try:
                import json
                correct = bool(json.loads(answer.answer_text).get("status") == "ACCEPTED")
            except Exception:
                correct = False
        marks = assessment_questions.get(q.id, q.marks)
        answer.is_correct = correct
        answer.marks_awarded = marks if correct else 0
        score += answer.marks_awarded
        answer.save(update_fields=["is_correct", "marks_awarded"])
    attempt.score = score
    attempt.percentage = round((score / total) * 100, 2) if total else 0
    attempt.status = "EVALUATED"
    attempt.submitted_at = timezone.now(); attempt.evaluated_at = timezone.now()
    attempt.save(update_fields=["score", "percentage", "status", "submitted_at", "evaluated_at"])
    award_xp(attempt.student, "ASSESSMENT", max(10, int(round(float(attempt.score)))), f"Completed assessment: {assessment.title}", source_key=f"assessment:{assessment.id}")
    create_notification(attempt.student.user, "Assessment completed", f"Your result for {assessment.title} is {attempt.percentage}%.", "ASSESSMENT")
    return attempt
