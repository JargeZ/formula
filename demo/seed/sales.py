import unicodedata
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from demo.models import Customer, Order, OrderItem, OrderStatus, ProductStatus
from utils.seed import past, rng, weighted

CUSTOMER_COUNT = 120
ORDER_COUNT = 201

FIRST_NAMES = [
    "Emma",
    "Liam",
    "Olivia",
    "Noah",
    "Sophia",
    "Lucas",
    "Mia",
    "Elias",
    "Lena",
    "Jonas",
    "Clara",
    "Felix",
    "Hannah",
    "Leon",
    "Marie",
    "Paul",
    "Anna",
    "David",
    "Laura",
    "Tomas",
    "Eva",
    "Martin",
    "Julia",
    "Jakub",
    "Sara",
    "Mateo",
    "Chloe",
    "Hugo",
    "Alice",
    "Louis",
    "Isabella",
    "Oliver",
    "Ava",
    "James",
    "Grace",
    "Ethan",
    "Nora",
    "Adam",
    "Zoe",
    "Daniel",
]

LAST_NAMES = [
    "Müller",
    "Schmidt",
    "Novák",
    "Horváth",
    "Kowalski",
    "Rossi",
    "Bianchi",
    "García",
    "Martínez",
    "Dubois",
    "Lefebvre",
    "Jansen",
    "de Vries",
    "Andersson",
    "Nielsen",
    "Smith",
    "Johnson",
    "Brown",
    "Taylor",
    "Wilson",
    "Walker",
    "Clarke",
    "Murphy",
    "O'Brien",
    "Kovač",
    "Varga",
    "Svoboda",
    "Fischer",
    "Weber",
    "Wagner",
]

# country -> [(city, state, zip code, phone prefix)]
LOCATIONS = {
    "Germany": [
        ("Berlin", "Berlin", "10115", "+49"),
        ("Munich", "Bavaria", "80331", "+49"),
        ("Hamburg", "Hamburg", "20095", "+49"),
    ],
    "Slovakia": [
        ("Bratislava", "Bratislava", "81101", "+421"),
        ("Košice", "Košice", "04001", "+421"),
    ],
    "Czechia": [
        ("Prague", "Prague", "11000", "+420"),
        ("Brno", "South Moravia", "60200", "+420"),
    ],
    "Austria": [("Vienna", "Vienna", "1010", "+43"), ("Graz", "Styria", "8010", "+43")],
    "France": [
        ("Paris", "Île-de-France", "75001", "+33"),
        ("Lyon", "Auvergne-Rhône-Alpes", "69001", "+33"),
    ],
    "Netherlands": [
        ("Amsterdam", "North Holland", "1012", "+31"),
        ("Utrecht", "Utrecht", "3511", "+31"),
    ],
    "Spain": [
        ("Madrid", "Madrid", "28001", "+34"),
        ("Barcelona", "Catalonia", "08001", "+34"),
    ],
    "Italy": [("Milan", "Lombardy", "20121", "+39"), ("Rome", "Lazio", "00118", "+39")],
    "United States": [
        ("New York", "NY", "10001", "+1"),
        ("Austin", "TX", "73301", "+1"),
        ("Seattle", "WA", "98101", "+1"),
    ],
    "United Kingdom": [
        ("London", "England", "EC1A 1BB", "+44"),
        ("Manchester", "England", "M1 1AE", "+44"),
    ],
}

COUNTRY_WEIGHTS = {
    "Germany": 22,
    "Slovakia": 12,
    "Czechia": 10,
    "Austria": 8,
    "France": 10,
    "Netherlands": 7,
    "Spain": 7,
    "Italy": 7,
    "United States": 10,
    "United Kingdom": 7,
}

STREETS = [
    "Main Street",
    "Station Road",
    "Park Avenue",
    "Market Square",
    "Lake View",
    "Hill Road",
    "River Lane",
]

EMAIL_DOMAINS = ["example.com", "mail.example.org", "inbox.example.net"]

SELLABLE = [
    ProductStatus.ACTIVE,
    ProductStatus.OUT_OF_STOCK,
    ProductStatus.DISCONTINUED,
]


def ascii_name(text):
    text = unicodedata.normalize("NFKD", text.lower().replace("'", "").replace(" ", ""))
    return text.encode("ascii", "ignore").decode()


def make_customer(index):
    first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
    country = weighted(COUNTRY_WEIGHTS)
    city, state, zip_code, prefix = rng.choice(LOCATIONS[country])
    return Customer(
        first_name=first,
        last_name=last,
        email=f"{ascii_name(first)}.{ascii_name(last)}{index}@{rng.choice(EMAIL_DOMAINS)}",
        phone=f"{prefix} {rng.randint(100, 999)} {rng.randint(100, 999)} {rng.randint(100, 999)}",
        address=f"{rng.randint(1, 180)} {rng.choice(STREETS)}",
        city=city,
        state=state,
        zip_code=zip_code,
        country=country,
    )


def order_status(created_at):
    """Older orders are further along, like a real fulfilment pipeline."""
    if rng.random() < 0.06:
        return OrderStatus.CANCELLED

    age = (timezone.now() - created_at).days

    if age > 10:
        return OrderStatus.DELIVERED
    if age > 4:
        return rng.choice([OrderStatus.SHIPPED, OrderStatus.DELIVERED])
    if age > 1:
        return rng.choice([OrderStatus.PROCESSING, OrderStatus.SHIPPED])
    return rng.choice([OrderStatus.PENDING, OrderStatus.PROCESSING])


def seed_sales(products):
    customers = Customer.objects.bulk_create(
        make_customer(index) for index in range(1, CUSTOMER_COUNT + 1)
    )
    for customer in customers:
        customer.created_at = customer.modified_at = past(120, 1)
    Customer.objects.bulk_update(customers, ["created_at", "modified_at"])

    # A few loyal customers place most of the repeat orders
    loyalty = [rng.paretovariate(1.4) for _ in customers]
    sellable = [p for p in products if p.status in SELLABLE]

    orders = []
    for customer in rng.choices(customers, weights=loyalty, k=ORDER_COUNT):
        age = (timezone.now() - customer.created_at).days
        created_at = customer.created_at + timedelta(
            days=rng.randint(0, age), minutes=rng.randint(0, 600)
        )
        created_at = min(created_at, timezone.now() - timedelta(minutes=5))
        orders.append(
            Order(
                customer=customer,
                status=order_status(created_at),
                created_at=created_at,
            )
        )

    orders.sort(key=lambda order: order.created_at)
    for index, order in enumerate(orders, start=1):
        order.number = f"ORD-{index:04d}"

    # bulk_create resets auto_now_add fields, bulk_update writes them back
    dates = [order.created_at for order in orders]
    orders = Order.objects.bulk_create(orders)
    for order, created_at in zip(orders, dates, strict=True):
        order.created_at = created_at
        order.modified_at = created_at + timedelta(hours=rng.randint(0, 72))
    Order.objects.bulk_update(orders, ["created_at", "modified_at"])

    items = []
    for order in orders:
        for weight, product in enumerate(rng.sample(sellable, rng.randint(1, 4))):
            discount = Decimal(rng.choice([1, 1, 1, Decimal("0.9"), Decimal("0.8")]))
            items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=rng.choice([1, 1, 1, 2, 2, 3]),
                    price=(product.price.amount * discount).quantize(Decimal("0.01")),
                    price_currency="EUR",
                    weight=weight,
                )
            )
    OrderItem.objects.bulk_create(items)

    return customers, orders
