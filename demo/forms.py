from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django.utils.translation import gettext_lazy as _
from unfold.fields import (
    UnfoldAdminAutocompleteModelChoiceField,
    UnfoldAdminMultipleAutocompleteModelChoiceField,
)
from unfold.layout import Submit
from unfold.widgets import (
    UnfoldAdminEmailInputWidget,
    UnfoldAdminSelectWidget,
    UnfoldAdminTextInputWidget,
)

from demo.models import Product
from formula.forms import CustomForm, CustomHorizontalForm

AUTOCOMPLETE_URL = "admin:crispy_product_autocomplete"


class AutocompleteFieldsMixin(forms.Form):
    object = UnfoldAdminAutocompleteModelChoiceField(
        label=_("Object – Single value"),
        queryset=Product.objects.all(),
        url_path=AUTOCOMPLETE_URL,
        required=False,
    )
    objects = UnfoldAdminMultipleAutocompleteModelChoiceField(
        label=_("Objects – Multiple values"),
        queryset=Product.objects.all(),
        url_path=AUTOCOMPLETE_URL,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["object"].initial = Product.objects.first()
        self.helper.layout.append(
            Fieldset(_("Autocomplete widgets"), "object", "objects")
        )


class VerticalForm(AutocompleteFieldsMixin, CustomForm):
    pass


class HorizontalForm(AutocompleteFieldsMixin, CustomHorizontalForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.add_input(Submit("submit", _("Submit")))


class ContactForm(forms.Form):
    name = forms.CharField(label=_("Name"), widget=UnfoldAdminTextInputWidget)
    email = forms.EmailField(label=_("Email"), widget=UnfoldAdminEmailInputWidget)
    priority = forms.ChoiceField(
        label=_("Priority"),
        choices=[("low", _("Low")), ("medium", _("Medium")), ("high", _("High"))],
        widget=UnfoldAdminSelectWidget,
    )


ContactFormSet = forms.formset_factory(ContactForm, extra=0, can_delete=True)


class ContactFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "unfold_crispy/layout/table_inline_formset.html"
        self.form_id = "contact-formset"
        self.form_add = True
        self.form_show_labels = False
        self.add_input(Submit("submit", _("Submit")))
