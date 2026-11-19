import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0001_initial"),
        ("students", "0001_initial"),
        ("assessments", "0005_merge_20261028_1442"),
        ("assignments", "0002_assignment_duration_minutes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField("course", "language", models.CharField(blank=True, default="English", max_length=80)),
        migrations.AddField("course", "learning_outcomes", models.TextField(blank=True, help_text="One outcome per line")),
        migrations.AddField("course", "prerequisites", models.TextField(blank=True)),
        migrations.AddField("course", "access_type", models.CharField(choices=[("FREE", "Free"), ("PAID", "Paid")], default="FREE", max_length=10)),
        migrations.AddField("course", "price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField("course", "minimum_quiz_percentage", models.DecimalField(decimal_places=2, default=70, max_digits=5)),
        migrations.AddField("course", "require_assignment_approval", models.BooleanField(default=False)),
        migrations.AddField("course", "is_archived", models.BooleanField(default=False)),
        migrations.AddField("lesson", "video_file", models.FileField(blank=True, upload_to="course_videos/")),
        migrations.AddField("lessonprogress", "last_position_seconds", models.PositiveIntegerField(default=0)),
        migrations.AddField("lessonprogress", "last_accessed_at", models.DateTimeField(auto_now=True, default=django.utils.timezone.now), preserve_default=False),
        migrations.CreateModel(
            name="LearningBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("code", models.CharField(max_length=60, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("students", models.ManyToManyField(blank=True, related_name="learning_batches", to="students.studentprofile")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="LessonResource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("file", models.FileField(upload_to="course_resources/")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resources", to="courses.lesson")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="CourseEnrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("SELF", "Self enrolled"), ("INDIVIDUAL", "Assigned individually"), ("BATCH", "Assigned through batch")], default="SELF", max_length=20)),
                ("access_expires_at", models.DateTimeField(blank=True, null=True)),
                ("enrolled_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="courses.course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_enrollments", to="students.studentprofile")),
                ("assigned_batch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="course_enrollments", to="courses.learningbatch")),
            ],
            options={"ordering": ["-enrolled_at"]},
        ),
        migrations.CreateModel(
            name="CourseBatchAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("access_expires_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_assignments", to="courses.learningbatch")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batch_assignments", to="courses.course")),
            ],
        ),
        migrations.CreateModel(
            name="CourseModuleAssessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("assessment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_module_links", to="assessments.assessment")),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assessment_links", to="courses.coursemodule")),
            ],
        ),
        migrations.CreateModel(
            name="CourseModuleAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_module_links", to="assignments.assignment")),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignment_links", to="courses.coursemodule")),
            ],
        ),
        migrations.AlterModelOptions(name="coursemodule", options={"ordering": ["order", "id"]}),
        migrations.AlterModelOptions(name="lesson", options={"ordering": ["order", "id"]}),
        migrations.AddConstraint(
            model_name="courseenrollment",
            constraint=models.UniqueConstraint(fields=("student", "course"), name="unique_student_course_enrollment"),
        ),
        migrations.AddConstraint(
            model_name="coursebatchassignment",
            constraint=models.UniqueConstraint(fields=("course", "batch"), name="unique_course_batch_assignment"),
        ),
        migrations.AddConstraint(
            model_name="coursemoduleassessment",
            constraint=models.UniqueConstraint(fields=("module", "assessment"), name="unique_module_assessment_link"),
        ),
        migrations.AddConstraint(
            model_name="coursemoduleassignment",
            constraint=models.UniqueConstraint(fields=("module", "assignment"), name="unique_module_assignment_link"),
        ),
    ]
