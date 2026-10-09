from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import action, display
from unfold.widgets import UnfoldAdminTextareaWidget

from demo.models import Ticket, TicketStatus

TICKET_STATUS_LABELS = {
    TicketStatus.OPEN: "warning",
    TicketStatus.PENDING: "info",
    TicketStatus.ON_HOLD: "info",
    TicketStatus.RESOLVED: "success",
    TicketStatus.CLOSED: "success",
    TicketStatus.CANCELLED: "danger",
}


@admin.register(Ticket)
class TicketAdmin(GuardedModelAdmin, ModelAdmin):
    list_display = [
        "name",
        "customer",
        "order",
        "display_status",
        "created_at",
        "weight",
    ]
    list_select_related = ["customer", "order"]
    date_hierarchy = "created_at"
    ordering_field = "weight"
    hide_ordering_field = True
    autocomplete_fields = ["assigned_to", "customer", "order"]
    fields = [
        "name",
        "description",
        "assigned_to",
        "customer",
        "order",
        "status",
        "weight",
    ]
    formfield_overrides = {models.TextField: {"widget": UnfoldAdminTextareaWidget}}
    actions = ["resolve"]

    @display(description=_("Status"), label=TICKET_STATUS_LABELS)
    def display_status(self, instance):
        return instance.status, instance.get_status_display()

    @action(description=_("Mark selected tickets as resolved"))
    def resolve(self, request, queryset):
        count = queryset.update(status=TicketStatus.RESOLVED)
        self.message_user(request, _("{} tickets resolved.").format(count))
