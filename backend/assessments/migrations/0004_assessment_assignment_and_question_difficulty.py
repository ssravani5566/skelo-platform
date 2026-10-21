from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0003_alter_assessment_assessment_type"),
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="difficulty",
            field=models.CharField(
                blank=True,
                default="",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="assessment",
            name="assigned_students",
            field=models.ManyToManyField(
                blank=True,
                related_name="assigned_assessments",
                to="students.studentprofile",
            ),
        ),
    ]
