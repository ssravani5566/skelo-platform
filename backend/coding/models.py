from django.conf import settings
from django.db import models


class Problem(models.Model):
    DIFFICULTY_CHOICES = (("EASY", "Easy"), ("MEDIUM", "Medium"), ("HARD", "Hard"))
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    input_format = models.TextField(blank=True)
    output_format = models.TextField(blank=True)
    constraints = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="EASY")
    topic = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    points = models.PositiveIntegerField(default=10)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ExternalProblemProgress(models.Model):
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="external_problem_progress")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="external_progress")
    solved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "problem"], name="unique_external_problem_progress"),
        ]
        ordering = ["-solved_at"]

    def __str__(self):
        return f"{self.student} - {self.problem}"


class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="test_cases")
    input_data = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.problem.title} - Test {self.order}"


class Submission(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("WRONG_ANSWER", "Wrong Answer"),
        ("COMPILE_ERROR", "Compile Error"),
        ("RUNTIME_ERROR", "Runtime Error"),
        ("TIME_LIMIT", "Time Limit Exceeded"),
        ("MEMORY_LIMIT", "Memory Limit Exceeded"),
        ("ERROR", "Error"),
    )
    LANGUAGE_CHOICES = (("PYTHON", "Python"), ("JAVA", "Java"), ("CPP", "C++"), ("C", "C"), ("JAVASCRIPT", "JavaScript"))

    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="submissions")
    language = models.CharField(choices=LANGUAGE_CHOICES, max_length=20)
    source_code = models.TextField()
    status = models.CharField(choices=STATUS_CHOICES, default="PENDING", max_length=30)
    runtime_ms = models.PositiveIntegerField(default=0)
    memory_kb = models.PositiveIntegerField(default=0)
    passed_test_cases = models.PositiveIntegerField(default=0)
    total_test_cases = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student} - {self.problem} - {self.status}"


class SubmissionResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="results")
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name="submission_results")
    passed = models.BooleanField(default=False)
    actual_output = models.TextField(blank=True)
    runtime_ms = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.submission_id} - test {self.test_case.order}"
