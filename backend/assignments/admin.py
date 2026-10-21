from django.contrib import admin
from .models import Assignment, AssignmentSubmission, AssignmentEvaluation

admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(AssignmentEvaluation)
