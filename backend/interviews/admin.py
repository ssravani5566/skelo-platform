from django.contrib import admin
from .models import Interview, InterviewQuestion, InterviewAnswer, InterviewFeedback

admin.site.register(Interview)
admin.site.register(InterviewQuestion)
admin.site.register(InterviewAnswer)
admin.site.register(InterviewFeedback)
