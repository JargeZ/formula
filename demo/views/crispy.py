from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from unfold.views import BaseAutocompleteView, UnfoldSiteViewMixin

from demo.forms import (
    ContactFormSet,
    ContactFormSetHelper,
    HorizontalForm,
    VerticalForm,
)
from demo.models import Product


class CrispyFormView(UnfoldSiteViewMixin, FormView):
    permission_required = ()
    template_name = "demo/crispy/form.html"

    def form_valid(self, form):
        # Demo only: nothing is stored
        messages.success(self.request, _("Form submitted successfully."))
        return super().form_valid(form)


class VerticalFormView(CrispyFormView):
    title = _("Vertical Form")
    form_class = VerticalForm
    success_url = reverse_lazy("admin:crispy_vertical")


class HorizontalFormView(CrispyFormView):
    title = _("Horizontal Form")
    form_class = HorizontalForm
    success_url = reverse_lazy("admin:crispy_horizontal")


class FormsetView(CrispyFormView):
    title = _("Formset")
    form_class = ContactFormSet
    success_url = reverse_lazy("admin:crispy_demo_formset")

    def get_context_data(self, **kwargs):
        return super().get_context_data(helper=ContactFormSetHelper(), **kwargs)


class ProductAutocompleteView(BaseAutocompleteView):
    admin_site = None  # passed by UNFOLD["SITE_VIEWS"]
    model = Product

    def get_queryset(self):
        term = self.request.GET.get("term", "")
        return Product.objects.filter(name__icontains=term).order_by("name")
