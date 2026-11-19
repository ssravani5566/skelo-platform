from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.api import paginated_response
from students.models import StudentProfile
from students.services import get_student_profile
from assessments.models import Assessment
from assignments.models import Assignment
from .models import (
    Course, CourseModule, Lesson, LessonResource, CourseProgress, LessonProgress,
    LearningBatch, CourseBatchAssignment, CourseEnrollment,
    CourseModuleAssessment, CourseModuleAssignment,
)
from .serializers import (
    CourseModuleSerializer, CourseProgressSerializer, CourseSerializer,
    LessonSerializer, LearningBatchSerializer, CourseEnrollmentSerializer,
)
from .services import complete_lesson, refresh_course_progress, start_course


STAFF_ROLES = ("ADMIN", "FACULTY")


def _student_for(user):
    return get_student_profile(user) if user.role == "STUDENT" else None


def _has_course_access(student, course):
    if not student:
        return False
    now = timezone.now()
    enrollment = CourseEnrollment.objects.filter(student=student, course=course).first()
    if enrollment and enrollment.is_active:
        return True

    # A student may receive access through a second batch after an earlier
    # assignment expired. Reconcile the saved enrolment rather than blocking
    # the newly assigned access or discarding its learning history.
    batch_assignment = CourseBatchAssignment.objects.filter(
        course=course,
        batch__is_active=True,
        batch__students=student,
    ).filter(Q(access_expires_at__isnull=True) | Q(access_expires_at__gt=now)).select_related("batch").first()
    if batch_assignment:
        CourseEnrollment.objects.update_or_create(
            student=student,
            course=course,
            defaults={
                "source": "BATCH",
                "assigned_batch": batch_assignment.batch,
                "access_expires_at": batch_assignment.access_expires_at,
            },
        )
        return True
    return False


def _require_student_access(request, course):
    if request.user.role != "STUDENT":
        return None
    if not course.is_published or course.is_archived:
        return Response({"detail": "Course is not available."}, status=404)
    student = _student_for(request.user)
    if not _has_course_access(student, course):
        return Response({"detail": "Enrol in this course or ask your administrator to assign it before opening lessons."}, status=403)
    enrollment = CourseEnrollment.objects.filter(student=student, course=course).first()
    if enrollment and not enrollment.is_active:
        return Response({"detail": "Your access to this course has expired. Contact your administrator."}, status=403)
    return None


def _file_response(field_file, filename=None):
    if not field_file:
        return Response({"detail": "File not found."}, status=404)
    try:
        field_file.open("rb")
        return FileResponse(field_file, as_attachment=True, filename=filename or field_file.name.rsplit("/", 1)[-1])
    except (OSError, ValueError):
        return Response({"detail": "The requested file is unavailable."}, status=404)


class HealthView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({"status": "ok"})


class CourseListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        qs = Course.objects.prefetch_related("modules__lessons").filter(is_archived=False)
        if request.user.role == "STUDENT":
            qs = qs.filter(is_published=True)
        elif request.query_params.get("published") in {"true", "false"}:
            qs = qs.filter(is_published=request.query_params["published"] == "true")
        if request.query_params.get("archived") == "true" and request.user.role in STAFF_ROLES:
            qs = Course.objects.filter(is_archived=True)
        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(category__icontains=q) | Q(description__icontains=q))
        level = request.query_params.get("level")
        if level:
            qs = qs.filter(level=level.upper())
        student = _student_for(request.user)
        if student:
            for course in qs:
                if _has_course_access(student, course):
                    refresh_course_progress(student, course)
        data = CourseSerializer(qs.order_by("title"), many=True, context={"request": request, "student": student}).data
        return paginated_response(request, data)

    def post(self, request):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        payload = request.data.copy()
        if not payload.get("slug"):
            base = slugify(payload.get("title", "course")) or "course"
            candidate = base
            counter = 2
            while Course.objects.filter(slug=candidate).exists():
                candidate = f"{base}-{counter}"
                counter += 1
            payload["slug"] = candidate
        serializer = CourseSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(created_by=request.user)
        return Response(CourseSerializer(obj, context={"request": request}).data, status=201)


class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, pk):
        qs = Course.objects.prefetch_related("modules__lessons")
        if request.user.role == "STUDENT":
            qs = qs.filter(is_published=True, is_archived=False)
        course = get_object_or_404(qs, pk=pk)
        student = _student_for(request.user)
        if student and _has_course_access(student, course):
            refresh_course_progress(student, course)
        return Response(CourseSerializer(course, context={"request": request, "student": student}).data)

    def patch(self, request, pk):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=pk)
        if request.user.role == "FACULTY" and course.created_by_id not in (None, request.user.id):
            return Response({"detail": "You can edit only your courses."}, status=403)
        serializer = CourseSerializer(course, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CourseSerializer(course, context={"request": request}).data)

    def delete(self, request, pk):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=pk)
        course.is_archived = True
        course.is_published = False
        course.save(update_fields=["is_archived", "is_published", "updated_at"])
        return Response({"detail": "Course archived. Enrolments and learning records have been preserved."})


class CourseModulesView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id, **({"is_published": True, "is_archived": False} if request.user.role == "STUDENT" else {}))
        student = _student_for(request.user)
        has_access = bool(student and _has_course_access(student, course))
        if has_access:
            refresh_course_progress(student, course)
        preview = bool(student and not has_access)
        return Response(CourseModuleSerializer(course.modules.all(), many=True, context={"request": request, "student": student, "preview": preview}).data)

    def post(self, request, course_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=course_id)
        payload = request.data.copy()
        try:
            requested_order = max(1, int(payload.get("order") or 1))
        except (TypeError, ValueError):
            return Response({"detail": "Module order must be a positive whole number."}, status=400)
        if CourseModule.objects.filter(course=course, order=requested_order).exists():
            last_order = CourseModule.objects.filter(course=course).order_by("-order").values_list("order", flat=True).first() or 0
            payload["order"] = last_order + 1
        payload["course"] = course.id
        serializer = CourseModuleSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(CourseModuleSerializer(obj, context={"request": request}).data, status=201)

    def patch(self, request, course_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        obj = get_object_or_404(CourseModule, pk=request.data.get("id"), course_id=course_id)
        serializer = CourseModuleSerializer(obj, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CourseModuleSerializer(obj, context={"request": request}).data)

    def delete(self, request, course_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        get_object_or_404(CourseModule, pk=request.data.get("id"), course_id=course_id).delete()
        return Response(status=204)


class LessonsView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id, **({"is_published": True, "is_archived": False} if request.user.role == "STUDENT" else {}))
        denied = _require_student_access(request, course)
        if denied:
            return denied
        qs = Lesson.objects.filter(module__course_id=course_id).select_related("module")
        if request.user.role == "STUDENT":
            qs = qs.filter(is_published=True)
        student = _student_for(request.user)
        return Response(LessonSerializer(qs, many=True, context={"request": request, "student": student}).data)

    def post(self, request, course_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        module_id = request.data.get("module") or request.data.get("module_id")
        module = get_object_or_404(CourseModule, pk=module_id, course_id=course_id)
        payload = request.data.copy()
        payload["module"] = module.id
        serializer = LessonSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(LessonSerializer(obj, context={"request": request}).data, status=201)

    def patch(self, request, course_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        obj = get_object_or_404(Lesson, pk=request.data.get("id"), module__course_id=course_id)
        payload = request.data.copy()
        target_module_id = payload.get("module") or payload.get("module_id")
        if target_module_id:
            target_module = get_object_or_404(CourseModule, pk=target_module_id, course_id=course_id)
            payload["module"] = target_module.id
        serializer = LessonSerializer(obj, data=payload, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(LessonSerializer(obj, context={"request": request}).data)

    def delete(self, request, course_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        get_object_or_404(Lesson, pk=request.data.get("id"), module__course_id=course_id).delete()
        return Response(status=204)


class LessonResourceView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, lesson_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "Choose a file to upload."}, status=400)
        if file_obj.size > 25 * 1024 * 1024:
            return Response({"detail": "Each lesson note must be 25 MB or smaller."}, status=400)
        from .serializers import LessonResourceSerializer
        resource = LessonResource.objects.create(lesson=lesson, title=request.data.get("title") or file_obj.name, file=file_obj)
        return Response(LessonResourceSerializer(resource, context={"request": request}).data, status=201)

    def delete(self, request, lesson_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        get_object_or_404(LessonResource, pk=request.data.get("id"), lesson_id=lesson_id).delete()
        return Response(status=204)


class CourseStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        course = get_object_or_404(Course, pk=pk, is_published=True, is_archived=False)
        denied = _require_student_access(request, course)
        if denied:
            return denied
        return Response(CourseProgressSerializer(start_course(_student_for(request.user), course)).data)


class CourseEnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        course = get_object_or_404(Course, pk=pk, is_published=True, is_archived=False)
        student = _student_for(request.user)
        existing = CourseEnrollment.objects.filter(student=student, course=course).first()
        if _has_course_access(student, course):
            enrollment = CourseEnrollment.objects.get(student=student, course=course)
            return Response(CourseEnrollmentSerializer(enrollment, context={"request": request}).data)
        if existing and not existing.is_active:
            return Response({"detail": "Your course access has expired. Contact your administrator."}, status=403)
        if course.access_type != "FREE":
            return Response({"detail": "This is a paid course. Contact your administrator for access; online payments are not enabled."}, status=403)
        with transaction.atomic():
            enrollment, _ = CourseEnrollment.objects.get_or_create(student=student, course=course, defaults={"source": "SELF"})
            start_course(student, course)
        return Response(CourseEnrollmentSerializer(enrollment, context={"request": request}).data, status=201)


class LessonCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        lesson = get_object_or_404(Lesson, pk=pk, is_published=True)
        course = lesson.module.course
        if not course.is_published or course.is_archived:
            return Response({"detail": "Course is not available."}, status=404)
        denied = _require_student_access(request, course)
        if denied:
            return denied
        student = _student_for(request.user)
        complete_lesson(student, lesson)
        return Response(LessonSerializer(lesson, context={"request": request, "student": student}).data)


class LessonVideoProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        lesson = get_object_or_404(Lesson, pk=pk, is_published=True)
        denied = _require_student_access(request, lesson.module.course)
        if denied:
            return denied
        try:
            position = max(0, int(request.data.get("position_seconds", 0)))
        except (TypeError, ValueError):
            return Response({"detail": "Video position must be a number."}, status=400)
        progress, _ = LessonProgress.objects.get_or_create(student=_student_for(request.user), lesson=lesson)
        progress.last_position_seconds = position
        progress.save(update_fields=["last_position_seconds", "last_accessed_at"])
        return Response({"last_position_seconds": progress.last_position_seconds, "completed": progress.completed})


class MyCourseProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        qs = CourseProgress.objects.filter(student=_student_for(request.user)).select_related("course")
        return Response(CourseProgressSerializer(qs, many=True).data)


class MyLearningView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student access required."}, status=403)
        student = _student_for(request.user)
        qs = CourseEnrollment.objects.filter(student=student).select_related("course").filter(course__is_archived=False, course__is_published=True)
        for enrollment in qs:
            if _has_course_access(student, enrollment.course):
                refresh_course_progress(student, enrollment.course)
        data = CourseEnrollmentSerializer(qs, many=True, context={"request": request}).data
        return Response(data)


class CourseBatchesView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        qs = LearningBatch.objects.prefetch_related("students__user").all()
        return Response(LearningBatchSerializer(qs, many=True).data)

    def post(self, request):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        serializer = LearningBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        student_ids = request.data.get("student_ids", [])
        if student_ids:
            batch.students.set(StudentProfile.objects.filter(id__in=student_ids))
        return Response(LearningBatchSerializer(batch).data, status=201)


class CourseBatchDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        batch = get_object_or_404(LearningBatch, pk=pk)
        serializer = LearningBatchSerializer(batch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if "student_ids" in request.data:
            requested_ids = set(int(value) for value in request.data.get("student_ids", []))
            removed_ids = set(batch.students.values_list("id", flat=True)) - requested_ids
            if removed_ids:
                CourseEnrollment.objects.filter(course__batch_assignments__batch=batch, student_id__in=removed_ids, source="BATCH", assigned_batch=batch).update(access_expires_at=timezone.now())
            batch.students.set(StudentProfile.objects.filter(id__in=requested_ids))
        _sync_batch_enrollments(batch)
        return Response(LearningBatchSerializer(batch).data)

    def delete(self, request, pk):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        batch = get_object_or_404(LearningBatch, pk=pk)
        CourseEnrollment.objects.filter(assigned_batch=batch, source="BATCH").update(access_expires_at=timezone.now())
        batch.delete()
        return Response(status=204)


def _sync_batch_enrollments(batch):
    for assignment in batch.course_assignments.select_related("course").all():
        for student in batch.students.all():
            enrollment, created = CourseEnrollment.objects.get_or_create(
                student=student,
                course=assignment.course,
                defaults={"source": "BATCH", "assigned_batch": batch, "access_expires_at": assignment.access_expires_at},
            )
            if not created and enrollment.source == "BATCH":
                enrollment.assigned_batch = batch
                enrollment.access_expires_at = assignment.access_expires_at
                enrollment.save(update_fields=["assigned_batch", "access_expires_at"])


class CourseAdminStudentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        qs = StudentProfile.objects.select_related("user").order_by("user__first_name", "user__email")
        return Response([{
            "id": p.id,
            "name": p.user.get_full_name() or p.user.username,
            "email": p.user.email,
            "register_number": p.register_number,
            "department": p.department,
            "year": p.year,
        } for p in qs])


class CourseAssignmentsView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, pk):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=pk)
        return Response({
            "enrollments": CourseEnrollmentSerializer(course.enrollments.select_related("student__user", "assigned_batch"), many=True, context={"request": request}).data,
            "batches": [{"id": x.batch_id, "name": x.batch.name, "access_expires_at": x.access_expires_at} for x in course.batch_assignments.select_related("batch")],
        })

    def post(self, request, pk):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=pk)
        student_ids = request.data.get("student_ids", []) or []
        batch_ids = request.data.get("batch_ids", []) or []
        expiry = request.data.get("access_expires_at") or None
        created = 0
        selected_students = set(int(value) for value in student_ids)
        selected_batches = set(int(value) for value in batch_ids)
        with transaction.atomic():
            # Treat this form as the current access selection; removing a student or
            # batch expires the course access but never deletes their learning history.
            CourseEnrollment.objects.filter(course=course, source="INDIVIDUAL").exclude(student_id__in=selected_students).update(access_expires_at=timezone.now())
            removed_batch_ids = list(CourseBatchAssignment.objects.filter(course=course).exclude(batch_id__in=selected_batches).values_list("batch_id", flat=True))
            if removed_batch_ids:
                CourseEnrollment.objects.filter(course=course, source="BATCH", assigned_batch_id__in=removed_batch_ids).update(access_expires_at=timezone.now())
                CourseBatchAssignment.objects.filter(course=course, batch_id__in=removed_batch_ids).delete()
            for student in StudentProfile.objects.filter(id__in=student_ids):
                enrollment, was_created = CourseEnrollment.objects.get_or_create(
                    student=student, course=course,
                    defaults={"source": "INDIVIDUAL", "access_expires_at": expiry},
                )
                if not was_created:
                    # An explicit individual selection should remain valid even
                    # when the student previously received access through a batch.
                    enrollment.source = "INDIVIDUAL"
                    enrollment.assigned_batch = None
                    enrollment.access_expires_at = expiry
                    enrollment.save(update_fields=["source", "assigned_batch", "access_expires_at"])
                created += int(was_created)
            for batch in LearningBatch.objects.filter(id__in=batch_ids, is_active=True):
                CourseBatchAssignment.objects.update_or_create(
                    course=course, batch=batch, defaults={"access_expires_at": expiry},
                )
                for student in batch.students.all():
                    enrollment, was_created = CourseEnrollment.objects.get_or_create(
                        student=student, course=course,
                        defaults={"source": "BATCH", "assigned_batch": batch, "access_expires_at": expiry},
                    )
                    if not was_created and enrollment.source == "BATCH":
                        enrollment.assigned_batch = batch
                        enrollment.access_expires_at = expiry
                        enrollment.save(update_fields=["assigned_batch", "access_expires_at"])
                    created += int(was_created)
        return Response({"created_enrollments": created, "detail": "Course access assignments saved."})


class CourseModuleActivitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id, module_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        module = get_object_or_404(CourseModule, pk=module_id, course_id=course_id)
        kind = request.data.get("kind")
        activity_id = request.data.get("activity_id")
        if kind == "assessment":
            activity = get_object_or_404(Assessment, pk=activity_id)
            link, _ = CourseModuleAssessment.objects.get_or_create(module=module, assessment=activity)
        elif kind == "assignment":
            activity = get_object_or_404(Assignment, pk=activity_id)
            link, _ = CourseModuleAssignment.objects.get_or_create(module=module, assignment=activity)
        else:
            return Response({"detail": "Activity kind must be assessment or assignment."}, status=400)
        return Response({"id": link.id, "kind": kind, "activity_id": activity.id}, status=201)

    def delete(self, request, course_id, module_id):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        module = get_object_or_404(CourseModule, pk=module_id, course_id=course_id)
        kind = request.data.get("kind")
        activity_id = request.data.get("activity_id")
        if kind == "assessment":
            CourseModuleAssessment.objects.filter(module=module, assessment_id=activity_id).delete()
        elif kind == "assignment":
            CourseModuleAssignment.objects.filter(module=module, assignment_id=activity_id).delete()
        else:
            return Response({"detail": "Activity kind must be assessment or assignment."}, status=400)
        return Response(status=204)


class CourseReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if request.user.role not in STAFF_ROLES:
            return Response({"detail": "Faculty or admin access required."}, status=403)
        course = get_object_or_404(Course, pk=pk)
        rows = []
        cutoff = timezone.now() - timedelta(days=7)
        assessment_ids = list(CourseModuleAssessment.objects.filter(module__course=course).values_list("assessment_id", flat=True).distinct())
        assignment_ids = list(CourseModuleAssignment.objects.filter(module__course=course).values_list("assignment_id", flat=True).distinct())
        from assessments.models import StudentAssessment
        from assignments.models import AssignmentSubmission
        for enrollment in course.enrollments.select_related("student__user"):
            refresh_course_progress(enrollment.student, course)
            progress = CourseProgress.objects.filter(student=enrollment.student, course=course).first()
            quiz_rows = list(StudentAssessment.objects.filter(student=enrollment.student, assessment_id__in=assessment_ids).select_related("assessment").order_by("-submitted_at")) if assessment_ids else []
            submission_rows = list(AssignmentSubmission.objects.filter(student=enrollment.student, assignment_id__in=assignment_ids).select_related("assignment", "evaluation").order_by("-submitted_at")) if assignment_ids else []
            latest = LessonProgress.objects.filter(student=enrollment.student, lesson__module__course=course).order_by("-last_accessed_at").first()
            latest_quiz = StudentAssessment.objects.filter(student=enrollment.student, assessment_id__in=assessment_ids).order_by("-submitted_at").first() if assessment_ids else None
            latest_assignment = AssignmentSubmission.objects.filter(student=enrollment.student, assignment_id__in=assignment_ids).order_by("-submitted_at").first() if assignment_ids else None
            activity_dates = [value for value in [latest.last_accessed_at if latest else None, latest_quiz.submitted_at if latest_quiz else None, latest_assignment.submitted_at if latest_assignment else None, enrollment.enrolled_at] if value]
            last_activity = max(activity_dates) if activity_dates else None
            rows.append({
                "student_id": enrollment.student_id,
                "student": enrollment.student.user.get_full_name() or enrollment.student.user.username,
                "email": enrollment.student.user.email,
                "register_number": enrollment.student.register_number,
                "progress": float(progress.percentage) if progress else 0,
                "completed": bool(progress and progress.completed),
                "last_activity": last_activity,
                "inactive": not last_activity or last_activity < cutoff,
                "source": enrollment.source,
                "access_expires_at": enrollment.access_expires_at,
                "quiz_attempts": len(quiz_rows),
                "quiz_scores": [{"title": row.assessment.title, "score": float(row.score), "percentage": float(row.percentage), "status": row.status} for row in quiz_rows],
                "assignment_submissions": len(submission_rows),
                "assignment_results": [{"title": row.assignment.title, "status": row.status, "submitted_at": row.submitted_at, "marks": float(row.evaluation.marks) if hasattr(row, "evaluation") else None, "max_marks": row.assignment.max_marks} for row in submission_rows],
            })
        return Response({
            "course": {"id": course.id, "title": course.title},
            "enrolled_count": len(rows),
            "completed_count": sum(1 for row in rows if row["completed"]),
            "inactive_count": sum(1 for row in rows if row["inactive"]),
            "students": rows,
        })


class ProtectedCourseFileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, kind, pk):
        if kind == "resource":
            resource = get_object_or_404(LessonResource.objects.select_related("lesson__module__course"), pk=pk)
            lesson = resource.lesson
            field_file = resource.file
            name = field_file.name.rsplit("/", 1)[-1] if field_file else None
        elif kind == "lesson-resource":
            lesson = get_object_or_404(Lesson.objects.select_related("module__course"), pk=pk)
            field_file = lesson.resource_file
            name = field_file.name.rsplit("/", 1)[-1] if field_file else None
        elif kind == "video":
            lesson = get_object_or_404(Lesson.objects.select_related("module__course"), pk=pk)
            field_file = lesson.video_file
            name = field_file.name.rsplit("/", 1)[-1] if field_file else None
        else:
            return Response({"detail": "Unknown file type."}, status=404)
        course = lesson.module.course
        if request.user.role == "STUDENT":
            if not course.is_published or course.is_archived:
                return Response({"detail": "Course is not available."}, status=404)
            denied = _require_student_access(request, course)
            if denied:
                return denied
        return _file_response(field_file, name)
