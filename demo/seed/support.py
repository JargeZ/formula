from django.utils import timezone
from guardian.shortcuts import assign_perm

from demo.models import Customer, Ticket, TicketStatus
from utils.seed import past, rng, weighted

TICKET_COUNT = 48

SUBJECTS = [
    (
        "Package not delivered",
        "Tracking shows delivered but nothing arrived at the address.",
    ),
    ("Wrong item received", "The box contained a different color than ordered."),
    ("Request for invoice", "Please send a VAT invoice for the company account."),
    ("Refund status", "Returned the item two weeks ago, still waiting for the refund."),
    ("Damaged on arrival", "The screen was cracked when the parcel was opened."),
    (
        "Change delivery address",
        "Customer moved and needs the order sent to a new address.",
    ),
    ("Warranty claim", "Device stopped charging after three months."),
    (
        "Discount code not applied",
        "Promo code was accepted but the total did not change.",
    ),
    ("Missing accessories", "Charger and cable were not included in the box."),
    ("Cancel order", "Customer ordered twice by mistake and wants one cancelled."),
    ("Pairing issue", "Earbuds do not pair with the phone after the latest update."),
    (
        "Question about compatibility",
        "Will this adapter work with an older laptop model?",
    ),
]

STATUS_WEIGHTS = {
    TicketStatus.RESOLVED: 18,
    TicketStatus.CLOSED: 14,
    TicketStatus.PENDING: 5,
    TicketStatus.ON_HOLD: 3,
    TicketStatus.CANCELLED: 3,
}


def seed_support(orders, agents):
    tickets, dates = [], []

    for index in range(TICKET_COUNT):
        order = rng.choice(orders)
        subject, description = rng.choice(SUBJECTS)
        created_at = past(60)
        dates.append(created_at)
        recent = (timezone.now() - created_at).days < 3
        tickets.append(
            Ticket(
                name=f"{subject} – {order.number}",
                description=description,
                assigned_to=rng.choice(agents),
                customer=order.customer,
                order=order,
                # Only fresh tickets are still open, which keeps the sidebar badge small
                status=TicketStatus.OPEN if recent else weighted(STATUS_WEIGHTS),
                weight=index,
            )
        )

    tickets = Ticket.objects.bulk_create(tickets)
    for ticket, created_at in zip(tickets, dates, strict=True):
        ticket.created_at = ticket.modified_at = created_at
    Ticket.objects.bulk_update(tickets, ["created_at", "modified_at"])

    # django-guardian: each agent may view and change only their own tickets
    # and view the customers behind them
    for agent in agents:
        own = Ticket.objects.filter(assigned_to=agent)
        customers = Customer.objects.filter(ticket__in=own).distinct()
        for perm in ("demo.view_ticket", "demo.change_ticket"):
            assign_perm(perm, agent, own)
        assign_perm("demo.view_customer", agent, customers)
