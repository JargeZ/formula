from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import GenericTabularInline, ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    BooleanRadioFilter,
    RangeDateFilter,
    RangeDateTimeFilter,
    RangeNumericFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.fields import UnfoldAdminJSONSchemaField
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextInputWidget

from demo.models import Category, OrderItem, Product, ProductStatus, Tag, TagRelation
from utils.admin import ImportExportAdmin, done, money

WYSIWYG = {models.TextField: {"widget": WysiwygWidget}}

PRODUCT_STATUS_LABELS = {
    ProductStatus.ACTIVE: "success",
    ProductStatus.INACTIVE: "info",
    ProductStatus.OUT_OF_STOCK: "warning",
    ProductStatus.DISCONTINUED: "danger",
    ProductStatus.PREORDER: "info",
}

DATASET_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "title": "Name"},
        "email": {"type": "string", "title": "Email"},
        "age": {"type": "integer", "title": "Age"},
        "active": {"type": "boolean", "title": "Active"},
    },
}

DEFAULT_DATASET = {"name": "John Doe", "email": "john@example.com", "age": 32}


@admin.register(Category)
class CategoryAdmin(ImportExportAdmin):
    list_display = ["name", "slug", "display_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    fields = ["name", "slug", "description", "image", "is_active"]
    formfield_overrides = WYSIWYG

    @display(description=_("Active"), boolean=True)
    def display_active(self, instance):
        return instance.is_active


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    fields = ["name", "slug", "description"]
    formfield_overrides = WYSIWYG


class TagRelationInline(GenericTabularInline):
    model = TagRelation
    autocomplete_fields = ["tag"]
    extra = 0
    tab = True


class ProductOrderInline(TabularInline):
    """Read-only list of orders containing the product."""

    model = OrderItem
    verbose_name_plural = _("Orders")
    fields = ["order", "display_status", "display_customer", "display_created_at"]
    readonly_fields = fields
    can_delete = False
    max_num = 0
    show_change_link = True
    tab = True
    per_page = 10

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order__customer")

    @display(description=_("Status"))
    def display_status(self, instance):
        return instance.order.get_status_display()

    @display(description=_("Customer"))
    def display_customer(self, instance):
        return instance.order.customer

    @display(description=_("Created at"))
    def display_created_at(self, instance):
        return instance.order.created_at


class ProductAdminForm(forms.ModelForm):
    dataset = UnfoldAdminJSONSchemaField(
        label=_("Dataset"), schema=DATASET_SCHEMA, required=False
    )
    custom_select = forms.ChoiceField(
        label=_("Conditional select"),
        choices=[("show", _("Show")), ("hide", _("Hide"))],
        initial="hide",
        required=False,
        widget=UnfoldAdminSelectWidget,
    )
    custom_text_input = forms.CharField(
        label=_("Custom Text Input"),
        required=False,
        widget=UnfoldAdminTextInputWidget,
    )

    class Meta:
        model = Product
        fields = "__all__"


@admin.register(Product)
class ProductAdmin(DjangoQLSearchMixin, SimpleHistoryAdmin, ImportExportAdmin):
    form = ProductAdminForm
    list_display = [
        "name",
        "display_price",
        "display_status",
        "display_category",
        "display_tags",
    ]
    list_filter = [
        ("category", AutocompleteSelectFilter),
        ("is_active", BooleanRadioFilter),
        ("price", RangeNumericFilter),
        ("created_at", RangeDateFilter),
        ("modified_at", RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ["name"]
    autocomplete_fields = ["category"]
    inlines = [ProductOrderInline, TagRelationInline]
    formfield_overrides = WYSIWYG
    conditional_fields = {"custom_text_input": "custom_select == 'show'"}
    fieldsets = [
        (
            _("General"),
            {
                "classes": ["tab"],
                "fields": [
                    "name",
                    "price",
                    "status",
                    "category",
                    "image",
                    "instructions",
                    "description",
                    "specification",
                    "dataset",
                    "released_at",
                    "discontinued_at",
                    "is_active",
                    "custom_select",
                    "custom_text_input",
                ],
            },
        ),
    ]
    actions_row = ["rebuild_index", "reindex_cache", "mark_out_of_stock"]
    actions_submit_line = ["dataset"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category")
            .prefetch_related("tags__tag")
        )

    @display(description=_("Price"), ordering="price")
    def display_price(self, instance):
        return money(instance.price.amount, instance.price.currency)

    @display(description=_("Status"), label=PRODUCT_STATUS_LABELS)
    def display_status(self, instance):
        return instance.status, instance.get_status_display()

    @display(description=_("Category"), label=True)
    def display_category(self, instance):
        return instance.category and instance.category.name

    @display(description=_("Tags"), label=True)
    def display_tags(self, instance):
        return [relation.tag.name for relation in instance.tags.all()]

    # Demo actions: they only change data as if a real process had run.

    @action(description=_("Rebuild Index"), icon="manage_search")
    def rebuild_index(self, request, object_id):
        product = Product.objects.get(pk=object_id)
        product.dataset = {
            **(product.dataset or {}),
            "indexed_at": timezone.now().isoformat(),
        }
        product.save(update_fields=["dataset", "modified_at"])
        return done(
            request,
            _("Search index rebuilt for {}.").format(product),
            reverse_lazy("admin:demo_product_changelist"),
        )

    @action(description=_("Reindex Cache"), icon="cached")
    def reindex_cache(self, request, object_id):
        product = Product.objects.get(pk=object_id)
        product.save(update_fields=["modified_at"])
        return done(
            request,
            _("Cache refreshed for {}.").format(product),
            reverse_lazy("admin:demo_product_changelist"),
        )

    @action(description=_("Mark out of stock"), icon="remove_shopping_cart")
    def mark_out_of_stock(self, request, object_id):
        product = Product.objects.get(pk=object_id)
        product.status = ProductStatus.OUT_OF_STOCK
        product.save(update_fields=["status", "modified_at"])
        return done(
            request,
            _("{} is now out of stock.").format(product),
            reverse_lazy("admin:demo_product_changelist"),
        )

    @action(description=_("Save & reset dataset"))
    def dataset(self, request, obj):
        obj.dataset = DEFAULT_DATASET
        obj.save(update_fields=["dataset"])
