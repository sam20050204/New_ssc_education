from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def populate_student_ids(apps, schema_editor):
    AdmittedStudent = apps.get_model("core", "AdmittedStudent")

    for student in AdmittedStudent.objects.order_by("admission_date", "id"):
        if student.student_id:
            continue

        admission_year = (student.admission_date or django.utils.timezone.now().date()).year
        prefix = f"SSC{admission_year}"
        existing = student.student_id or ""
        if existing.startswith(prefix):
            continue

        count = AdmittedStudent.objects.filter(student_id__startswith=prefix).count() + 1
        student.student_id = f"{prefix}{count:05d}"
        student.save(update_fields=["student_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0028_alter_admittedstudent_practical_batch_time_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="admittedstudent",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="admittedstudent",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="admittedstudent",
            name="is_archived",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="admittedstudent",
            name="student_id",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="batch",
            name="is_archived",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="enquiry",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="enquiry",
            name="is_archived",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="enquiry",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(db_index=True, max_length=100)),
                ("object_id", models.CharField(blank=True, max_length=64)),
                ("target_repr", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_logs", to=settings.AUTH_USER_MODEL)),
                ("content_type", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="contenttypes.contenttype")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="LoginAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(db_index=True, max_length=150)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("successful", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="login_attempts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="admittedstudent",
            index=models.Index(fields=["batch_month"], name="core_admitt_batch_m_47f6a7_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["action", "created_at"], name="core_auditl_action_29a2bf_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["content_type", "object_id"], name="core_auditl_content_fec0c4_idx"),
        ),
        migrations.AddIndex(
            model_name="loginattempt",
            index=models.Index(fields=["username", "created_at"], name="core_logina_usernam_06627e_idx"),
        ),
        migrations.AddIndex(
            model_name="loginattempt",
            index=models.Index(fields=["ip_address", "created_at"], name="core_logina_ip_addr_311365_idx"),
        ),
        migrations.RunPython(populate_student_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="admittedstudent",
            name="student_id",
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
