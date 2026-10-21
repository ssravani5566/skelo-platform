from django.conf import settings
from django.db import models


class Interview(models.Model):
    TYPE_CHOICES = (("TECHNICAL", "Technical"), ("HR", "HR"), ("MIXED", "Mixed"), ("SYSTEM_DESIGN", "System Design"))
    STATUS_CHOICES = (("SCHEDULED", "Scheduled"), ("IN_PROGRESS", "In Progress"), ("COMPLETED", "Completed"), ("CANCELLED", "Cancelled"))
    title = models.CharField(max_length=200)
    interview_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="TECHNICAL")
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="interviews")
    interviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="conducted_interviews")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SCHEDULED")
    role = models.CharField(max_length=150, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.student}"


class InterviewQuestion(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]


class InterviewAnswer(models.Model):
    interview_question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name="answers")
    answer_text = models.TextField(blank=True)
    audio_url = models.URLField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    feedback = models.TextField(blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)


class InterviewFeedback(models.Model):
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name="feedback")
    strengths = models.TextField(blank=True)
    improvement_areas = models.TextField(blank=True)
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    communication_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
