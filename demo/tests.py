from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from demo.models import Category, Order, OrderStatus, Product, Ticket
from formula.models import User

PAGES = [
    "admin:index",
    "admin:dashboard_system",
    "admin:dashboard_retention",
    "admin:dashboard_commerce",
    "admin:dashboard_spending",
    "admin:ui_buttons",
    "admin:ui_tables",
    "admin:crispy_vertical",
    "admin:crispy_horizontal",
    "admin:crispy_demo_formset",
    "admin:constance_config_changelist",
]

MODELS = [
    "demo_category",
    "demo_tag",
    "demo_product",
    "demo_customer",
    "demo_order",
    "demo_ticket",
    "formula_user",
    "sites_site",
    "waffle_flag",
    "waffle_switch",
    "waffle_sample",
    "django_celery_beat_periodictask",
]


class SeededAdminTests(TestCase):
    """Run with `manage.py test --debug-mode`: without DEBUG the database is readonly."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed", stdout=open("/dev/null", "w"))  # noqa: SIM115

    def setUp(self):
        self.assertTrue(self.client.login(username="demo", password="unfold123"))

    def test_pages(self):
        for name in PAGES:
            with self.subTest(name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

        response = self.client.get(reverse("admin:index") + "?dashboard=django")
        self.assertEqual(response.status_code, 200)

    def test_model_pages(self):
        for model in MODELS:
            changelist = self.client.get(reverse(f"admin:{model}_changelist"))
            self.assertEqual(changelist.status_code, 200, model)
            obj = changelist.context["cl"].result_list[0]
            change = self.client.get(reverse(f"admin:{model}_change", args=[obj.pk]))
            self.assertEqual(change.status_code, 200, model)
            add = self.client.get(reverse(f"admin:{model}_add"))
            self.assertEqual(add.status_code, 200, model)

    def test_check_status_moves_order_forward(self):
        order = Order.objects.filter(status=OrderStatus.PENDING).first()
        self.client.get(
            reverse("admin:demo_order_check_status", args=[order.pk]),
        )
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.PROCESSING)

    def test_rebuild_index_marks_product(self):
        product = Product.objects.first()
        self.client.get(reverse("admin:demo_product_rebuild_index", args=[product.pk]))
        product.refresh_from_db()
        self.assertIn("indexed_at", product.dataset)

    def test_category_is_translated(self):
        category = Category.objects.get(slug="photography")
        with translation.override("de"):
            self.assertEqual(category.name, "Fotografie")
        with translation.override("en"):
            self.assertEqual(category.name, "Photography")

    def test_agent_has_object_permissions_only_for_own_tickets(self):
        agent = User.objects.get(username="anna.kovac")
        own = Ticket.objects.filter(assigned_to=agent).first()
        other = Ticket.objects.exclude(assigned_to=agent).first()
        self.assertTrue(agent.has_perm("demo.change_ticket", own))
        self.assertFalse(agent.has_perm("demo.change_ticket", other))

    def test_object_permissions_page(self):
        ticket = Ticket.objects.first()
        url = reverse("admin:demo_ticket_permissions", args=[ticket.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
