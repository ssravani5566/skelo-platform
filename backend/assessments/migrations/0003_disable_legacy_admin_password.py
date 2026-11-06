from django.db import migrations
from django.contrib.auth.hashers import check_password


def disable_known_legacy_password(apps, schema_editor):
    """Invalidate the published development password if an old DB still has it."""
    User = apps.get_model("accounts", "User")
    candidates = User.objects.filter(username__iexact="Admin") | User.objects.filter(email__iexact="admin@scott.local")
    for user in candidates.distinct():
        if user.password and check_password("Admin@1234", user.password):
            user.password = "!"
            user.save(update_fields=["password"])


class Migration(migrations.Migration):
    dependencies = [("assessments", "0002_admin_coding_support")]
    operations = [migrations.RunPython(disable_known_legacy_password, migrations.RunPython.noop)]
