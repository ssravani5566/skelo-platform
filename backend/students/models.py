from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    register_number = models.CharField(max_length=50, unique=True)
    college = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=100, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    semester = models.PositiveSmallIntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    resume = models.FileField(upload_to="resumes/", blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - {self.register_number}"


class FacultyProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="faculty_profile")
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - {self.employee_id}"


class Skill(models.Model):
    CATEGORY_CHOICES = (
        ("TECHNICAL", "Technical"),
        ("COMMUNICATION", "Communication"),
        ("APTITUDE", "Aptitude"),
        ("INTERVIEW", "Interview"),
        ("SYSTEM_DESIGN", "System Design"),
        ("OTHER", "Other"),
    )

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="TECHNICAL")
    description = models.TextField(blank=True)
    target_score = models.PositiveSmallIntegerField(default=100)

    def __str__(self):
        return self.name


class StudentSkill(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="student_skills")
    current_score = models.PositiveSmallIntegerField(default=0)
    target_score = models.PositiveSmallIntegerField(default=100)
    practice_count = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "skill"], name="unique_student_skill")]

    def __str__(self):
        return f"{self.student} - {self.skill}"
