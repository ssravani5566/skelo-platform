import secrets
from django.db import transaction
from .models import StudentProfile


def generate_register_number():
    while True:
        candidate = f"STU{secrets.randbelow(900000) + 100000}"
        if not StudentProfile.objects.filter(register_number=candidate).exists():
            return candidate


@transaction.atomic
def create_student_profile(user):
    if user.role != "STUDENT":
        return getattr(user, "student_profile", None)
    profile, _ = StudentProfile.objects.get_or_create(
        user=user,
        defaults={"register_number": generate_register_number()},
    )
    return profile


def get_student_profile(user):
    return create_student_profile(user)
