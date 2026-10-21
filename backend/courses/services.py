from django.db import transaction
from django.utils import timezone
from .models import Course, CourseModule, Lesson, CourseProgress, LessonProgress
from core.notifications import create_notification


@transaction.atomic
def start_course(student, course):
    progress, _ = CourseProgress.objects.get_or_create(student=student, course=course)
    return progress


def complete_lesson(student, lesson):
    progress, _ = LessonProgress.objects.get_or_create(student=student, lesson=lesson)
    if progress.completed:
        return progress
    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save(update_fields=["completed", "completed_at"])
    course = lesson.module.course
    total = Lesson.objects.filter(module__course=course, is_published=True).count()
    completed = LessonProgress.objects.filter(student=student, lesson__module__course=course, completed=True).count()
    pct = round((completed / total) * 100, 2) if total else 0
    cp, _ = CourseProgress.objects.get_or_create(student=student, course=course)
    cp.percentage = pct
    cp.completed = pct >= 100
    cp.save(update_fields=["percentage", "completed", "updated_at"])
    if cp.completed:
        create_notification(student.user, "Course completed", f"You completed {course.title}.", "COURSE")
    return progress
