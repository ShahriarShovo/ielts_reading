# Generated manually for adding paragraph fields to Passage model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reading', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='passage',
            name='has_paragraphs',
            field=models.BooleanField(default=False, help_text='Whether this passage has paragraph structure for matching questions'),
        ),
        migrations.AddField(
            model_name='passage',
            name='paragraph_count',
            field=models.PositiveIntegerField(blank=True, help_text='Number of paragraphs (e.g., 7 for A-G)', null=True),
        ),
        migrations.AddField(
            model_name='passage',
            name='paragraph_labels',
            field=models.CharField(blank=True, help_text="Paragraph labels (e.g., 'A-G' or '1-7')", max_length=50),
        ),
        migrations.AddField(
            model_name='passage',
            name='organization_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='passage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='passage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, blank=True, null=True),
        ),
    ]
