from django.conf import settings
from django.db import models
from django.utils import timezone


class Course(models.Model):
    LEVEL_CHOICES = (("BEGINNER", "Beginner"), ("INTERMEDIATE", "Intermediate"), ("ADVANCED", "Advanced"))
    ACCESS_CHOICES = (("FREE", "Free"), ("PAID", "Paid"))

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="BEGINNER")
    language = models.CharField(max_length=80, default="English", blank=True)
    learning_outcomes = models.TextField(blank=True, help_text="One outcome per line")
    prerequisites = models.TextField(blank=True)
    access_type = models.CharField(max_length=10, choices=ACCESS_CHOICES, default="FREE")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_quiz_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=70)
    require_assignment_approval = models.BooleanField(default=False)
    thumbnail = models.ImageField(upload_to="courses/", blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_courses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        constraints = [models.UniqueConstraint(fields=["course", "order"], name="unique_course_module_order")]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to="course_videos/", blank=True, null=True)
    resource_file = models.FileField(upload_to="course_resources/", blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class LessonResource(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=180)
    file = models.FileField(upload_to="course_resources/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title


class LearningBatch(models.Model):
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True)
    students = models.ManyToManyField("students.StudentProfile", blank=True, related_name="learning_batches")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class CourseBatchAssignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="batch_assignments")
    batch = models.ForeignKey(LearningBatch, on_delete=models.CASCADE, related_name="course_assignments")
    access_expires_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["course", "batch"], name="unique_course_batch_assignment")]

    @property
    def is_active(self):
        return not self.access_expires_at or self.access_expires_at > timezone.now()


class CourseEnrollment(models.Model):
    SOURCE_CHOICES = (("SELF", "Self enrolled"), ("INDIVIDUAL", "Assigned individually"), ("BATCH", "Assigned through batch"))
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="course_enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="SELF")
    assigned_batch = models.ForeignKey(LearningBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="course_enrollments")
    access_expires_at = models.DateTimeField(null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="unique_student_course_enrollment")]
        ordering = ["-enrolled_at"]

    @property
    def is_active(self):
        return not self.access_expires_at or self.access_expires_at > timezone.now()


class CourseModuleAssessment(models.Model):
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name="assessment_links")
    assessment = models.ForeignKey("assessments.Assessment", on_delete=models.CASCADE, related_name="course_module_links")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["module", "assessment"], name="unique_module_assessment_link")]


class CourseModuleAssignment(models.Model):
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name="assignment_links")
    assignment = models.ForeignKey("assignments.Assignment", on_delete=models.CASCADE, related_name="course_module_links")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["module", "assignment"], name="unique_module_assignment_link")]


class CourseProgress(models.Model):
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="course_progress")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="student_progress")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="unique_student_course_progress")]

    def __str__(self):
        return f"{self.student} - {self.course}"


class LessonProgress(models.Model):
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="student_progress")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_position_seconds = models.PositiveIntegerField(default=0)
    last_accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "lesson"], name="unique_student_lesson_progress")]
