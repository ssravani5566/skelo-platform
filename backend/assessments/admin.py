from django.contrib import admin
from .models import Assessment, Question, AssessmentQuestion, StudentAssessment, StudentAnswer

admin.site.register(Assessment)
admin.site.register(Question)
admin.site.register(AssessmentQuestion)
admin.site.register(StudentAssessment)
admin.site.register(StudentAnswer)
