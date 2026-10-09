import logging
import shutil
from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from os import environ, path
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.contrib.constance.settings import UNFOLD_CONSTANCE_ADDITIONAL_FIELDS

######################################################################
# General
######################################################################
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = environ.get("SECRET_KEY", get_random_secret_key())

DEBUG = environ.get("DEBUG") == "1"

ROOT_URLCONF = "formula.urls"

WSGI_APPLICATION = "formula.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

SITE_ID = 1

######################################################################
# Domains
######################################################################
ALLOWED_HOSTS = environ.get("ALLOWED_HOSTS", "localhost").split(",")

CSRF_TRUSTED_ORIGINS = environ.get(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:8000"
).split(",")

######################################################################
# Apps
######################################################################
INSTALLED_APPS = [
    "modeltranslation",
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.constance",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.hijack",
    "unfold.contrib.waffle",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.sites",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "crispy_forms",
    "import_export",
    "guardian",
    "constance",
    "simple_history",
    "django_celery_beat",
    "djmoney",
    "djangoql",
    "hijack",
    "waffle",
    "django_unfold_agentic_layer",
    "formula",
    "demo",
]

if environ.get("UNFOLD_STUDIO") == "1":
    INSTALLED_APPS.insert(0, "unfold_studio")

######################################################################
# Middleware
######################################################################
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # After whitenoise: static files are not logged
    "request_logging.middleware.LoggingMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "formula.middleware.ReadonlyExceptionHandlerMiddleware",
]

# Dev only: debug_toolbar adds ~40 modules to every worker.
if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(2, "debug_toolbar.middleware.DebugToolbarMiddleware")

######################################################################
# Sessions
######################################################################
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

######################################################################
# Templates
######################################################################
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            path.normpath(path.join(BASE_DIR, "formula/templates")),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "formula.context_processors.variables",
            ],
        },
    },
]

######################################################################
# Databases
######################################################################
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "database.sqlite",
    },
}

# Demo mode: the database is baked into the image and opened as immutable.
# mode=ro: a read-write open copies the file into the Fly machine rootfs layer, which survives deploys.
DATABASE_READONLY = environ.get("DATABASE_READONLY") == "1"

if DATABASE_READONLY:
    baked_database = DATABASES["default"]["NAME"]
    DATABASES["default"]["NAME"] = f"file:{baked_database}?mode=ro&immutable=1"

    # MCP OAuth must store clients and tokens, so the agentic layer gets a writable
    # copy of the whole database (tokens reference auth_user). A newer image replaces it.
    agentic_database = Path("/tmp/agentic_layer.sqlite")
    if not agentic_database.exists() or agentic_database.stat().st_mtime < baked_database.stat().st_mtime:
        shutil.copyfile(baked_database, agentic_database)

    DATABASES["agentic_layer"] = {"ENGINE": "django.db.backends.sqlite3", "NAME": agentic_database}
    DATABASE_ROUTERS = ["formula.routers.AgenticLayerRouter"]

######################################################################
# Authentication
######################################################################
AUTH_USER_MODEL = "formula.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LOGIN_URL = "admin:login"

LOGIN_REDIRECT_URL = reverse_lazy("admin:index")

######################################################################
# Localization
######################################################################
LANGUAGE_CODE = "en"

TIME_ZONE = "Europe/Bratislava"

USE_I18N = True

USE_TZ = True

LANGUAGES = (
    ("de", _("German")),
    ("en", _("English")),
)

# https://docs.djangoproject.com/en/5.1/ref/settings/#date-input-formats
DATE_INPUT_FORMATS = [
    "%d.%m.%Y",  # Custom input
    "%Y-%m-%d",  # '2006-10-25'
    "%m/%d/%Y",  # '10/25/2006'
    "%m/%d/%y",  # '10/25/06'
    "%b %d %Y",  # 'Oct 25 2006'
    "%b %d, %Y",  # 'Oct 25, 2006'
    "%d %b %Y",  # '25 Oct 2006'
    "%d %b, %Y",  # '25 Oct, 2006'
    "%B %d %Y",  # 'October 25 2006'
    "%B %d, %Y",  # 'October 25, 2006'
    "%d %B %Y",  # '25 October 2006'
    "%d %B, %Y",  # '25 October, 2006'
]

# https://docs.djangoproject.com/en/5.1/ref/settings/#datetime-input-formats
DATETIME_INPUT_FORMATS = [
    "%d.%m.%Y %H:%M:%S",  # Custom input
    "%Y-%m-%d %H:%M:%S",  # '2006-10-25 14:30:59'
    "%Y-%m-%d %H:%M:%S.%f",  # '2006-10-25 14:30:59.000200'
    "%Y-%m-%d %H:%M",  # '2006-10-25 14:30'
    "%m/%d/%Y %H:%M:%S",  # '10/25/2006 14:30:59'
    "%m/%d/%Y %H:%M:%S.%f",  # '10/25/2006 14:30:59.000200'
    "%m/%d/%Y %H:%M",  # '10/25/2006 14:30'
    "%m/%d/%y %H:%M:%S",  # '10/25/06 14:30:59'
    "%m/%d/%y %H:%M:%S.%f",  # '10/25/06 14:30:59.000200'
    "%m/%d/%y %H:%M",  # '10/25/06 14:30'
]

######################################################################
# Static
######################################################################
STATIC_URL = "/static/"

STATICFILES_DIRS = [BASE_DIR / "formula" / "static"]

STATIC_ROOT = BASE_DIR / "static"

MEDIA_ROOT = BASE_DIR / "media"

MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

######################################################################
# Unfold
######################################################################
UNFOLD = {
    "STUDIO": {
        # "header_sticky": True,
        # "layout_style": "boxed",
        # "header_variant": "dark",
        # "sidebar_style": "minimal",
        # "sidebar_variant": "dark",
        # "site_banner": "Custom global message",
    },
    "SITE_TITLE": _("Formula Admin"),
    "SITE_HEADER": _("Formula Admin"),
    "SITE_SUBHEADER": _("Example demo project"),
    "SITE_SYMBOL": "dashboard",
    "SITE_ICON": lambda request: static("formula/images/logo.svg"),
    # "SITE_URL": None,
    "SITE_DROPDOWN": [
        {
            "icon": "diamond",
            "title": _("Unfold theme repository"),
            "link": "https://github.com/unfoldadmin/django-unfold",
        },
        {
            "icon": "rocket_launch",
            "title": _("Turbo boilerplate repository"),
            "link": "https://github.com/unfoldadmin/turbo",
        },
        {
            "icon": "description",
            "title": _("Technical documentation"),
            "link": "https://unfoldadmin.com/docs/",
        },
    ],
    # "SHOW_HISTORY": True,
    "SHOW_LANGUAGES": True,
    "LANGUAGE_FLAGS": {
        "de": "🇩🇪",
        "en": "🇺🇸",
    },
    "ENVIRONMENT": "formula.utils.environment_callback",
    "DASHBOARD_CALLBACK": "demo.views.dashboards.dashboard_callback",
    "SITE_VIEWS": [
        ("dashboard/system", "dashboard_system", "demo.views.dashboards.SystemView"),
        (
            "dashboard/retention",
            "dashboard_retention",
            "demo.views.dashboards.RetentionView",
        ),
        (
            "dashboard/commerce",
            "dashboard_commerce",
            "demo.views.dashboards.CommerceView",
        ),
        (
            "dashboard/spending",
            "dashboard_spending",
            "demo.views.dashboards.SpendingView",
        ),
        ("ui/buttons", "ui_buttons", "demo.views.ui.ButtonsView"),
        ("ui/tables", "ui_tables", "demo.views.ui.TablesView"),
        ("crispy/vert", "crispy_vertical", "demo.views.crispy.VerticalFormView"),
        ("crispy/horiz", "crispy_horizontal", "demo.views.crispy.HorizontalFormView"),
        ("crispy/formset", "crispy_demo_formset", "demo.views.crispy.FormsetView"),
        (
            "crispy/autocomplete/products",
            "crispy_product_autocomplete",
            "demo.views.crispy.ProductAutocompleteView",
        ),
    ],
    "LOGIN": {
        "image": lambda request: static("formula/images/login-bg.jpg"),
        "form": "formula.forms.LoginForm",
    },
    "STYLES": [
        # lambda request: static("css/styles.css"),
    ],
    "SCRIPTS": [
        # lambda request: static("js/chart.min.js"),
    ],
    "TABS": [
        {
            "models": [
                "formula.race",
                "formula.constructor",
            ],
            "items": [
                {
                    "title": _("Races"),
                    "link": reverse_lazy("admin:formula_race_changelist"),
                },
                {
                    "title": _("Constructors"),
                    "link": reverse_lazy("admin:formula_constructor_changelist"),
                },
            ],
        },
        {
            "page": "drivers",
            "models": ["formula.driver"],
            "items": [
                {
                    "title": _("Drivers"),
                    "link": reverse_lazy("admin:formula_driver_changelist"),
                    "active": lambda request: request.path
                    == reverse_lazy("admin:formula_driver_changelist")
                    and "status__exact" not in request.GET,
                },
                {
                    "title": _("Active drivers"),
                    "link": lambda request: f"{
                        reverse_lazy('admin:formula_driver_changelist')
                    }?status__exact=ACTIVE",
                },
                {
                    "title": _("Crispy Form"),
                    "link": reverse_lazy("admin:crispy_form"),
                },
                {
                    "title": _("Crispy Formset"),
                    "link": reverse_lazy("admin:crispy_formset"),
                },
            ],
        },
    ],
    "COMMAND": {
        "search_models": "formula.utils.search_models_callback",
        "show_history": "formula.utils.show_history_callback",
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "command_search": True,
        "navigation": [
            {
                "title": _("Dashboards"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Default"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        "active": "demo.callbacks.default_dashboard_active",
                    },
                    {
                        "title": _("System"),
                        "icon": "monitor_heart",
                        "link": reverse_lazy("admin:dashboard_system"),
                    },
                    {
                        "title": _("Retention"),
                        "icon": "group_add",
                        "link": reverse_lazy("admin:dashboard_retention"),
                    },
                    {
                        "title": _("Commerce"),
                        "icon": "storefront",
                        "link": reverse_lazy("admin:dashboard_commerce"),
                    },
                    {
                        "title": _("Spending"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:dashboard_spending"),
                    },
                    {
                        "title": _("Django"),
                        "icon": "apps",
                        "link": lambda request: f"{reverse_lazy('admin:index')}?dashboard=django",
                        "active": "demo.callbacks.django_dashboard_active",
                    },
                ],
            },
            {
                "title": _("Commerce"),
                "items": [
                    {
                        "title": _("Orders"),
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:demo_order_changelist"),
                        "badge": "demo.callbacks.orders_badge",
                    },
                    {
                        "title": _("Products"),
                        "icon": "inventory",
                        "link": reverse_lazy("admin:demo_product_changelist"),
                        "badge": "demo.callbacks.products_badge",
                    },
                    {
                        "title": _("Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:demo_category_changelist"),
                    },
                    {
                        "title": _("Tags"),
                        "icon": "tag",
                        "link": reverse_lazy("admin:demo_tag_changelist"),
                    },
                ],
            },
            {
                "title": _("CRM"),
                "items": [
                    {
                        "title": _("Customers"),
                        "icon": "group",
                        "link": reverse_lazy("admin:demo_customer_changelist"),
                    },
                    {
                        "title": _("Tickets"),
                        "icon": "event_note",
                        "link": reverse_lazy("admin:demo_ticket_changelist"),
                        "badge": "demo.callbacks.tickets_badge",
                        "badge_variant": "danger",
                    },
                ],
            },
            {
                "title": _("UI Elements"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Buttons"),
                        "icon": "smart_button",
                        "link": reverse_lazy("admin:ui_buttons"),
                    },
                    {
                        "title": _("Tables"),
                        "icon": "table",
                        "link": reverse_lazy("admin:ui_tables"),
                    },
                    {
                        "title": _("Vertical Form"),
                        "icon": "view_agenda",
                        "link": reverse_lazy("admin:crispy_vertical"),
                    },
                    {
                        "title": _("Horizontal Form"),
                        "icon": "view_column",
                        "link": reverse_lazy("admin:crispy_horizontal"),
                    },
                    {
                        "title": _("Formset"),
                        "icon": "table_rows",
                        "link": reverse_lazy("admin:crispy_demo_formset"),
                    },
                ],
            },
            {
                "title": _("Formula"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Drivers"),
                        "icon": "sports_motorsports",
                        "active": "formula.utils.driver_list_link_callback",
                        ###########################################################
                        # Works only with Studio: https://unfoldadmin.com/studio/
                        ###########################################################
                        "items": [
                            {
                                "title": _("List drivers"),
                                "link": reverse_lazy("admin:formula_driver_changelist"),
                                "active": "formula.utils.driver_list_sublink_callback",
                            },
                            {
                                "title": _("Advanced filters"),
                                "link": reverse_lazy(
                                    "admin:formula_driverwithfilters_changelist"
                                ),
                            },
                            {
                                "title": _("Crispy form"),
                                "link": reverse_lazy("admin:crispy_form"),
                            },
                            {
                                "title": _("Crispy formset"),
                                "link": reverse_lazy("admin:crispy_formset"),
                            },
                        ],
                    },
                    {
                        "title": _("Circuits"),
                        "icon": "sports_score",
                        "link": reverse_lazy("admin:formula_circuit_changelist"),
                    },
                    {
                        "title": _("Races"),
                        "icon": "stadium",
                        "link": reverse_lazy("admin:formula_race_changelist"),
                        "badge": "formula.utils.badge_callback",
                        "badge_variant": "danger",
                        "badge_style": "solid",
                    },
                    {
                        "title": _("Standings"),
                        "icon": "trophy",
                        "link": reverse_lazy("admin:formula_standing_changelist"),
                        "permission": "formula.utils.permission_callback",
                        # "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
            {
                "title": _("Authentication and Authorization"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "account_circle",
                        "link": reverse_lazy("admin:formula_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Periodic Tasks"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Clocked"),
                        "icon": "hourglass_bottom",
                        "link": reverse_lazy(
                            "admin:django_celery_beat_clockedschedule_changelist"
                        ),
                    },
                    {
                        "title": _("Crontabs"),
                        "icon": "update",
                        "link": reverse_lazy(
                            "admin:django_celery_beat_crontabschedule_changelist"
                        ),
                    },
                    {
                        "title": _("Intervals"),
                        "icon": "timer",
                        "link": reverse_lazy(
                            "admin:django_celery_beat_intervalschedule_changelist"
                        ),
                    },
                    {
                        "title": _("Periodic tasks"),
                        "icon": "task",
                        "link": reverse_lazy(
                            "admin:django_celery_beat_periodictask_changelist"
                        ),
                    },
                    {
                        "title": _("Solar events"),
                        "icon": "event",
                        "link": reverse_lazy(
                            "admin:django_celery_beat_solarschedule_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Waffle"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Flags"),
                        "icon": "flag",
                        "link": reverse_lazy("admin:waffle_flag_changelist"),
                    },
                    {
                        "title": _("Switches"),
                        "icon": "toggle_on",
                        "link": reverse_lazy("admin:waffle_switch_changelist"),
                    },
                    {
                        "title": _("Samples"),
                        "icon": "percent",
                        "link": reverse_lazy("admin:waffle_sample_changelist"),
                    },
                ],
            },
            {
                "title": _("Constance"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Config"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:constance_config_changelist"),
                    },
                ],
            },
            {
                "title": _("Sites"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Sites"),
                        "icon": "language",
                        "link": reverse_lazy("admin:sites_site_changelist"),
                    },
                ],
            },
        ],
    },
}

UNFOLD_STUDIO_ENABLE_CUSTOMIZER = True

UNFOLD_STUDIO_DEFAULT_FRAGMENT = "color-schemes"

UNFOLD_STUDIO_ENABLE_SAVE = False

UNFOLD_STUDIO_ENABLE_FILEUPLOAD = False

UNFOLD_STUDIO_ALWAYS_OPEN = True

UNFOLD_STUDIO_ENABLE_RESET_PASSWORD = True

######################################################################
# Money
######################################################################
CURRENCIES = ("USD", "EUR")

######################################################################
# App
######################################################################
LOGIN_USERNAME = environ.get("LOGIN_USERNAME")

LOGIN_PASSWORD = environ.get("LOGIN_PASSWORD")

############################################################################
# Agentic layer (MCP at /mcp)
######################################################################
UNFOLD_AGENTIC_LAYER = {
    "PORTAL_TITLE": "Formula Agentic Layer",
    "SESSION_TTL": timedelta(days=1),
    # Shared between gunicorn workers, unlike the default LocMem cache.
    "CONFIRMATION_CACHE": "agentic_layer",
}

# Dev only: requests without a token act as the first superuser. Ignored when DEBUG is off.
UNFOLD_AGENTIC_LAYER_UNAUTHORIZED = environ.get("UNFOLD_AGENTIC_LAYER_UNAUTHORIZED") == "1"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "agentic_layer": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / ".cache" / "agentic_layer",
    },
}

# Behind a TLS-terminating proxy MCP OAuth needs the original https scheme.
if environ.get("SECURE_PROXY_SSL_HEADER") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

# Without this, DEBUG=False sends tracebacks only to mail_admins.
# django-request-logging: one line per request ("GET /path?query - 200"), no bodies or headers.
# Exceptions keep their traceback through the "django.request" logger -> root.
REQUEST_LOGGING_ENABLE_COLORIZE = False
REQUEST_LOGGING_DATA_LOG_LEVEL = logging.DEBUG
REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL = logging.INFO
DJANGO_REQUEST_LOGGING_LOGGER_NAME = "request_log"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        # The middleware also logs the request line and, for 5xx, bodies at ERROR: keep only the response line
        "response_line_only": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: record.levelno == logging.INFO
            and getattr(record, "response", None) is not None,
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "request_console": {
            "class": "logging.StreamHandler",
            "filters": ["response_line_only"],
        },
    },
    "loggers": {
        "request_log": {
            "handlers": ["request_console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}

######################################################################
# Debug toolbar
############################################################################
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}

######################################################################
# Plausible
######################################################################
PLAUSIBLE_DOMAIN = environ.get("PLAUSIBLE_DOMAIN")

######################################################################
# Sentry
######################################################################
SENTRY_DSN = environ.get("SENTRY_DSN")

if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        enable_tracing=False,
    )

######################################################################
# Crispy forms
######################################################################
CRISPY_TEMPLATE_PACK = "unfold_crispy"

CRISPY_ALLOWED_TEMPLATE_PACKS = ["unfold_crispy"]

######################################################################
# Constance
######################################################################
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_CONFIG = {
    "SITE_NAME": ("My Title", _("Website title")),
    "SITE_DESCRIPTION": ("", _("Website description")),
    "THEME": ("light-blue", _("Website theme"), "choice_field"),
    "IN_CONSTRUCTION": (False, _("Website in construction")),
    "SITE_URL": ("", _("Website URL")),
    "SITE_LOGO": ("", _("Website logo"), "image_field"),
    "SITE_FAVICON": ("", _("Website favicon"), "file_field"),
    "SITE_BACKGROUND_IMAGE": ("", _("Website background image"), "image_field"),
    "SITE_BACKGROUND_COLOR": ("#FFFFFF", _("Website background color")),
    "SITE_FONT_SIZE": (16, _("Base font size in pixels")),
    "SITE_ANALYTICS_ID": ("", _("Google Analytics ID")),
    "SITE_MAINTENANCE_MODE": (False, _("Enable maintenance mode")),
    "SITE_MAINTENANCE_MESSAGE": ("", _("Maintenance mode message")),
    "SITE_SOCIAL_LINKS": ("", _("Social media links")),
    "SITE_FOOTER_TEXT": ("", _("Footer text")),
    "SITE_META_KEYWORDS": ("", _("Meta keywords")),
    "SITE_CACHE_TTL": (3600, _("Cache TTL in seconds")),
    "SITE_DATE_FORMAT": ("%Y-%m-%d", _("Date format")),
    "SITE_TIME_ZONE": ("UTC", _("Time zone")),
    "SITE_DATE": (date(2026, 1, 1), _("Launch date")),
    "SITE_DATETIME": (datetime(2026, 1, 1, 9, 0), _("Launch date and time")),
    "SITE_TIME": (time(9, 0), _("Daily report time")),
}

CONSTANCE_CONFIG_FIELDSETS = OrderedDict(
    {
        "General Settings": {
            "fields": (
                "SITE_NAME",
                "SITE_DESCRIPTION",
                "SITE_URL",
            ),
            # "collapse": False,
        },
        "Theme & Design": {
            "fields": (
                "THEME",
                "SITE_FONT_SIZE",
                "SITE_BACKGROUND_COLOR",
                "SITE_BACKGROUND_IMAGE",
            ),
            # "collapse": False,
        },
        "Assets": {
            "fields": (
                "SITE_LOGO",
                "SITE_FAVICON",
            ),
            # "collapse": True,
        },
        "Content": {
            "fields": (
                "SITE_FOOTER_TEXT",
                "SITE_META_KEYWORDS",
                "SITE_SOCIAL_LINKS",
            ),
            # "collapse": True,
        },
        "System": {
            "fields": (
                "IN_CONSTRUCTION",
                "SITE_MAINTENANCE_MODE",
                "SITE_MAINTENANCE_MESSAGE",
                "SITE_CACHE_TTL",
                "SITE_DATE_FORMAT",
                "SITE_TIME_ZONE",
                "SITE_ANALYTICS_ID",
            ),
            # "collapse": True,
        },
        "Schedule": {
            "fields": (
                "SITE_DATE",
                "SITE_DATETIME",
                "SITE_TIME",
            ),
            # "collapse": True,
        },
    }
)


CONSTANCE_ADDITIONAL_FIELDS = {
    **UNFOLD_CONSTANCE_ADDITIONAL_FIELDS,
    "choice_field": [
        "django.forms.fields.ChoiceField",
        {
            "widget": "unfold.widgets.UnfoldAdminSelectWidget",
            "choices": (
                ("light-blue", "Light blue"),
                ("dark-blue", "Dark blue"),
            ),
        },
    ],
}
