# Save as: core/migrations/0010_add_batch_fields.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_enquiry_custom_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='admittedstudent',
            name='batch_month',
            field=models.CharField(
                max_length=20, 
                blank=True, 
                null=True,
                help_text="Month of batch (e.g., January, February)"
            ),
        ),
        migrations.AddField(
            model_name='admittedstudent',
            name='batch_year',
            field=models.CharField(
                max_length=4, 
                blank=True, 
                null=True,
                help_text="Year of batch (e.g., 2024, 2025)"
            ),
        ),
    ]


# After creating this file, run:
# python manage.py makemigrations
# python manage.py migrate