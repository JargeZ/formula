from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from demo.seed.catalog import seed_catalog
from demo.seed.sales import seed_sales
from demo.seed.support import seed_support
from demo.seed.system import (
    DEMO_PASSWORD,
    DEMO_USERNAME,
    seed_constance,
    seed_periodic_tasks,
    seed_site,
    seed_users,
    seed_waffle,
)

FIXTURES = sorted((Path(settings.BASE_DIR) / "formula" / "fixtures").glob("*.json"))


class Command(BaseCommand):
    help = "Delete all data and fill the database with realistic demo data."

    def handle(self, *args, **options):
        call_command("flush", interactive=False, verbosity=0)

        with transaction.atomic():
            call_command("loaddata", *FIXTURES, verbosity=0)
            staff = seed_users()
            products = seed_catalog()
            _, orders = seed_sales(products)
            seed_support(orders, staff)
            seed_site()
            seed_waffle()
            seed_periodic_tasks()

        seed_constance()

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready. Login: {DEMO_USERNAME} / {DEMO_PASSWORD}"
            )
        )
