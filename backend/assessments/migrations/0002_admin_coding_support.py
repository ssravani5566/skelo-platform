from django.db import migrations, models
from django.contrib.auth.hashers import make_password


def seed_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    user = User.objects.filter(username="Admin").first() or User.objects.filter(email__iexact="admin@scott.local").first()
    if user is None:
        user = User(username="Admin", email="admin@scott.local")
    user.role = "ADMIN"
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.is_email_verified = True
    user.password = make_password("Admin@1234")
    user.save()

class Migration(migrations.Migration):
    dependencies = [("assessments", "0001_initial"), ("accounts", "0001_initial")]
    operations = [
        migrations.AddField(model_name="question", name="coding_language", field=models.CharField(blank=True, default="PYTHON", max_length=20)),
        migrations.AddField(model_name="question", name="starter_code", field=models.TextField(blank=True)),
        migrations.AddField(model_name="question", name="input_format", field=models.TextField(blank=True)),
        migrations.AddField(model_name="question", name="output_format", field=models.TextField(blank=True)),
        migrations.AddField(model_name="question", name="constraints", field=models.TextField(blank=True)),
        migrations.AddField(model_name="question", name="test_cases", field=models.JSONField(blank=True, default=list)),
        migrations.RunPython(seed_admin, migrations.RunPython.noop),
    ]
