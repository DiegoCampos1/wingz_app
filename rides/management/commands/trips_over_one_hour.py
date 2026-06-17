"""Run the bonus reporting SQL: trips longer than one hour, by month and driver."""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

SQL_PATH = settings.BASE_DIR / "reports" / "trips_over_one_hour.sql"


class Command(BaseCommand):
    help = "Report the count of trips longer than 1 hour, grouped by month and driver."

    def handle(self, *args, **options):
        sql = SQL_PATH.read_text()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        header = ("Month", "Driver", "Count of Trips > 1 hr")
        self.stdout.write(f"{header[0]:<9} {header[1]:<20} {header[2]}")
        for month, driver, count in rows:
            self.stdout.write(f"{month:<9} {driver:<20} {count}")
        self.stdout.write(self.style.SUCCESS(f"({len(rows)} row(s))"))
