from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assignments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="duration_minutes",
            field=models.PositiveIntegerField(default=60),
        ),
    ]
