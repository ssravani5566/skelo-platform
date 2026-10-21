from django.db import migrations, models
import django.db.models.constraints
from django.db.models import Q

class Migration(migrations.Migration):
    dependencies=[("gamification","0001_initial")]
    operations=[
        migrations.AddField(model_name="xptransaction",name="source_key",field=models.CharField(blank=True,max_length=150)),
        migrations.AddConstraint(model_name="xptransaction",constraint=models.UniqueConstraint(condition=~Q(source_key=""),fields=("student","source_key"),name="unique_student_xp_source")),
    ]
