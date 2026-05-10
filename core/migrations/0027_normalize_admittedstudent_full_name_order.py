from django.db import migrations


def normalize_full_names(apps, schema_editor):
    AdmittedStudent = apps.get_model("core", "AdmittedStudent")

    for student in AdmittedStudent.objects.all().iterator():
        parts = [student.surname, student.student_name, student.father_name]
        full_name = " ".join(part.strip() for part in parts if part and part.strip())
        if student.full_name != full_name:
            student.full_name = full_name
            student.save(update_fields=["full_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0026_studentfinancedetail_fees_paid_to_mkcl_3_and_more"),
    ]

    operations = [
        migrations.RunPython(normalize_full_names, migrations.RunPython.noop),
    ]
