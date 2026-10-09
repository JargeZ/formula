from django.db import models
from django.db.models import DecimalField, F, OuterRef, Subquery, Sum
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from simple_history.models import HistoricalRecords

from utils.models import AuditedModel


class Customer(AuditedModel):
    first_name = models.CharField(_("first name"), max_length=255)
    last_name = models.CharField(_("last name"), max_length=255)
    email = models.EmailField(_("email"))
    phone = models.CharField(_("phone"), max_length=64, blank=True)
    address = models.TextField(_("address"), blank=True)
    city = models.CharField(_("city"), max_length=255, blank=True)
    state = models.CharField(_("state"), max_length=255, blank=True)
    zip_code = models.CharField(_("zip code"), max_length=32, blank=True)
    country = models.CharField(_("country"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("customer")
        verbose_name_plural = _("customers")
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class OrderStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    SHIPPED = "shipped", _("Shipped")
    DELIVERED = "delivered", _("Delivered")
    CANCELLED = "cancelled", _("Cancelled")


class OrderQuerySet(models.QuerySet):
    def with_total(self):
        # Subquery keeps the sum correct when other joins (filters) are added
        totals = (
            OrderItem.objects.filter(order=OuterRef("pk"))
            .values("order")
            .annotate(total=Sum(F("price") * F("quantity")))
            .values("total")
        )
        return self.annotate(
            total_price=Subquery(
                totals, output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )


class Order(AuditedModel):
    number = models.CharField(_("number"), max_length=32, unique=True)
    status = models.CharField(
        _("status"), max_length=32, choices=OrderStatus, default=OrderStatus.PENDING
    )
    customer = models.ForeignKey(
        Customer, verbose_name=_("customer"), on_delete=models.CASCADE
    )
    products = models.ManyToManyField(
        "demo.Product", verbose_name=_("products"), through="OrderItem", blank=True
    )
    history = HistoricalRecords()

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]

    def __str__(self):
        return self.number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name=_("order"), on_delete=models.CASCADE)
    product = models.ForeignKey(
        "demo.Product", verbose_name=_("product"), on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    price = MoneyField(
        _("price"), max_digits=10, decimal_places=2, default_currency="EUR"
    )
    weight = models.PositiveIntegerField(_("weight"), default=0, db_index=True)

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")
        ordering = ["weight"]

    def __str__(self):
        return f"{self.quantity}× {self.product}"

    @property
    def total(self):
        return self.price * self.quantity if self.price is not None else None
