from django.conf import settings
from django.db import models


class TrainingSession(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="training_sessions")
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.session_date}"


class Attendance(models.Model):
    STATUS_CHOICES = (("PRESENT", "Present"), ("ABSENT", "Absent"), ("LATE", "Late"))
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ABSENT")
    marked_at = models.DateTimeField(auto_now=True)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["session", "student"], name="unique_session_student_attendance")]
