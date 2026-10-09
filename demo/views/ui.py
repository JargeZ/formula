from django.utils.translation import gettext_lazy as _

from demo.models import Customer, Product
from utils.admin import admin_link as link
from utils.admin import money
from utils.views import AdminPageView


class ButtonsView(AdminPageView):
    title = _("Buttons")
    template_name = "demo/ui/buttons.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            variants=["primary", "default", "secondary", "ghost", "danger"],
            sizes=["xs", "sm", "md", "lg"],
            **kwargs,
        )


class TablesView(AdminPageView):
    title = _("Tables")
    template_name = "demo/ui/tables.html"

    def get_context_data(self, **kwargs):
        products = Product.objects.select_related("category")[:8]
        customers = Customer.objects.all()[:6]
        product_table = {
            "headers": [_("Product"), _("Category"), _("Status"), _("Price")],
            "rows": [
                [
                    link(p),
                    p.category or "-",
                    p.get_status_display(),
                    money(p.price.amount, p.price.currency),
                ]
                for p in products
            ],
        }
        customer_table = {
            "headers": [_("Customer"), _("Email"), _("City"), _("Country")],
            "rows": [[link(c), c.email, c.city, c.country] for c in customers],
        }
        return super().get_context_data(
            product_table=product_table, customer_table=customer_table, **kwargs
        )
