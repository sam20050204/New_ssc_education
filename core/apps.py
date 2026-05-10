from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.dispatch import receiver


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """Enable FOREIGN_KEYS for SQLite when Django is ready"""

        # Enable FOREIGN_KEYS for SQLite
        @receiver(connection_created)
        def enable_sqlite_foreign_keys(sender, connection, **kwargs):
            """Enable FOREIGN_KEY constraints for SQLite"""
            if connection.settings_dict["ENGINE"] == "django.db.backends.sqlite3":
                cursor = connection.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
