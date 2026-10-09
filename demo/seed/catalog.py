from datetime import timedelta
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.text import slugify

from demo.models import Category, Product, ProductStatus, Tag, TagRelation
from utils.seed import paragraphs, past, rng, weighted

PRODUCT_COUNT = 271

# category -> (description, product nouns, price range in EUR)
CATEGORIES = {
    "Laptops": (
        "Portable computers for work and play.",
        ["Laptop", "Notebook", "Ultrabook", "Chromebook"],
        (449, 2899),
    ),
    "Smartphones": (
        "Phones with the latest cameras and chips.",
        ["Phone", "Smartphone", "Phone Mini", "Phone Max"],
        (199, 1499),
    ),
    "Audio": (
        "Headphones, earbuds and speakers.",
        ["Headphones", "Earbuds", "Speaker", "Soundbar", "Microphone"],
        (29, 499),
    ),
    "Wearables": (
        "Watches and fitness trackers.",
        ["Smartwatch", "Fitness Band", "Ring Tracker"],
        (49, 799),
    ),
    "Home Office": (
        "Furniture and accessories for productive days.",
        ["Desk", "Office Chair", "Monitor Arm", "Desk Lamp", "Footrest"],
        (39, 899),
    ),
    "Gaming": (
        "Consoles, controllers and accessories.",
        ["Controller", "Gaming Mouse", "Gaming Keyboard", "Headset", "Console"],
        (25, 699),
    ),
    "Smart Home": (
        "Connected devices for every room.",
        ["Smart Plug", "Thermostat", "Video Doorbell", "Smart Bulb", "Hub"],
        (15, 299),
    ),
    "Photography": (
        "Cameras, lenses and tripods.",
        ["Mirrorless Camera", "Lens", "Tripod", "Camera Bag", "Flash"],
        (39, 2499),
    ),
    "Networking": (
        "Routers, mesh systems and switches.",
        ["Router", "Mesh System", "Switch", "Access Point"],
        (35, 599),
    ),
    "Accessories": (
        "Cables, chargers and cases.",
        ["USB-C Cable", "Charger", "Power Bank", "Case", "Adapter", "Stand"],
        (9, 129),
    ),
}

BRANDS = [
    "Nordic",
    "Aurora",
    "Vertex",
    "Lumen",
    "Pulse",
    "Atlas",
    "Orbit",
    "Nimbus",
    "Zenith",
    "Echo",
    "Kite",
    "Summit",
]
MODELS = [
    "Air",
    "Pro",
    "Lite",
    "Max",
    "One",
    "Neo",
    "Go",
    "Plus",
    "S",
    "X",
    "Ultra",
    "Mini",
]

TAGS = {
    "Bestseller": "Top selling products of the season.",
    "New Arrival": "Added to the catalog recently.",
    "Eco Friendly": "Made from recycled materials.",
    "Limited Edition": "Available only while stock lasts.",
    "Gift Idea": "Popular choice for presents.",
    "Premium": "Flagship quality and materials.",
    "Budget": "Great value for money.",
    "Wireless": "Works without cables.",
    "Refurbished": "Certified pre-owned.",
    "Clearance": "Final price reductions.",
    "Staff Pick": "Recommended by our team.",
    "Bundle": "Comes with useful extras.",
}

STATUS_WEIGHTS = {
    ProductStatus.ACTIVE: 70,
    ProductStatus.OUT_OF_STOCK: 10,
    ProductStatus.PREORDER: 8,
    ProductStatus.INACTIVE: 7,
    ProductStatus.DISCONTINUED: 5,
}


def seed_catalog():
    categories = [
        Category.objects.create(
            name=name,
            slug=slugify(name),
            description=paragraphs(description),
            is_active=name != "Photography",
        )
        for name, (description, *_) in CATEGORIES.items()
    ]

    tags = [
        Tag.objects.create(name=name, slug=slugify(name), description=paragraphs(text))
        for name, text in TAGS.items()
    ]

    used_names = set()
    products = []

    while len(products) < PRODUCT_COUNT:
        category = rng.choice(categories)
        _, nouns, (low, high) = CATEGORIES[category.name]
        name = f"{rng.choice(BRANDS)} {rng.choice(nouns)} {rng.choice(MODELS)}"

        if name in used_names:
            continue

        used_names.add(name)
        status = weighted(STATUS_WEIGHTS)
        released_at = timezone.localdate() - timedelta(days=rng.randint(-30, 900))
        price = Decimal(rng.randint(low, high)) - Decimal("0.01")

        products.append(
            Product(
                name=name,
                price=price,
                price_currency="EUR",
                status=status,
                category=category,
                description=paragraphs(
                    f"The {name} is part of our {category.name.lower()} range.",
                    "Designed for everyday use with a two year warranty included.",
                ),
                specification=paragraphs(
                    f"Weight: {rng.randint(50, 4000)} g",
                    f"Warranty: {rng.choice([12, 24, 36])} months",
                    f"Color: {rng.choice(['Black', 'Silver', 'White', 'Graphite', 'Blue'])}",
                ),
                dataset={
                    "name": rng.choice(BRANDS) + " Supplier",
                    "email": f"supply@{rng.choice(BRANDS).lower()}.example.com",
                    "age": rng.randint(1, 15),
                    "active": status == ProductStatus.ACTIVE,
                },
                released_at=released_at,
                discontinued_at=timezone.now() - timedelta(days=rng.randint(1, 120))
                if status == ProductStatus.DISCONTINUED
                else None,
                is_active=status in (ProductStatus.ACTIVE, ProductStatus.PREORDER),
            )
        )

    products = Product.objects.bulk_create(products)

    # bulk_update skips auto_now, so the catalog gets a believable history
    for product in products:
        product.created_at = past(720, 60)
        product.modified_at = past(60)
    Product.objects.bulk_update(products, ["created_at", "modified_at"])

    content_type = ContentType.objects.get_for_model(Product)
    TagRelation.objects.bulk_create(
        TagRelation(tag=tag, content_type=content_type, object_id=product.pk)
        for product in products
        for tag in rng.sample(tags, rng.randint(0, 3))
    )

    return products
