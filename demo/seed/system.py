import json
from datetime import date, datetime, time, timedelta

from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.utils import timezone
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)
from waffle.models import Flag, Sample, Switch

from utils.seed import paragraphs, past, rng

DEMO_USERNAME = "demo"
# Matches the prefilled login form when LOGIN_PASSWORD is set (fly demo)
DEMO_PASSWORD = settings.LOGIN_PASSWORD or "unfold123"

# group -> app models it can change
GROUPS = {
    "Sales": ["order", "orderitem", "customer"],
    "Catalog managers": ["product", "category", "tag", "tagrelation"],
    "Support": ["ticket", "customer"],
}

# username, first, last, location, group
STAFF = [
    ("anna.kovac", "Anna", "Kovač", "Bratislava, Slovakia", "Support"),
    ("lukas.weber", "Lukas", "Weber", "Berlin, Germany", "Support"),
    ("marie.dubois", "Marie", "Dubois", "Lyon, France", "Sales"),
    ("tomas.novak", "Tomáš", "Novák", "Prague, Czechia", "Catalog managers"),
    ("sara.rossi", "Sara", "Rossi", "Milan, Italy", "Sales"),
    ("james.walker", "James", "Walker", "London, United Kingdom", None),
]


def seed_users():
    """Demo superuser plus a small staff team. Returns the staff users."""
    User = get_user_model()

    groups = {}
    for name, models in GROUPS.items():
        group = Group.objects.create(name=name)
        group.permissions.set(
            Permission.objects.filter(
                content_type__app_label="demo", content_type__model__in=models
            )
        )
        groups[name] = group

    demo, _ = User.objects.get_or_create(
        username=DEMO_USERNAME, defaults={"email": "demo@example.com"}
    )
    demo.set_password(DEMO_PASSWORD)
    demo.is_staff = demo.is_superuser = demo.is_active = True
    demo.first_name, demo.last_name = "Demo", "Admin"
    demo.location = "Bratislava, Slovakia"
    demo.biography = paragraphs("Administrator account of the demo project.")
    demo.save()

    staff = []
    for username, first, last, location, group in STAFF:
        user = User.objects.create_user(
            username=username,
            password=DEMO_PASSWORD,
            email=f"{username}@example.com",
            first_name=first,
            last_name=last,
            location=location,
            biography=paragraphs(f"{first} works in the {group or 'IT'} team."),
            is_staff=True,
            is_active=username != "james.walker",
            last_login=past(14),
        )
        if group:
            user.groups.add(groups[group])
        staff.append(user)

    return staff


def seed_site():
    Site.objects.update_or_create(
        pk=1, defaults={"domain": "demo.example.com", "name": "Unfold Demo"}
    )


def seed_constance():
    values = {
        "SITE_NAME": "Unfold Demo Store",
        "SITE_DESCRIPTION": "Electronics and accessories delivered across Europe.",
        "SITE_URL": "https://demo.example.com",
        "THEME": "light-blue",
        "SITE_FONT_SIZE": 16,
        "SITE_BACKGROUND_COLOR": "#F8FAFC",
        "SITE_ANALYTICS_ID": "G-DEMO12345",
        "SITE_MAINTENANCE_MESSAGE": "We are upgrading the store. Back in 30 minutes.",
        "SITE_SOCIAL_LINKS": "https://x.com/example, https://linkedin.com/company/example",
        "SITE_FOOTER_TEXT": "© Unfold Demo Store. All rights reserved.",
        "SITE_META_KEYWORDS": "electronics, laptops, audio, smart home",
        "SITE_CACHE_TTL": 900,
        "SITE_DATE_FORMAT": "%d.%m.%Y",
        "SITE_TIME_ZONE": "Europe/Bratislava",
        "SITE_DATE": date(2026, 3, 1),
        "SITE_DATETIME": datetime(
            2026, 3, 1, 9, 0, tzinfo=timezone.get_current_timezone()
        ),
        "SITE_TIME": time(7, 30),
    }
    for key, value in values.items():
        setattr(config, key, value)


def seed_waffle():
    User = get_user_model()
    # name, note, options, groups, usernames
    flags = [
        ("new_checkout", "New one page checkout", {"percent": 25, "rollout": True}, [], []),
        ("product_reviews", "Show reviews on product pages", {"everyone": True}, [], []),
        ("ai_recommendations", "Recommendations block on cart page", {"superusers": True}, [], []),
        ("dark_mode_emails", "Dark mode for transactional emails", {"everyone": False}, [], []),
        ("beta_dashboard", "Beta analytics dashboard", {"staff": True}, [], []),
        ("wishlist", "Wishlist for logged in customers", {"authenticated": True}, [], []),
        ("german_storefront", "Localized storefront", {"languages": "de,de-at,de-ch"}, [], []),
        ("bulk_order_edit", "Edit many orders at once", {}, ["Sales"], []),
        ("catalog_ai_descriptions", "Generate product descriptions", {}, ["Catalog managers"], ["tomas.novak"]),
        ("support_macros", "Canned replies in tickets", {"testing": True}, ["Support"], ["anna.kovac"]),
        ("live_chat", "Live chat widget", {"percent": 5, "testing": True}, [], ["lukas.weber"]),
        ("gift_cards", "Gift card checkout", {"percent": 0}, [], []),
    ]
    for name, note, options, groups, usernames in flags:
        flag = Flag.objects.create(name=name, note=note, **options)
        flag.groups.set(Group.objects.filter(name__in=groups))
        flag.users.set(User.objects.filter(username__in=usernames))

    for name, note, active in [
        ("maintenance_banner", "Show maintenance banner", False),
        ("free_shipping", "Free shipping over €50", True),
        ("newsletter_popup", "Newsletter signup popup", True),
        ("legacy_api", "Keep v1 API endpoints", False),
        ("cookie_consent_v2", "New cookie consent dialog", True),
        ("paypal_checkout", "Allow PayPal at checkout", True),
        ("read_only_mode", "Stop all writes during migrations", False),
        ("holiday_theme", "Seasonal storefront theme", False),
    ]:
        Switch.objects.create(name=name, note=note, active=active)

    for name, note, percent in [
        ("search_v2", "Route traffic to new search", 30),
        ("image_cdn", "Serve images from the new CDN", 75),
        ("new_pricing_engine", "Shadow traffic for new pricing", 10),
        ("recommendations_cache", "Cache recommendation results", 50),
        ("full_rollout_check", "Sample always on", 100),
        ("disabled_experiment", "Sample always off", 0),
    ]:
        Sample.objects.create(name=name, note=note, percent=percent)


def seed_periodic_tasks():
    every_30_sec = IntervalSchedule.objects.create(
        every=30, period=IntervalSchedule.SECONDS
    )
    every_5_min = IntervalSchedule.objects.create(
        every=5, period=IntervalSchedule.MINUTES
    )
    every_hour = IntervalSchedule.objects.create(every=1, period=IntervalSchedule.HOURS)
    every_day = IntervalSchedule.objects.create(every=1, period=IntervalSchedule.DAYS)

    def cron(minute="*", hour="*", day_of_week="*", day_of_month="*", month_of_year="*", tz="UTC"):
        return CrontabSchedule.objects.create(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            timezone=tz,
        )

    every_15_min = cron(minute="*/15")
    hourly = cron(minute="5")
    nightly = cron(minute="0", hour="2", tz="Europe/Bratislava")
    workdays = cron(minute="0", hour="9", day_of_week="1-5", tz="Europe/Berlin")
    weekly = cron(minute="30", hour="6", day_of_week="1")
    monthly = cron(minute="0", hour="3", day_of_month="1")
    quarterly = cron(minute="0", hour="4", day_of_month="1", month_of_year="1,4,7,10")
    business_hours = cron(minute="0,30", hour="8-18", day_of_week="mon-fri", tz="Europe/London")

    sunrise = SolarSchedule.objects.create(
        event="sunrise", latitude=48.1486, longitude=17.1077
    )
    sunset = SolarSchedule.objects.create(
        event="sunset", latitude=52.5200, longitude=13.4050
    )
    launch = ClockedSchedule.objects.create(
        clocked_time=timezone.now() + timedelta(days=7)
    )
    past_launch = ClockedSchedule.objects.create(
        clocked_time=timezone.now() - timedelta(days=30)
    )

    # name, task, schedule and extra fields
    tasks = [
        ("Health check ping", "demo.tasks.ping", {"interval": every_30_sec, "kwargs": "{}"}),
        ("Sync stock levels", "demo.tasks.sync_stock", {"interval": every_5_min}),
        ("Send abandoned cart emails", "demo.tasks.abandoned_carts", {"interval": every_hour, "queue": "emails"}),
        ("Daily database backup", "demo.tasks.backup_database", {"interval": every_day, "priority": 9}),
        ("Sync exchange rates", "demo.tasks.sync_exchange_rates", {"crontab": every_15_min, "kwargs": json.dumps({"dry_run": False, "currencies": ["EUR", "USD", "CZK"]})}),
        ("Hourly order reminders", "demo.tasks.send_order_reminders", {"crontab": hourly, "queue": "emails"}),
        ("Rebuild search index", "demo.tasks.rebuild_index", {"crontab": nightly}),
        ("Morning sales report", "demo.tasks.sales_report", {"crontab": workdays, "kwargs": json.dumps({"dry_run": False, "recipients": ["sales@example.com"]})}),
        ("Weekly sales report", "demo.tasks.sales_report", {"crontab": weekly, "args": json.dumps([True])}),
        ("Archive old tickets", "demo.tasks.archive_tickets", {"crontab": monthly, "kwargs": json.dumps({"older_than_days": 180})}),
        ("Quarterly report", "demo.tasks.sales_report", {"crontab": quarterly, "description": "Board report at the start of each quarter."}),
        ("Business hours stock sync", "demo.tasks.sync_stock", {"crontab": business_hours, "expire_seconds": 600}),
        ("Turn on storefront lights", "demo.tasks.storefront", {"solar": sunrise}),
        ("Turn off storefront lights", "demo.tasks.storefront", {"solar": sunset, "enabled": False}),
        ("Spring sale launch", "demo.tasks.launch_campaign", {"clocked": launch, "one_off": True, "kwargs": json.dumps({"campaign": "spring-sale"})}),
        ("Winter sale launch", "demo.tasks.launch_campaign", {"clocked": past_launch, "one_off": True, "enabled": False, "kwargs": json.dumps({"campaign": "winter-sale"})}),
        ("Clean expired sessions", "demo.tasks.clear_sessions", {"crontab": nightly, "enabled": False}),
        ("Legacy cache warmup", "demo.tasks.rebuild_index", {"interval": every_hour, "expires": timezone.now() - timedelta(days=3), "description": "Expired, kept for history."}),
        ("Delayed archive start", "demo.tasks.archive_tickets", {"crontab": weekly, "start_time": timezone.now() + timedelta(days=14)}),
    ]
    for name, task, schedule in tasks:
        never_ran = "clocked" in schedule or "start_time" in schedule
        runs = 0 if never_ran else rng.randint(20, 4000)
        schedule.setdefault("kwargs", json.dumps({"dry_run": False}))
        PeriodicTask.objects.create(
            name=name,
            task=task,
            total_run_count=runs,
            last_run_at=past(2) if runs else None,
            **schedule,
        )
