"""Reusable building blocks for Unfold admin classes."""

from decimal import Decimal

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$"}


class ImportExportAdmin(ModelAdmin, ImportExportModelAdmin):
    """Unfold model admin with import / export buttons on the changelist."""

    import_form_class = ImportForm
    export_form_class = ExportForm


def admin_url(obj, view="change"):
    meta = obj._meta
    return reverse(f"admin:{meta.app_label}_{meta.model_name}_{view}", args=[obj.pk])


def admin_link(obj, text=None):
    return format_html('<a href="{}">{}</a>', admin_url(obj), text or obj)


def redirect_back(request, fallback):
    return redirect(request.headers.get("referer") or fallback)


def done(request, message, fallback):
    """Show a success message and return to the previous page."""
    messages.success(request, message)
    return redirect_back(request, fallback)


def initials(*parts):
    return "".join(part[0] for part in parts if part).upper()


def header(title, subtitle=None, *parts):
    """Value for `@display(header=True)`: avatar with initials, title, subtitle."""
    return [title, subtitle, initials(*parts) or initials(title)]


def dropdown(title, objects, empty="-"):
    """Value for `@display(dropdown=True)`: list of links to related objects."""
    objects = list(objects)

    if not objects:
        return empty

    return {
        "title": title.format(count=len(objects)),
        "items": [{"title": str(obj), "link": admin_url(obj)} for obj in objects],
        "striped": True,
        "max_height": 200,
    }


def money(amount, currency="EUR"):
    if amount is None:
        return "-"

    amount = Decimal(amount).quantize(Decimal("0.01"))
    return f"{CURRENCY_SYMBOLS.get(str(currency), str(currency))}{amount:,}"
