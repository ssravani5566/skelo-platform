from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("codeathons", "0001_initial")]
    operations = [
        migrations.AddField("codeathon", "event_type", models.CharField(choices=[("CODING", "Coding Competition"), ("HACKATHON", "Hackathon")], default="CODING", max_length=20)),
        migrations.AddField("codeathon", "category", models.CharField(blank=True, max_length=80)),
        migrations.AddField("codeathon", "difficulty", models.CharField(choices=[("EASY", "Easy"), ("MEDIUM", "Medium"), ("HARD", "Hard"), ("ALL", "All levels")], default="ALL", max_length=20)),
        migrations.AddField("codeathon", "participation_type", models.CharField(choices=[("INDIVIDUAL", "Individual"), ("TEAM", "Team")], default="INDIVIDUAL", max_length=20)),
        migrations.AddField("codeathon", "mode", models.CharField(choices=[("ONLINE", "Online"), ("OFFLINE", "Offline"), ("HYBRID", "Hybrid")], default="ONLINE", max_length=20)),
        migrations.AddField("codeathon", "registration_opens_at", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("codeathon", "registration_closes_at", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("codeathon", "venue", models.CharField(blank=True, max_length=250)),
        migrations.AddField("codeathon", "instructions", models.TextField(blank=True)),
        migrations.AddField("codeathon", "prizes", models.TextField(blank=True)),
    ]
