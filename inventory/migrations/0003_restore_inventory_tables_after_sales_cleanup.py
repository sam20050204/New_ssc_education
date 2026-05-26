from django.db import migrations


def restore_inventory_tables(apps, schema_editor):
    existing_tables = set(schema_editor.connection.introspection.table_names())
    model_order = [
        ("inventory", "Category"),
        ("inventory", "Supplier"),
        ("inventory", "Item"),
        ("inventory", "Purchase"),
        ("inventory", "Inventory"),
        ("inventory", "StockMovement"),
        ("inventory", "LowStockAlert"),
    ]

    for app_label, model_name in model_order:
        model = apps.get_model(app_label, model_name)
        if model._meta.db_table not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(model._meta.db_table)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0038_remove_sales_and_inventory"),
        ("inventory", "0002_rename_inventory_c_is_acti_idx_inventory_c_is_acti_734468_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(restore_inventory_tables, migrations.RunPython.noop),
    ]
