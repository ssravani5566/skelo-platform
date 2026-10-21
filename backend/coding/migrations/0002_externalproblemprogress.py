from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("coding", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ExternalProblemProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("solved_at", models.DateTimeField(auto_now_add=True)),
                ("problem", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="external_progress", to="coding.problem")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="external_problem_progress", to="students.studentprofile")),
            ],
            options={"ordering": ["-solved_at"]},
        ),
        migrations.AddConstraint(
            model_name="externalproblemprogress",
            constraint=models.UniqueConstraint(fields=("student", "problem"), name="unique_external_problem_progress"),
        ),
    ]
