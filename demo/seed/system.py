import json
from datetime import date, datetime, time, timedelta

from constance import config
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
DEMO_PASSWORD = "unfold123"

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
    flags = [
        ("new_checkout", "New one page checkout", {"percent": 25}),
        ("product_reviews", "Show reviews on product pages", {"everyone": True}),
        (
            "ai_recommendations",
            "Recommendations block on cart page",
            {"superusers": True},
        ),
        ("dark_mode_emails", "Dark mode for transactional emails", {"everyone": False}),
        ("beta_dashboard", "Beta analytics dashboard", {"staff": True}),
    ]
    for name, note, options in flags:
        Flag.objects.create(name=name, note=note, **options)

    for name, note, active in [
        ("maintenance_banner", "Show maintenance banner", False),
        ("free_shipping", "Free shipping over €50", True),
        ("newsletter_popup", "Newsletter signup popup", True),
        ("legacy_api", "Keep v1 API endpoints", False),
    ]:
        Switch.objects.create(name=name, note=note, active=active)

    for name, note, percent in [
        ("search_v2", "Route traffic to new search", 30),
        ("image_cdn", "Serve images from the new CDN", 75),
    ]:
        Sample.objects.create(name=name, note=note, percent=percent)


def seed_periodic_tasks():
    every_5_min = IntervalSchedule.objects.create(
        every=5, period=IntervalSchedule.MINUTES
    )
    every_hour = IntervalSchedule.objects.create(every=1, period=IntervalSchedule.HOURS)
    nightly = CrontabSchedule.objects.create(minute="0", hour="2")
    weekly = CrontabSchedule.objects.create(minute="30", hour="6", day_of_week="1")
    sunrise = SolarSchedule.objects.create(
        event="sunrise", latitude=48.1486, longitude=17.1077
    )
    launch = ClockedSchedule.objects.create(
        clocked_time=timezone.now() + timedelta(days=7)
    )

    tasks = [
        ("Sync stock levels", "demo.tasks.sync_stock", {"interval": every_5_min}),
        (
            "Send abandoned cart emails",
            "demo.tasks.abandoned_carts",
            {"interval": every_hour},
        ),
        ("Rebuild search index", "demo.tasks.rebuild_index", {"crontab": nightly}),
        ("Weekly sales report", "demo.tasks.sales_report", {"crontab": weekly}),
        ("Turn on storefront lights", "demo.tasks.storefront", {"solar": sunrise}),
        (
            "Spring sale launch",
            "demo.tasks.launch_campaign",
            {"clocked": launch, "one_off": True},
        ),
        (
            "Clean expired sessions",
            "demo.tasks.clear_sessions",
            {"crontab": nightly, "enabled": False},
        ),
    ]
    for name, task, schedule in tasks:
        runs = 0 if "clocked" in schedule else rng.randint(20, 4000)
        PeriodicTask.objects.create(
            name=name,
            task=task,
            kwargs=json.dumps({"dry_run": False}),
            total_run_count=runs,
            last_run_at=past(2) if runs else None,
            **schedule,
        )
