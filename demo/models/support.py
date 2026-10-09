from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.models import AuditedModel


class TicketStatus(models.TextChoices):
    OPEN = "open", _("Open")
    CLOSED = "closed", _("Closed")
    PENDING = "pending", _("Pending")
    RESOLVED = "resolved", _("Resolved")
    ON_HOLD = "on_hold", _("On Hold")
    CANCELLED = "cancelled", _("Cancelled")


class Ticket(AuditedModel):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("assigned to"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    customer = models.ForeignKey(
        "demo.Customer",
        verbose_name=_("customer"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    order = models.ForeignKey(
        "demo.Order",
        verbose_name=_("order"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        _("status"), max_length=32, choices=TicketStatus, default=TicketStatus.OPEN
    )
    weight = models.PositiveIntegerField(_("weight"), default=0, db_index=True)

    class Meta:
        verbose_name = _("ticket")
        verbose_name_plural = _("tickets")
        ordering = ["weight"]

    def __str__(self):
        return self.name
