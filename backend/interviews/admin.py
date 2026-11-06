from django.contrib import admin
from .models import Interview, InterviewQuestion, InterviewAnswer, InterviewFeedback


class InterviewQuestionInline(admin.TabularInline):
    model = InterviewQuestion
    extra = 1


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "interview_type", "student", "status", "is_published", "scheduled_at")
    list_filter = ("interview_type", "status", "company", "is_published", "difficulty")
    search_fields = ("title", "company", "role", "student__user__email")
    inlines = [InterviewQuestionInline]


admin.site.register(InterviewQuestion)
admin.site.register(InterviewAnswer)
admin.site.register(InterviewFeedback)
