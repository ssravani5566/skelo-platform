from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("schedules", "0001_initial")]
    operations = [
        migrations.AlterField(
            model_name="studyplan",
            name="course",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="study_plans", to="courses.course"),
        ),
        migrations.AddField(
            model_name="studyplan",
            name="custom_course_title",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
