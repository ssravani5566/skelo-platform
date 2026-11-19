from django.contrib import admin
from .models import (
    Course, CourseModule, Lesson, LessonResource, CourseProgress, LessonProgress,
    LearningBatch, CourseEnrollment, CourseBatchAssignment,
    CourseModuleAssessment, CourseModuleAssignment,
)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "level", "access_type", "is_published", "is_archived")
    list_filter = ("level", "access_type", "is_published", "is_archived")
    search_fields = ("title", "slug", "category")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CourseModuleInline]


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order", "is_published")
    list_filter = ("is_published", "module__course")


admin.site.register(LessonResource)
admin.site.register(CourseProgress)
admin.site.register(LessonProgress)
admin.site.register(LearningBatch)
admin.site.register(CourseEnrollment)
admin.site.register(CourseBatchAssignment)
admin.site.register(CourseModuleAssessment)
admin.site.register(CourseModuleAssignment)
