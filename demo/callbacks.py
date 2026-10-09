from django.urls import reverse

from demo.models import Order, Product, Ticket, TicketStatus


def orders_badge(request):
    return Order.objects.count()


def products_badge(request):
    return Product.objects.count()


def tickets_badge(request):
    return Ticket.objects.filter(status=TicketStatus.OPEN).count() or None


def default_dashboard_active(request):
    return request.path == reverse("admin:index") and "dashboard" not in request.GET


def django_dashboard_active(request):
    return request.GET.get("dashboard") == "django"
