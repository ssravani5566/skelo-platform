from django.db import migrations, models


def do_not_seed_admin(apps, schema_editor):
    # Admin accounts must be created through the management command or secure setup flow.
    # Never assign a shared password or elevate a user during schema migration.
    pass

class Migration(migrations.Migration):
    dependencies = [("assessments", "0001_initial"), ("accounts", "0001_initial")]
    operations = [
        migrations.AddField(model_name="question", name="coding_language", field=models.CharField(blank=True, default="PYTHON", max_length=20)),
        migrations.AddField(model_name="question", name="starter_code", field=models.TextField(blank=True)),
        migrations.AddField(model_name="question", name="input_format", field=models.TextField(blank=True)),
        migrations.AddField(model_name="question", name="output_format", field=models.TextField(blank=True)),
        migrations.AddField(model_name="question", name="constraints", field=models.TextField(blank=True)),
        migrations.AddField(model_name="question", name="test_cases", field=models.JSONField(blank=True, default=list)),
        migrations.RunPython(do_not_seed_admin, migrations.RunPython.noop),
    ]
