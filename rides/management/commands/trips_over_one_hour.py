"""Run the bonus reporting SQL: trips longer than one hour, by month and driver.

Prints the report as a table and saves a timestamped JSON copy under ``output/``
(or a custom ``--output-dir``) so the result is easy to share or inspect outside
the terminal.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

SQL_PATH = settings.BASE_DIR / "reports" / "trips_over_one_hour.sql"


class Command(BaseCommand):
    help = "Report the count of trips longer than 1 hour, grouped by month and driver."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Directory for the JSON report (default: <project>/output).",
        )

    def handle(self, *args, **options):
        sql = SQL_PATH.read_text()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        # Human-readable table on stdout.
        self.stdout.write(f"{'Month':<9} {'Driver':<20} Count of Trips > 1 hr")
        for month, driver, count in rows:
            self.stdout.write(f"{month:<9} {driver:<20} {count}")

        # Timestamped JSON copy on disk.
        now = timezone.now()
        output_dir = options["output_dir"]
        output_dir = Path(output_dir) if output_dir else settings.BASE_DIR / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"trips_over_one_hour_{now:%Y-%m-%d_%H%M%S}.json"
        payload = {
            "generated_at": now.isoformat(),
            "count": len(rows),
            "rows": [
                {"month": month, "driver": driver, "trips_over_one_hour": count}
                for month, driver, count in rows
            ],
        }
        path.write_text(json.dumps(payload, indent=2))
        self.stdout.write(self.style.SUCCESS(f"Saved {len(rows)} row(s) to {path}"))
