from django.db import transaction
from django.utils import timezone
from core.notifications import create_notification
from .models import (
    Course, CourseModuleAssessment, CourseModuleAssignment, CourseProgress,
    Lesson, LessonProgress,
)
from assessments.models import StudentAssessment
from assignments.models import AssignmentSubmission


@transaction.atomic
def start_course(student, course):
    progress, _ = CourseProgress.objects.get_or_create(student=student, course=course)
    refresh_course_progress(student, course, progress=progress)
    return progress


@transaction.atomic
def refresh_course_progress(student, course, progress=None):
    """Recalculate progress from lessons and the course's configured activities."""
    progress = progress or CourseProgress.objects.filter(student=student, course=course).first()
    if progress is None:
        progress, _ = CourseProgress.objects.get_or_create(student=student, course=course)
    total_lessons = Lesson.objects.filter(module__course=course, is_published=True).count()
    completed_lessons = LessonProgress.objects.filter(
        student=student, lesson__module__course=course, lesson__is_published=True, completed=True
    ).count()
    lesson_tasks = total_lessons
    assessment_ids = list(CourseModuleAssessment.objects.filter(
        module__course=course, assessment__is_published=True
    ).values_list("assessment_id", flat=True).distinct())
    passed_assessment_ids = set()
    if assessment_ids:
        passed_assessment_ids = set(StudentAssessment.objects.filter(
            student=student,
            assessment_id__in=assessment_ids,
            status="EVALUATED",
            percentage__gte=course.minimum_quiz_percentage,
        ).values_list("assessment_id", flat=True).distinct())
    assignment_ids = []
    evaluated_assignment_ids = set()
    if course.require_assignment_approval:
        assignment_ids = list(CourseModuleAssignment.objects.filter(
            module__course=course, assignment__status="PUBLISHED"
        ).values_list("assignment_id", flat=True).distinct())
        if assignment_ids:
            evaluated_assignment_ids = set(AssignmentSubmission.objects.filter(
                student=student, assignment_id__in=assignment_ids, status="EVALUATED"
            ).values_list("assignment_id", flat=True).distinct())
    required_total = lesson_tasks + len(assessment_ids) + len(assignment_ids)
    completed_total = completed_lessons + len(passed_assessment_ids) + len(evaluated_assignment_ids)
    percentage = round((completed_total / required_total) * 100, 2) if required_total else 0
    was_completed = progress.completed
    progress.percentage = percentage
    progress.completed = bool(required_total and completed_total >= required_total)
    progress.save(update_fields=["percentage", "completed", "updated_at"])
    if progress.completed and not was_completed:
        create_notification(student.user, "Course completed", f"You completed {course.title}.", "COURSE")
    return progress


def complete_lesson(student, lesson):
    progress, _ = LessonProgress.objects.get_or_create(student=student, lesson=lesson)
    if not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=["completed", "completed_at", "last_accessed_at"])
    course = lesson.module.course
    refresh_course_progress(student, course)
    return progress
