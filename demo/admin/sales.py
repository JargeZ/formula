from django.contrib import admin
from django.db.models import Count
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import StackedInline, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    AutocompleteSelectMultipleFilter,
)
from unfold.decorators import action, display

from demo.models import Customer, Order, OrderItem, OrderStatus
from utils.admin import ImportExportAdmin, done, dropdown, header, money

ORDER_STATUS_LABELS = {
    OrderStatus.PENDING: "warning",
    OrderStatus.PROCESSING: "info",
    OrderStatus.SHIPPED: "info",
    OrderStatus.DELIVERED: "success",
    OrderStatus.CANCELLED: "danger",
}

# Next status for the "Check status" demo action
NEXT_ORDER_STATUS = {
    OrderStatus.PENDING: OrderStatus.PROCESSING,
    OrderStatus.PROCESSING: OrderStatus.SHIPPED,
    OrderStatus.SHIPPED: OrderStatus.DELIVERED,
}


class OrderItemInline(TabularInline):
    model = OrderItem
    fields = ["product", "quantity", "price", "display_total", "weight"]
    readonly_fields = ["display_total"]
    autocomplete_fields = ["product"]
    ordering_field = "weight"
    hide_ordering_field = True
    extra = 0

    @display(description=_("Total"))
    def display_total(self, instance):
        total = instance.total
        return money(total.amount, total.currency) if total else "-"


class CustomerOrderInline(StackedInline):
    model = Order
    fields = ["number", "status"]
    inlines = [OrderItemInline]
    show_change_link = True
    extra = 0
    per_page = 5
    collapsible = True


@admin.register(Customer)
class CustomerAdmin(DjangoQLSearchMixin, ImportExportAdmin):
    list_display = ["display_header", "phone", "country", "display_orders"]
    search_fields = ["first_name", "last_name", "email", "phone", "city"]
    inlines = [CustomerOrderInline]
    fieldsets = [
        (None, {"fields": [("first_name", "last_name"), "email", "phone"]}),
        (
            _("Address"),
            {"fields": ["address", ("city", "state"), ("zip_code", "country")]},
        ),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(orders_count=Count("order"))

    @display(description=_("Full Name"), header=True, ordering="last_name")
    def display_header(self, instance):
        return header(
            instance.full_name, instance.email, instance.first_name, instance.last_name
        )

    @display(description=_("Orders"), ordering="orders_count")
    def display_orders(self, instance):
        return instance.orders_count


@admin.register(Order)
class OrderAdmin(DjangoQLSearchMixin, SimpleHistoryAdmin, ImportExportAdmin):
    list_display = [
        "number",
        "customer",
        "display_products",
        "display_total",
        "display_status",
    ]
    list_display_links = ["number"]
    list_filter = [
        ("customer", AutocompleteSelectFilter),
        ("products", AutocompleteSelectMultipleFilter),
    ]
    list_filter_submit = True
    search_fields = ["number", "customer__first_name", "customer__last_name"]
    autocomplete_fields = ["customer"]
    fields = ["number", "status", "customer"]
    inlines = [OrderItemInline]
    actions_row = ["check_status"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("customer")
            .prefetch_related("products")
            .with_total()
        )

    @display(description=_("Products"), dropdown=True)
    def display_products(self, instance):
        return dropdown(_("Found {count} products"), instance.products.all())

    @display(description=_("Total Price"), ordering="total_price")
    def display_total(self, instance):
        return money(instance.total_price)

    @display(description=_("Status"), label=ORDER_STATUS_LABELS)
    def display_status(self, instance):
        return instance.status, instance.get_status_display()

    @action(description=_("Check status"), icon="sync", url_path="custom_row_action")
    def check_status(self, request, object_id):
        # Demo only: pretend the carrier reported progress and move one step forward.
        order = Order.objects.get(pk=object_id)
        order.status = NEXT_ORDER_STATUS.get(order.status, order.status)
        order.save(update_fields=["status", "modified_at"])
        return done(
            request,
            _("Order {} status: {}.").format(order, order.get_status_display()),
            reverse_lazy("admin:demo_order_changelist"),
        )
