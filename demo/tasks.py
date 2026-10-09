"""Demo Celery tasks. They do nothing: they exist so Celery Beat has real task names to show."""

from celery import shared_task


@shared_task(name="demo.tasks.sync_stock")
def sync_stock(dry_run=False):
    pass


@shared_task(name="demo.tasks.abandoned_carts")
def abandoned_carts(dry_run=False):
    pass


@shared_task(name="demo.tasks.rebuild_index")
def rebuild_index(dry_run=False):
    pass


@shared_task(name="demo.tasks.sales_report")
def sales_report(dry_run=False, recipients=None):
    pass


@shared_task(name="demo.tasks.storefront")
def storefront(dry_run=False):
    pass


@shared_task(name="demo.tasks.launch_campaign")
def launch_campaign(dry_run=False, campaign=None):
    pass


@shared_task(name="demo.tasks.clear_sessions")
def clear_sessions(dry_run=False):
    pass


@shared_task(name="demo.tasks.sync_exchange_rates")
def sync_exchange_rates(dry_run=False, currencies=None):
    pass


@shared_task(name="demo.tasks.send_order_reminders")
def send_order_reminders(dry_run=False):
    pass


@shared_task(name="demo.tasks.archive_tickets")
def archive_tickets(dry_run=False, older_than_days=90):
    pass


@shared_task(name="demo.tasks.backup_database")
def backup_database(dry_run=False):
    pass


@shared_task(name="demo.tasks.ping")
def ping():
    pass
