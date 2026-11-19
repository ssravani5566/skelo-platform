from django.utils import timezone
from rest_framework import serializers
from .models import (
    Course, CourseModule, Lesson, LessonResource, CourseProgress,
    LessonProgress, LearningBatch, CourseEnrollment,
)


class LessonResourceSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = LessonResource
        fields = ["id", "lesson", "title", "file", "file_url", "uploaded_at"]
        read_only_fields = ["id", "lesson", "file_url", "uploaded_at"]

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        path = f"/api/courses/files/resource/{obj.id}/"
        return request.build_absolute_uri(path) if request else path


class LessonSerializer(serializers.ModelSerializer):
    video_file = serializers.FileField(required=False, allow_null=True, write_only=True)
    resource_file = serializers.FileField(required=False, allow_null=True, write_only=True)
    completed = serializers.SerializerMethodField()
    last_position_seconds = serializers.SerializerMethodField()
    resource_url = serializers.SerializerMethodField()
    video_file_url = serializers.SerializerMethodField()
    resources = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id", "module", "title", "description", "content", "video_url",
            "video_file", "video_file_url", "resource_file", "resource_url",
            "resources", "order", "duration_minutes", "is_published",
            "completed", "last_position_seconds",
        ]
        read_only_fields = ["resource_url", "video_file_url", "resources", "completed", "last_position_seconds"]

    def _student_progress(self, obj):
        student = self.context.get("student")
        if not student:
            return None
        return LessonProgress.objects.filter(student=student, lesson=obj).first()

    def get_completed(self, obj):
        progress = self._student_progress(obj)
        return bool(progress and progress.completed)

    def get_last_position_seconds(self, obj):
        progress = self._student_progress(obj)
        return progress.last_position_seconds if progress else 0

    def get_resource_url(self, obj):
        if not obj.resource_file:
            return None
        request = self.context.get("request")
        path = f"/api/courses/files/lesson-resource/{obj.id}/"
        return request.build_absolute_uri(path) if request else path

    def get_video_file_url(self, obj):
        if not obj.video_file:
            return None
        request = self.context.get("request")
        path = f"/api/courses/files/video/{obj.id}/"
        return request.build_absolute_uri(path) if request else path

    def get_resources(self, obj):
        request = self.context.get("request")
        return LessonResourceSerializer(obj.resources.all(), many=True, context={"request": request}).data


class CourseModuleSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    assessments = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()

    class Meta:
        model = CourseModule
        fields = ["id", "course", "title", "description", "order", "lessons", "assessments", "assignments"]
        read_only_fields = ["lessons", "assessments", "assignments"]

    def get_lessons(self, obj):
        student = self.context.get("student")
        if self.context.get("preview"):
            return [{"id": item.id, "title": item.title, "duration_minutes": item.duration_minutes, "order": item.order} for item in obj.lessons.filter(is_published=True)]
        qs = obj.lessons.all()
        if student:
            qs = qs.filter(is_published=True)
        return LessonSerializer(qs, many=True, context={"request": self.context.get("request"), "student": student}).data

    def get_assessments(self, obj):
        qs = obj.assessment_links.select_related("assessment").all()
        if self.context.get("preview"):
            return []
        student = self.context.get("student")
        if student:
            qs = qs.filter(assessment__is_published=True)
        return [{
            "id": link.assessment_id,
            "title": link.assessment.title,
            "description": link.assessment.description,
            "assessment_type": link.assessment.assessment_type,
            "duration_minutes": link.assessment.duration_minutes,
            "total_marks": link.assessment.total_marks,
            "passing_marks": link.assessment.passing_marks,
            "is_published": link.assessment.is_published,
        } for link in qs]

    def get_assignments(self, obj):
        qs = obj.assignment_links.select_related("assignment").all()
        if self.context.get("preview"):
            return []
        student = self.context.get("student")
        if student:
            qs = qs.filter(assignment__status="PUBLISHED")
        return [{
            "id": link.assignment_id,
            "title": link.assignment.title,
            "description": link.assignment.description,
            "due_date": link.assignment.due_date,
            "duration_minutes": link.assignment.duration_minutes,
            "max_marks": link.assignment.max_marks,
            "status": link.assignment.status,
        } for link in qs]


class CourseSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    completed_lessons = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    enrolled = serializers.SerializerMethodField()
    can_enroll = serializers.SerializerMethodField()
    trainer_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "description", "category", "level", "language",
            "learning_outcomes", "prerequisites", "access_type", "price", "minimum_quiz_percentage", "require_assignment_approval", "thumbnail",
            "thumbnail_url", "duration_minutes", "is_published", "is_archived",
            "created_by", "created_at", "updated_at", "progress", "lessons",
            "completed", "completed_lessons", "enrolled", "can_enroll", "trainer_name",
        ]
        read_only_fields = [
            "created_by", "created_at", "updated_at", "progress", "lessons",
            "completed", "completed_lessons", "thumbnail_url", "enrolled", "can_enroll", "trainer_name",
        ]

    def _student(self):
        return self.context.get("student")

    def get_progress(self, obj):
        student = self._student()
        if not student:
            return 0
        p = CourseProgress.objects.filter(student=student, course=obj).first()
        return float(p.percentage) if p else 0

    def get_lessons(self, obj):
        qs = Lesson.objects.filter(module__course=obj, is_published=True)
        if self._student():
            return qs.count()
        return Lesson.objects.filter(module__course=obj).count()

    def get_completed(self, obj):
        student = self._student()
        if not student:
            return False
        return CourseProgress.objects.filter(student=student, course=obj, completed=True).exists()

    def get_completed_lessons(self, obj):
        student = self._student()
        if not student:
            return 0
        return LessonProgress.objects.filter(student=student, lesson__module__course=obj, completed=True).count()

    def get_enrolled(self, obj):
        student = self._student()
        if not student:
            return False
        enrollment = CourseEnrollment.objects.filter(student=student, course=obj).first()
        return bool(enrollment and enrollment.is_active)

    def get_can_enroll(self, obj):
        student = self._student()
        if not student:
            return False
        if self.get_enrolled(obj):
            return True
        already_enrolled = CourseEnrollment.objects.filter(student=student, course=obj).exists()
        return not already_enrolled and obj.access_type == "FREE" and obj.is_published and not obj.is_archived

    def get_trainer_name(self, obj):
        if not obj.created_by:
            return "Not assigned"
        return obj.created_by.get_full_name() or obj.created_by.username or obj.created_by.email

    def get_thumbnail_url(self, obj):
        if not obj.thumbnail:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.thumbnail.url) if request else obj.thumbnail.url


class CourseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseProgress
        fields = ["id", "course", "percentage", "completed", "started_at", "updated_at"]
        read_only_fields = ["id", "percentage", "completed", "started_at", "updated_at"]


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(read_only=True)
    access_active = serializers.SerializerMethodField()
    course_detail = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = ["id", "course", "student_id", "source", "assigned_batch", "access_expires_at", "access_active", "enrolled_at", "course_detail"]
        read_only_fields = fields

    def get_access_active(self, obj):
        return obj.is_active

    def get_course_detail(self, obj):
        request = self.context.get("request")
        student = obj.student
        return CourseSerializer(obj.course, context={"request": request, "student": student}).data


class LearningBatchSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = LearningBatch
        fields = ["id", "name", "code", "description", "is_active", "students", "student_count", "created_at"]
        read_only_fields = ["student_count", "created_at"]

    def get_students(self, obj):
        return [{
            "id": profile.id,
            "name": profile.user.get_full_name() or profile.user.username,
            "email": profile.user.email,
            "register_number": profile.register_number,
        } for profile in obj.students.select_related("user").all()]

    def get_student_count(self, obj):
        return obj.students.count()
