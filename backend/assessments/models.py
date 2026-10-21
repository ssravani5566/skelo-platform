from django.conf import settings
from django.db import models


class Assessment(models.Model):
    TYPE_CHOICES = (
        ("MCQ", "MCQ"),
        ("APTITUDE", "Aptitude"),
        ("TECHNICAL", "Technical"),
        ("LSRW", "LSRW"),
        ("CODING", "Coding"),
        ("COMPANY", "Company Specific"),
        ("MIXED", "Mixed"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assessment_type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default="TECHNICAL"
    )
    duration_minutes = models.PositiveIntegerField(default=30)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)

    # If this list is empty, the assessment is available to all students.
    # If students are selected, only those students can see/start it.
    assigned_students = models.ManyToManyField(
        "students.StudentProfile",
        blank=True,
        related_name="assigned_assessments",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_assessments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = (
        ("MCQ", "MCQ"),
        ("TRUE_FALSE", "True/False"),
        ("SHORT", "Short Answer"),
        ("CODING", "Coding"),
    )

    text = models.TextField()
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPES, default="MCQ"
    )
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    correct_answer = models.CharField(max_length=500, blank=True)
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=30, blank=True, default="")
    marks = models.PositiveIntegerField(default=1)
    coding_language = models.CharField(max_length=20, default="PYTHON", blank=True)
    starter_code = models.TextField(blank=True)
    input_format = models.TextField(blank=True)
    output_format = models.TextField(blank=True)
    constraints = models.TextField(blank=True)
    test_cases = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.text[:80]


class AssessmentQuestion(models.Model):
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="assessment_questions"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="assessment_questions"
    )
    order = models.PositiveIntegerField(default=1)
    marks = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "question"],
                name="unique_assessment_question",
            )
        ]


class StudentAssessment(models.Model):
    STATUS_CHOICES = (
        ("NOT_STARTED", "Not Started"),
        ("IN_PROGRESS", "In Progress"),
        ("SUBMITTED", "Submitted"),
        ("EVALUATED", "Evaluated"),
    )

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="assessment_attempts",
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="student_attempts",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="NOT_STARTED"
    )
    score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "assessment"],
                name="unique_student_assessment",
            )
        ]


class StudentAnswer(models.Model):
    student_assessment = models.ForeignKey(
        StudentAssessment,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="student_answers",
    )
    answer_text = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    marks_awarded = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student_assessment", "question"],
                name="unique_student_assessment_answer",
            )
        ]
