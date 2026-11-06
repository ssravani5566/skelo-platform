from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("interviews", "0001_initial")]
    operations = [
        migrations.AddField(model_name="interview", name="company", field=models.CharField(blank=True, default="General Placement", max_length=120)),
        migrations.AddField(model_name="interview", name="difficulty", field=models.CharField(choices=[("BEGINNER", "Beginner"), ("INTERMEDIATE", "Intermediate"), ("ADVANCED", "Advanced")], default="INTERMEDIATE", max_length=20)),
        migrations.AddField(model_name="interview", name="duration_minutes", field=models.PositiveIntegerField(default=30)),
        migrations.AddField(model_name="interview", name="interview_mode", field=models.CharField(choices=[("TEXT", "Text"), ("VOICE", "Voice"), ("VIDEO", "Video")], default="TEXT", max_length=10)),
        migrations.AddField(model_name="interview", name="technical_topics", field=models.TextField(blank=True)),
        migrations.AddField(model_name="interview", name="is_published", field=models.BooleanField(default=True)),
    ]
