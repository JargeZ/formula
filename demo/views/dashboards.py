"""Dashboards. Every number is calculated from the seeded database."""

from collections import Counter, defaultdict
from datetime import timedelta

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Min, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import PeriodicTask
from waffle.models import Flag, Switch

from demo.models import Customer, Order, OrderItem, OrderStatus, Ticket, TicketStatus
from utils.admin import admin_link as link
from utils.admin import money
from utils.charts import chart, kpi, percent, pie
from utils.views import AdminPageView

LINE_TOTAL = ExpressionWrapper(
    F("price") * F("quantity"),
    output_field=DecimalField(max_digits=12, decimal_places=2),
)

DASHBOARDS = [
    (_("Default"), "admin:index"),
    (_("System"), "admin:dashboard_system"),
    (_("Retention"), "admin:dashboard_retention"),
    (_("Commerce"), "admin:dashboard_commerce"),
    (_("Spending"), "admin:dashboard_spending"),
]


def days_ago(days):
    return timezone.now() - timedelta(days=days)


def sold_items(start=None, end=None):
    items = OrderItem.objects.exclude(order__status=OrderStatus.CANCELLED)

    if start:
        items = items.filter(order__created_at__gte=start)

    if end:
        items = items.filter(order__created_at__lt=end)

    return items


def revenue(items):
    return items.aggregate(value=Sum(LINE_TOTAL))["value"] or 0


def weekly_kpis():
    week, two_weeks = days_ago(7), days_ago(14)

    def compare(queryset, field="created_at"):
        current = queryset.filter(**{f"{field}__gte": week}).count()
        previous = queryset.filter(
            **{f"{field}__gte": two_weeks, f"{field}__lt": week}
        ).count()
        return current, previous

    orders = compare(Order.objects.all())
    customers = compare(Customer.objects.all())
    tickets = compare(Ticket.objects.all())
    revenue_now = revenue(sold_items(week))
    revenue_before = revenue(sold_items(two_weeks, week))
    units_now = sold_items(week).aggregate(v=Sum("quantity"))["v"] or 0
    units_before = sold_items(two_weeks, week).aggregate(v=Sum("quantity"))["v"] or 0

    return [
        kpi(_("Weekly orders"), orders[0], *orders),
        kpi(_("Weekly revenue"), money(revenue_now), revenue_now, revenue_before),
        kpi(_("New customers"), customers[0], *customers),
        kpi(_("Units sold"), units_now, units_now, units_before),
        kpi(_("Tickets opened"), tickets[0], *tickets),
    ]


def progress_items():
    orders = Order.objects.count()
    delivered = Order.objects.filter(status=OrderStatus.DELIVERED).count()
    customers = Customer.objects.annotate(n=Count("order"))
    repeat = customers.filter(n__gt=1).count()
    tickets = Ticket.objects.count()
    resolved = Ticket.objects.filter(
        status__in=[TicketStatus.RESOLVED, TicketStatus.CLOSED]
    ).count()

    return [
        {"title": _("Delivered orders"), "value": percent(delivered, orders)},
        {"title": _("Repeat customers"), "value": percent(repeat, customers.count())},
        {"title": _("Resolved tickets"), "value": percent(resolved, tickets)},
    ]


def cohort_color(value):
    if value >= 60:
        return "bg-primary-600 text-white dark:bg-primary-500"
    if value >= 30:
        return "bg-primary-400 text-white"
    if value > 0:
        return "bg-primary-200 dark:bg-primary-800"
    return None


def cohort(weeks=6):
    """Customers grouped by the week of their first order, active in later weeks."""
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday(), weeks=weeks - 1)

    def week_of(moment):
        return (timezone.localdate(moment) - start).days // 7

    activity = defaultdict(set)
    for customer_id, created_at in Order.objects.filter(
        created_at__date__gte=start
    ).values_list("customer_id", "created_at"):
        activity[customer_id].add(week_of(created_at))

    cohorts = defaultdict(set)
    first_orders = Order.objects.values("customer_id").annotate(first=Min("created_at"))
    for row in first_orders:
        index = week_of(row["first"])
        if 0 <= index < weeks:
            cohorts[index].add(row["customer_id"])

    rows = []
    for index in range(weeks):
        members = cohorts[index]
        cols = []
        for offset in range(weeks):
            if index + offset >= weeks:
                cols.append({"value": ""})
                continue

            active = sum(1 for member in members if index + offset in activity[member])
            value = percent(active, len(members))
            cols.append(
                {
                    "value": f"{value}%",
                    "subtitle": _("{} customers").format(active),
                    "color": cohort_color(value),
                }
            )

        week_start = start + timedelta(weeks=index)
        rows.append(
            {
                "header": {
                    "title": week_start.strftime("%b %d"),
                    "subtitle": _("{} new customers").format(len(members)),
                },
                "cols": cols,
            }
        )

    return {
        "headers": [{"title": _("Week {}").format(i)} for i in range(weeks)],
        "rows": rows,
    }


def top_customers(limit=5):
    customers = (
        Customer.objects.annotate(
            spent=Sum(
                F("order__orderitem__price") * F("order__orderitem__quantity"),
                filter=~Q(order__status=OrderStatus.CANCELLED),
            ),
            orders=Count("order", distinct=True),
        )
        .filter(spent__isnull=False)
        .order_by("-spent")[:limit]
    )
    return {
        "headers": [_("Customer"), _("Country"), _("Orders"), _("Total")],
        "rows": [[link(c), c.country, c.orders, money(c.spent)] for c in customers],
    }


def recent_orders(limit=6):
    orders = Order.objects.with_total().select_related("customer")[:limit]
    return {
        "headers": [_("Number"), _("Customer"), _("Status"), _("Total")],
        "rows": [
            [link(o), o.customer, o.get_status_display(), money(o.total_price)]
            for o in orders
        ],
    }


def daily(values_by_date, days):
    today = timezone.localdate()
    dates = [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]
    return [d.strftime("%b %d") for d in dates], [
        values_by_date.get(d, 0) for d in dates
    ]


def per_day(queryset, field, value, days):
    rows = (
        queryset.filter(**{f"{field}__gte": days_ago(days)})
        .values(day=F(f"{field}__date"))
        .annotate(value=value)
    )
    return daily({row["day"]: row["value"] for row in rows}, days)


def dashboard_context(active):
    return {
        "dashboards": [
            {"title": title, "link": reverse(url), "active": url == active}
            for title, url in DASHBOARDS
        ],
    }


def dashboard_callback(request, context):
    """Default dashboard on the admin index page."""
    if request.GET.get("dashboard"):
        return context

    context.update(
        dashboard_context("admin:index"),
        kpis=weekly_kpis(),
        progress=progress_items(),
        cohort=cohort(),
        top_customers=top_customers(),
        recent_orders=recent_orders(),
    )
    return context


class DashboardView(AdminPageView):
    url_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(dashboard_context(self.url_name))
        return context


class SystemView(DashboardView):
    title = _("System")
    url_name = "admin:dashboard_system"
    template_name = "demo/dashboards/system.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        tickets = Counter(
            timezone.localdate(created)
            for created in Ticket.objects.filter(
                created_at__gte=days_ago(60)
            ).values_list("created_at", flat=True)
        )
        tracker = []
        for offset in range(59, -1, -1):
            day = today - timedelta(days=offset)
            count = tickets.get(day, 0)
            tracker.append(
                {
                    "color": "bg-red-500"
                    if count >= 3
                    else "bg-orange-500"
                    if count == 2
                    else "bg-green-500",
                    "tooltip": _("{}: {} tickets").format(day, count),
                }
            )

        labels, values = per_day(Ticket.objects.all(), "created_at", Count("id"), 30)
        tasks = PeriodicTask.objects.select_related("interval", "crontab")
        context.update(
            health=[
                {
                    "title": _("Enabled periodic tasks"),
                    "value": percent(tasks.filter(enabled=True).count(), tasks.count()),
                },
                {
                    "title": _("Active switches"),
                    "value": percent(
                        Switch.objects.filter(active=True).count(),
                        Switch.objects.count(),
                    ),
                },
                *progress_items()[2:],
            ],
            tracker=tracker,
            tickets_chart=chart(labels, (_("Tickets"), values)),
            tasks={
                "headers": [_("Task"), _("Schedule"), _("Last run"), _("Runs")],
                "rows": [
                    [
                        link(task, task.name),
                        task.interval or task.crontab or "-",
                        task.last_run_at or "-",
                        task.total_run_count,
                    ]
                    for task in tasks
                ],
            },
            flags={
                "headers": [_("Flag"), _("Everyone"), _("Percent"), _("Note")],
                "rows": [
                    [link(f, f.name), f.everyone, f.percent or "-", f.note]
                    for f in Flag.objects.all()
                ],
            },
        )
        return context


class RetentionView(DashboardView):
    title = _("Retention")
    url_name = "admin:dashboard_retention"
    template_name = "demo/dashboards/retention.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            progress=progress_items(),
            kpis=weekly_kpis(),
            cohort=cohort(weeks=8),
            top_customers=top_customers(limit=8),
        )
        return context


class CommerceView(DashboardView):
    title = _("Commerce")
    url_name = "admin:dashboard_commerce"
    template_name = "demo/dashboards/commerce.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = (
            sold_items()
            .values("product_id", "product__name", "product__category__name")
            .annotate(units=Sum("quantity"), revenue=Sum(LINE_TOTAL))
            .order_by("-revenue")[:10]
        )
        trending = list(
            sold_items(days_ago(14))
            .values("product__name")
            .annotate(units=Sum("quantity"))
            .order_by("-units")[:7]
        )
        top_units = trending[0]["units"] if trending else 0
        labels, values = per_day(sold_items(), "order__created_at", Sum(LINE_TOTAL), 30)
        statuses = dict(
            Order.objects.values_list("status").annotate(Count("id")).order_by()
        )
        categories = (
            sold_items()
            .values("product__category__name")
            .annotate(revenue=Sum(LINE_TOTAL))
            .order_by("-revenue")
        )
        context.update(
            products={
                "headers": [_("Product"), _("Category"), _("Units"), _("Revenue")],
                "rows": [
                    [
                        format_html(
                            '<a href="{}">{}</a>',
                            reverse(
                                "admin:demo_product_change", args=[p["product_id"]]
                            ),
                            p["product__name"],
                        ),
                        p["product__category__name"] or "-",
                        p["units"],
                        money(p["revenue"]),
                    ]
                    for p in products
                ],
            },
            trending=[
                {
                    "title": t["product__name"],
                    "description": _("{} units").format(t["units"]),
                    "value": percent(t["units"], top_units),
                }
                for t in trending
            ],
            revenue_chart=chart(labels, (_("Revenue"), values)),
            status_chart=chart(
                OrderStatus.labels,
                (_("Orders"), [statuses.get(s, 0) for s in OrderStatus.values]),
            ),
            category_chart=chart(
                [c["product__category__name"] or "-" for c in categories],
                (_("Revenue"), [c["revenue"] for c in categories]),
            ),
        )
        return context


class SpendingView(DashboardView):
    title = _("Spending")
    url_name = "admin:dashboard_spending"
    template_name = "demo/dashboards/spending.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = revenue(sold_items())
        orders = Order.objects.exclude(status=OrderStatus.CANCELLED).count()
        month = revenue(sold_items(days_ago(30)))
        previous_month = revenue(sold_items(days_ago(60), days_ago(30)))
        cancelled = revenue(
            OrderItem.objects.filter(order__status=OrderStatus.CANCELLED)
        )
        categories = (
            sold_items()
            .values("product__category__name")
            .annotate(revenue=Sum(LINE_TOTAL))
            .order_by("-revenue")
        )
        countries = (
            sold_items()
            .values("order__customer__country")
            .annotate(revenue=Sum(LINE_TOTAL))
            .order_by("-revenue")[:6]
        )
        weekdays = Counter(
            timezone.localtime(created).strftime("%a")
            for created in Order.objects.values_list("created_at", flat=True)
        )
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        context.update(
            tiles=[
                {"title": _("Total revenue"), "value": money(total)},
                {
                    "title": _("Average order"),
                    "value": money(total / orders if orders else 0),
                },
                {"title": _("Last 30 days"), "value": money(month)},
                {"title": _("Cancelled value"), "value": money(cancelled)},
            ],
            growth=percent(month - previous_month, previous_month),
            category_chart=pie(
                [c["product__category__name"] or "-" for c in categories],
                [c["revenue"] for c in categories],
            ),
            weekday_chart=chart(days, (_("Orders"), [weekdays[d] for d in days])),
            country_chart=pie(
                [c["order__customer__country"] for c in countries],
                [c["revenue"] for c in countries],
            ),
        )
        return context
