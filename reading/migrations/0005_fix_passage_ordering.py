# Generated manually to fix passage ordering

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reading', '0004_questiontype_student_range'),
    ]

    operations = [
        # Remove any existing unique constraints first
        migrations.AlterUniqueTogether(
            name='passage',
            unique_together=set(),
        ),
        
        # Add the new unique constraint
        migrations.AlterUniqueTogether(
            name='passage',
            unique_together={('test', 'order')},
        ),
    ]
