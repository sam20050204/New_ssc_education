from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0029_erp_foundation_upgrade"),
    ]

    operations = [
        migrations.AddField(
            model_name="admittedstudent",
            name="batch_end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="admittedstudent",
            name="batch_ended_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ended_batches", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="admittedstudent",
            name="batch_restored_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="restored_batches", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="admittedstudent",
            name="batch_restored_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="admittedstudent",
            name="batch_status",
            field=models.CharField(choices=[("active", "Active"), ("completed", "Completed"), ("archived", "Archived"), ("cancelled", "Cancelled")], db_index=True, default="active", max_length=20),
        ),
        migrations.CreateModel(
            name="BatchActionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("batch_month", models.CharField(db_index=True, max_length=20)),
                ("batch_year", models.CharField(db_index=True, max_length=4)),
                ("action_type", models.CharField(choices=[("ended", "Ended"), ("restored", "Restored"), ("cancelled", "Cancelled"), ("archived", "Archived")], db_index=True, max_length=20)),
                ("action_date", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("affected_students_count", models.PositiveIntegerField(default=0)),
                ("remarks", models.TextField(blank=True, null=True)),
                ("action_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="batch_action_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-action_date"],
            },
        ),
        migrations.AddIndex(
            model_name="admittedstudent",
            index=models.Index(fields=["batch_status"], name="core_admitt_batch_s_b113ac_idx"),
        ),
        migrations.AddIndex(
            model_name="admittedstudent",
            index=models.Index(fields=["batch_month", "batch_year", "batch_status"], name="core_admitt_batch_m_91827a_idx"),
        ),
        migrations.AddIndex(
            model_name="batchactionlog",
            index=models.Index(fields=["batch_month", "batch_year", "action_type"], name="core_batcha_batch_m_e7ea2b_idx"),
        ),
    ]
