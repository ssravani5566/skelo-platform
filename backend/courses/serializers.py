from django.db.models import Count
from rest_framework import serializers
from .models import Course, CourseModule, Lesson, CourseProgress, LessonProgress


class LessonSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()
    resource_url = serializers.SerializerMethodField()
    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "content", "video_url", "resource_file", "resource_url", "order", "duration_minutes", "is_published", "completed"]
        read_only_fields = ["resource_url", "completed"]
    def get_completed(self, obj):
        student = self.context.get("student")
        if not student: return False
        return LessonProgress.objects.filter(student=student, lesson=obj, completed=True).exists()
    def get_resource_url(self, obj):
        if not obj.resource_file: return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.resource_file.url) if request else obj.resource_file.url


class CourseModuleSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    class Meta:
        model = CourseModule
        fields = ["id", "course", "title", "description", "order", "lessons"]
        read_only_fields = ["lessons"]
    def get_lessons(self, obj):
        student = self.context.get("student")
        return LessonSerializer(obj.lessons.filter(is_published=True), many=True, context={"request": self.context.get("request"), "student": student}).data


class CourseSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ["id", "title", "slug", "description", "category", "level", "thumbnail", "thumbnail_url", "duration_minutes", "is_published", "created_by", "created_at", "updated_at", "progress", "lessons", "completed"]
        read_only_fields = ["created_by", "created_at", "updated_at", "progress", "lessons", "completed", "thumbnail_url"]
    def get_progress(self, obj):
        student = self.context.get("student")
        if not student: return 0
        p = CourseProgress.objects.filter(student=student, course=obj).first()
        return float(p.percentage) if p else 0
    def get_lessons(self, obj):
        return obj.modules.filter(lessons__is_published=True).values("lessons__id").count()
    def get_completed(self, obj):
        student = self.context.get("student")
        if not student: return False
        return CourseProgress.objects.filter(student=student, course=obj, completed=True).exists()
    def get_thumbnail_url(self, obj):
        if not obj.thumbnail: return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.thumbnail.url) if request else obj.thumbnail.url


class CourseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseProgress
        fields = ["id", "course", "percentage", "completed", "started_at", "updated_at"]
        read_only_fields = ["id", "percentage", "completed", "started_at", "updated_at"]
