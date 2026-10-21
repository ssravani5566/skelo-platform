from django.conf import settings
from django.db import models


class Assignment(models.Model):
    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("PUBLISHED", "Published"),
        ("CLOSED", "Closed"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True)

    # Time allowed / expected working time for the assignment.
    duration_minutes = models.PositiveIntegerField(default=60)

    # Final submission deadline.
    due_date = models.DateTimeField()

    # Maximum marks the faculty/admin can award.
    max_marks = models.PositiveIntegerField(default=100)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    # Optional question/reference file supplied by admin.
    attachment = models.FileField(
        upload_to="assignments/",
        blank=True,
        null=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    STATUS_CHOICES = (
        ("SUBMITTED", "Submitted"),
        ("EVALUATED", "Evaluated"),
        ("LATE", "Late"),
    )

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )

    # Optional text explanation/answer.
    answer_text = models.TextField(blank=True)

    # One submission file. This accepts Word documents, PDFs, images,
    # spreadsheets, ZIP files, etc. Django does not restrict the extension.
    submitted_file = models.FileField(
        upload_to="assignment_submissions/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUBMITTED",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"],
                name="unique_assignment_student_submission",
            )
        ]


class AssignmentEvaluation(models.Model):
    submission = models.OneToOneField(
        AssignmentSubmission,
        on_delete=models.CASCADE,
        related_name="evaluation",
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assignment_evaluations",
    )
    marks = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0,
    )
    feedback = models.TextField(blank=True)
    evaluated_at = models.DateTimeField(auto_now_add=True)
