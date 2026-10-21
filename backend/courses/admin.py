from django.contrib import admin
from .models import Course, CourseModule, Lesson, CourseProgress, LessonProgress

admin.site.register(Course)
admin.site.register(CourseModule)
admin.site.register(Lesson)
admin.site.register(CourseProgress)
admin.site.register(LessonProgress)
