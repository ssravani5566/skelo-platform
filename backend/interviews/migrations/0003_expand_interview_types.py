from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("interviews", "0002_interview_practice_fields")]

    operations = [
        migrations.AlterField(
            model_name="interview",
            name="interview_type",
            field=models.CharField(
                choices=[
                    ("TECHNICAL", "Technical"),
                    ("HR", "HR"),
                    ("MIXED", "Full Mock"),
                    ("CODING", "Coding"),
                    ("DSA", "DSA"),
                    ("BEHAVIORAL", "Behavioral"),
                    ("PROJECT", "Project"),
                    ("RESUME_BASED", "Resume Based"),
                    ("COMPANY_SPECIFIC", "Company Specific"),
                    ("SYSTEM_DESIGN", "System Design"),
                ],
                default="TECHNICAL",
                max_length=30,
            ),
        ),
    ]
