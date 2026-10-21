from django.utils import timezone

from core.notifications import create_notification
from gamification.services import award_xp

from .models import Assignment, AssignmentSubmission, AssignmentEvaluation


def submit_assignment(
    student,
    assignment,
    answer_text="",
    submitted_file=None,
):
    status = (
        "LATE"
        if timezone.now() > assignment.due_date
        else "SUBMITTED"
    )

    sub, _ = AssignmentSubmission.objects.update_or_create(
        assignment=assignment,
        student=student,
        defaults={
            "answer_text": answer_text,
            "submitted_file": submitted_file,
            "status": status,
            "submitted_at": timezone.now(),
        },
    )

    create_notification(
        student.user,
        "Assignment submitted",
        f"Your submission for {assignment.title} was recorded.",
        "ASSIGNMENT",
    )

    return sub


def evaluate_assignment(
    evaluator,
    submission,
    marks,
    feedback,
):
    if (
        marks < 0
        or marks > submission.assignment.max_marks
    ):
        raise ValueError(
            "Marks must be within the assignment maximum."
        )

    evaluation, _ = AssignmentEvaluation.objects.update_or_create(
        submission=submission,
        defaults={
            "evaluator": evaluator,
            "marks": marks,
            "feedback": feedback,
        },
    )

    submission.status = "EVALUATED"
    submission.save(update_fields=["status"])

    award_xp(
        submission.student,
        "ASSIGNMENT",
        max(5, int(round(float(marks)))),
        f"Assignment evaluated: {submission.assignment.title}",
        source_key=f"assignment:{submission.assignment.id}",
    )

    create_notification(
        submission.student.user,
        "Assignment evaluated",
        (
            f"{submission.assignment.title} was evaluated: "
            f"{marks}/{submission.assignment.max_marks}."
        ),
        "ASSIGNMENT",
    )

    return evaluation
