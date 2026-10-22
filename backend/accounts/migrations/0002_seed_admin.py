import os
from django.contrib.auth.hashers import make_password
from django.db import migrations


def seed_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    password = os.environ["INITIAL_ADMIN_PASSWORD"]

    user = User.objects.filter(username="Admin").first()

    if user is None:
        user = User(
            username="Admin",
            email="admin@scott.local",
        )
        user.password = make_password(password)

    user.role = "ADMIN"
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.is_email_verified = True
    user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_admin,
            migrations.RunPython.noop,
        ),
    ]