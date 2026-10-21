from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = (("ASSESSMENT", "Assessment"), ("ASSIGNMENT", "Assignment"), ("COURSE", "Course"), ("INTERVIEW", "Interview"), ("ATTENDANCE", "Attendance"), ("SYSTEM", "System"), ("OTHER", "Other"))
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="SYSTEM")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
