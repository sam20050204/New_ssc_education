# Generated migration file - Save as: core/migrations/0006_feepayment.py

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_course_student'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeePayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt_no', models.CharField(editable=False, max_length=20, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('payment_mode', models.CharField(choices=[('Cash', 'Cash'), ('UPI', 'UPI'), ('Card', 'Card'), ('Bank Transfer', 'Bank Transfer')], max_length=20)),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('total_fees_at_payment', models.DecimalField(decimal_places=2, max_digits=10)),
                ('paid_before_this', models.DecimalField(decimal_places=2, max_digits=10)),
                ('remaining_after_this', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fee_payments', to='core.admittedstudent')),
            ],
            options={
                'verbose_name': 'Fee Payment',
                'verbose_name_plural': 'Fee Payments',
                'ordering': ['-payment_date'],
            },
        ),
    ]