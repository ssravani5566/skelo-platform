# Generated for SCOTT Smart Attendance. Adds automated session tracking and policy controls.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("attendance", "0001_initial"),
        ("courses", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AttendancePolicy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("minimum_attendance_percentage", models.DecimalField(decimal_places=2, default=75.0, max_digits=5)),
                ("default_minimum_attendance_minutes", models.PositiveSmallIntegerField(default=15)),
                ("default_late_after_minutes", models.PositiveSmallIntegerField(default=10)),
                ("default_join_window_minutes", models.PositiveSmallIntegerField(default=15)),
                ("heartbeat_credit_cap_seconds", models.PositiveSmallIntegerField(default=75)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Attendance policy", "verbose_name_plural": "Attendance policy"},
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="session_type",
            field=models.CharField(choices=[("CLASS", "Live class"), ("CODING_LAB", "Coding lab"), ("WORKSHOP", "Workshop"), ("MOCK_INTERVIEW", "Mock interview"), ("LEARNING_LAB", "Learning session"), ("OTHER", "Other")], default="CLASS", max_length=24),
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="course",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attendance_sessions", to="courses.course"),
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="batch_label",
            field=models.CharField(blank=True, help_text="Display label only; use department/year/semester to target students.", max_length=100),
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="target_department",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="target_year",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="target_semester",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="minimum_attendance_minutes",
            field=models.PositiveSmallIntegerField(default=15),
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="late_after_minutes",
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="join_window_minutes",
            field=models.PositiveSmallIntegerField(default=15),
        ),
        migrations.AddField(
            model_name="attendance",
            name="joined_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attendance",
            name="last_activity_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attendance",
            name="left_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attendance",
            name="participation_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="attendance",
            name="tracking_paused",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="attendance",
            name="source",
            field=models.CharField(choices=[("AUTOMATIC", "Automatic tracking"), ("ADMIN_REVIEW", "Reviewed correction")], default="AUTOMATIC", max_length=20),
        ),
        migrations.AlterField(
            model_name="attendance",
            name="status",
            field=models.CharField(choices=[("IN_PROGRESS", "In progress"), ("PRESENT", "Present"), ("LATE", "Late"), ("ABSENT", "Absent")], default="ABSENT", max_length=20),
        ),
        migrations.AlterModelOptions(name="trainingsession", options={"ordering": ["session_date", "start_time", "title"]}),
        migrations.AlterModelOptions(name="attendance", options={"ordering": ["-marked_at"]}),
        migrations.CreateModel(
            name="AttendanceEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("JOINED", "Joined session"), ("PAUSED", "Tracking paused while page hidden"), ("RESUMED", "Tracking resumed"), ("LEFT", "Left session"), ("AUTO_FINALIZED", "Automatically finalized"), ("AUTO_ABSENT", "Automatically recorded absent"), ("REVIEWED", "Attendance correction reviewed")], max_length=24)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("attendance", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="attendance.attendance")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
