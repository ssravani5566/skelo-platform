from django.conf import settings
from django.db import models

class StudyPlan(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_plans')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='study_plans', null=True, blank=True)
    custom_course_title = models.CharField(max_length=200, blank=True)
    goal = models.CharField(max_length=240, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=1, default=1)
    preferred_days = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, default='ACTIVE', choices=(('ACTIVE','Active'),('COMPLETED','Completed'),('PAUSED','Paused')))
    last_reminded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class StudyTask(models.Model):
    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='tasks')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    scheduled_date = models.DateField()
    duration_minutes = models.PositiveIntegerField(default=45)
    order = models.PositiveIntegerField(default=1)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

class StudyCheck(models.Model):
    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='checks')
    offered_at = models.DateTimeField(auto_now_add=True)
    response = models.CharField(max_length=12, choices=(('PENDING','Pending'),('WILLING','Willing'),('LATER','Later')), default='PENDING')
    score = models.PositiveSmallIntegerField(null=True, blank=True)
