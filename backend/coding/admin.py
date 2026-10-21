from django.contrib import admin

from .external import is_external_problem, parse_external_tags, platform_label
from .models import ExternalProblemProgress, Problem, Submission, SubmissionResult, TestCase


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "topic", "source", "is_published", "created_at")
    list_filter = ("difficulty", "is_published")
    search_fields = ("title", "slug", "topic", "description")

    @admin.display(description="Source")
    def source(self, obj):
        if is_external_problem(obj):
            return platform_label(parse_external_tags(obj.tags).get("platform"))
        return "SCOTT"


admin.site.register(TestCase)
admin.site.register(Submission)
admin.site.register(SubmissionResult)
admin.site.register(ExternalProblemProgress)
