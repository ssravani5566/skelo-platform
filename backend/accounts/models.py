from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_STUDENT = "STUDENT"
    ROLE_FACULTY = "FACULTY"
    ROLE_ADMIN = "ADMIN"

    ROLE_CHOICES = (
        (ROLE_STUDENT, "Student"),
        (ROLE_FACULTY, "Faculty"),
        (ROLE_ADMIN, "Admin"),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone = models.CharField(max_length=20, blank=True)
    is_email_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
