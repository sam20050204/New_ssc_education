# Generated migration for adding 4th and 5th installments

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_alter_admittedstudent_mother_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentfinancedetail',
            name='fourth_installment',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='studentfinancedetail',
            name='fifth_installment',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
    ]
