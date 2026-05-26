from django.db import migrations


def purge_sales_content_types(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.filter(
        app_label="core",
        model__in=[
            "salesitem",
            "salesreceipt",
            "salesreceiptline",
            "dailysalesentry",
            "dailysalesline",
        ],
    ).delete()
    ContentType.objects.filter(app_label="inventory").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0037_sales_bugfixes_and_audit_fields"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP TABLE IF EXISTS core_dailysalesline;",
                "DROP TABLE IF EXISTS core_dailysalesentry;",
                "DROP TABLE IF EXISTS core_salesreceiptline;",
                "DROP TABLE IF EXISTS core_salesreceipt;",
                "DROP TABLE IF EXISTS core_salesitem;",
                "DROP TABLE IF EXISTS inventory_lowstockalert;",
                "DROP TABLE IF EXISTS inventory_stockmovement;",
                "DROP TABLE IF EXISTS inventory_inventory;",
                "DROP TABLE IF EXISTS inventory_purchase;",
                "DROP TABLE IF EXISTS inventory_item;",
                "DROP TABLE IF EXISTS inventory_supplier;",
                "DROP TABLE IF EXISTS inventory_category;",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunPython(purge_sales_content_types, migrations.RunPython.noop),
    ]
