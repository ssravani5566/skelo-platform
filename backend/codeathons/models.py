from django.db import models


class Codeathon(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=[("CODING", "Coding Competition"), ("HACKATHON", "Hackathon")], default="CODING")
    category = models.CharField(max_length=80, blank=True)
    difficulty = models.CharField(max_length=20, choices=[("EASY", "Easy"), ("MEDIUM", "Medium"), ("HARD", "Hard"), ("ALL", "All levels")], default="ALL")
    participation_type = models.CharField(max_length=20, choices=[("INDIVIDUAL", "Individual"), ("TEAM", "Team")], default="INDIVIDUAL")
    mode = models.CharField(max_length=20, choices=[("ONLINE", "Online"), ("OFFLINE", "Offline"), ("HYBRID", "Hybrid")], default="ONLINE")
    registration_opens_at = models.DateTimeField(null=True, blank=True)
    registration_closes_at = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=250, blank=True)
    instructions = models.TextField(blank=True)
    prizes = models.TextField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="codeathons_created")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CodeathonProblem(models.Model):
    codeathon = models.ForeignKey(Codeathon, on_delete=models.CASCADE, related_name="problems")
    problem = models.ForeignKey("coding.Problem", on_delete=models.CASCADE, related_name="codeathons")
    order = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField(default=10)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["codeathon", "problem"], name="unique_codeathon_problem")]


class CodeathonParticipant(models.Model):
    codeathon = models.ForeignKey(Codeathon, on_delete=models.CASCADE, related_name="participants")
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="codeathons")
    registered_at = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["codeathon", "student"], name="unique_codeathon_participant")]


class CodeathonSubmission(models.Model):
    participant = models.ForeignKey(CodeathonParticipant, on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey("coding.Problem", on_delete=models.CASCADE, related_name="codeathon_submissions")
    submission = models.ForeignKey("coding.Submission", on_delete=models.SET_NULL, null=True, blank=True, related_name="codeathon_submission")
    points_awarded = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
