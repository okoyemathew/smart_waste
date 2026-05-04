from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Audit database tables and highlight legacy tables not managed by Django models."

    def handle(self, *args, **options):
        django_tables = set(connection.introspection.django_table_names(only_existing=True))
        django_tables.add("django_migrations")
        all_tables = set(connection.introspection.table_names())
        legacy_tables = sorted(all_tables - django_tables)

        self.stdout.write(self.style.SUCCESS("Django-managed tables:"))
        for table in sorted(django_tables):
            self.stdout.write(f"  - {table}")

        self.stdout.write("")
        if legacy_tables:
            self.stdout.write(self.style.WARNING("Legacy/unmanaged tables (review before dropping):"))
            for table in legacy_tables:
                self.stdout.write(f"  - {table}")
        else:
            self.stdout.write(self.style.SUCCESS("No legacy/unmanaged tables found."))

        self.stdout.write("")
        self.stdout.write("Next safe step: back up these unmanaged tables before any cleanup.")
