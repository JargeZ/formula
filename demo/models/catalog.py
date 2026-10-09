from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from simple_history.models import HistoricalRecords

from utils.models import AuditedModel


class Category(AuditedModel):
    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), max_length=255, unique=True)
    description = models.TextField(_("description"), blank=True)
    image = models.ImageField(_("image"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(AuditedModel):
    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), max_length=255, unique=True)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        ordering = ["name"]

    def __str__(self):
        return self.name


class TagRelation(models.Model):
    """Attaches a tag to any object."""

    tag = models.ForeignKey(Tag, verbose_name=_("tag"), on_delete=models.CASCADE)
    content_type = models.ForeignKey(
        ContentType, verbose_name=_("content type"), on_delete=models.CASCADE
    )
    object_id = models.PositiveBigIntegerField(_("object id"))
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("tag relation")
        verbose_name_plural = _("tag relations")
        indexes = [models.Index(fields=["content_type", "object_id"])]
        constraints = [
            models.UniqueConstraint(
                fields=["tag", "content_type", "object_id"], name="unique_tag_relation"
            )
        ]

    def __str__(self):
        return str(self.tag)


# Fields from demo/translation.py. modeltranslation adds `<field>_<lang>` columns after
# simple_history built HistoricalProduct, so history must skip them.
# ponytail: history keeps only the default-language value of these fields.
PRODUCT_TRANSLATED_FIELDS = ["name", "description", "specification"]


class ProductStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    INACTIVE = "inactive", _("Inactive")
    OUT_OF_STOCK = "out_of_stock", _("Out of Stock")
    DISCONTINUED = "discontinued", _("Discontinued")
    PREORDER = "preorder", _("Preorder")


class Product(AuditedModel):
    name = models.CharField(_("name"), max_length=255)
    price = MoneyField(
        _("price"), max_digits=10, decimal_places=2, default_currency="EUR"
    )
    status = models.CharField(
        _("status"),
        max_length=32,
        choices=ProductStatus,
        default=ProductStatus.ACTIVE,
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_("category"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    image = models.ImageField(_("image"), blank=True)
    instructions = models.FileField(_("instructions"), blank=True)
    description = models.TextField(_("description"), blank=True)
    specification = models.TextField(_("specification"), blank=True)
    dataset = models.JSONField(_("dataset"), null=True, blank=True)
    released_at = models.DateField(_("released at"), null=True, blank=True)
    discontinued_at = models.DateTimeField(_("discontinued at"), null=True, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    tags = GenericRelation(TagRelation)
    history = HistoricalRecords(
        excluded_fields=[
            f"{field}_{code}"
            for field in PRODUCT_TRANSLATED_FIELDS
            for code, _label in settings.LANGUAGES
        ]
    )

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["name"]

    def __str__(self):
        return self.name
