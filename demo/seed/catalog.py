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

# German translations for modeltranslation fields: name -> (name, description)
CATEGORIES_DE = {
    "Laptops": ("Laptops", "Tragbare Computer für Arbeit und Freizeit."),
    "Smartphones": ("Smartphones", "Telefone mit neuesten Kameras und Chips."),
    "Audio": ("Audio", "Kopfhörer, Ohrhörer und Lautsprecher."),
    "Wearables": ("Wearables", "Uhren und Fitness-Tracker."),
    "Home Office": ("Homeoffice", "Möbel und Zubehör für produktive Tage."),
    "Gaming": ("Gaming", "Konsolen, Controller und Zubehör."),
    "Smart Home": ("Smart Home", "Vernetzte Geräte für jeden Raum."),
    "Photography": ("Fotografie", "Kameras, Objektive und Stative."),
    "Networking": ("Netzwerk", "Router, Mesh-Systeme und Switches."),
    "Accessories": ("Zubehör", "Kabel, Ladegeräte und Hüllen."),
}

TAGS_DE = {
    "Bestseller": ("Bestseller", "Die meistverkauften Produkte der Saison."),
    "New Arrival": ("Neuheit", "Kürzlich ins Sortiment aufgenommen."),
    "Eco Friendly": ("Umweltfreundlich", "Aus recycelten Materialien hergestellt."),
    "Limited Edition": ("Limitierte Edition", "Nur solange der Vorrat reicht."),
    "Gift Idea": ("Geschenkidee", "Beliebte Wahl für Geschenke."),
    "Premium": ("Premium", "Spitzenqualität und hochwertige Materialien."),
    "Budget": ("Preiswert", "Viel Leistung fürs Geld."),
    "Wireless": ("Kabellos", "Funktioniert ohne Kabel."),
    "Refurbished": ("Generalüberholt", "Geprüfte Gebrauchtware."),
    "Clearance": ("Abverkauf", "Letzte Preisreduzierungen."),
    "Staff Pick": ("Team-Tipp", "Von unserem Team empfohlen."),
    "Bundle": ("Paket", "Mit nützlichen Extras."),
}

COLORS = {
    "Black": "Schwarz",
    "Silver": "Silber",
    "White": "Weiß",
    "Graphite": "Graphit",
    "Blue": "Blau",
}

STATUS_WEIGHTS = {
    ProductStatus.ACTIVE: 70,
    ProductStatus.OUT_OF_STOCK: 10,
    ProductStatus.PREORDER: 8,
    ProductStatus.INACTIVE: 7,
    ProductStatus.DISCONTINUED: 5,
}


def seed_catalog():
    # Both languages are set explicitly: `name=` would only fill the active one
    categories = {
        name: Category.objects.create(
            name_en=name,
            name_de=CATEGORIES_DE[name][0],
            slug=slugify(name),
            description_en=paragraphs(description),
            description_de=paragraphs(CATEGORIES_DE[name][1]),
            is_active=name != "Photography",
        )
        for name, (description, *_) in CATEGORIES.items()
    }

    tags = [
        Tag.objects.create(
            name_en=name,
            name_de=TAGS_DE[name][0],
            slug=slugify(name),
            description_en=paragraphs(text),
            description_de=paragraphs(TAGS_DE[name][1]),
        )
        for name, text in TAGS.items()
    ]

    used_names = set()
    products = []

    while len(products) < PRODUCT_COUNT:
        key = rng.choice(list(categories))
        category = categories[key]
        _, nouns, (low, high) = CATEGORIES[key]
        name = f"{rng.choice(BRANDS)} {rng.choice(nouns)} {rng.choice(MODELS)}"

        if name in used_names:
            continue

        used_names.add(name)
        status = weighted(STATUS_WEIGHTS)
        released_at = timezone.localdate() - timedelta(days=rng.randint(-30, 900))
        price = Decimal(rng.randint(low, high)) - Decimal("0.01")
        weight, warranty = rng.randint(50, 4000), rng.choice([12, 24, 36])
        color = rng.choice(list(COLORS))

        products.append(
            Product(
                name_en=name,
                name_de=name,
                price=price,
                price_currency="EUR",
                status=status,
                category=category,
                description_en=paragraphs(
                    f"The {name} is part of our {key.lower()} range.",
                    "Designed for everyday use with a two year warranty included.",
                ),
                description_de=paragraphs(
                    f"{name} gehört zu unserem Sortiment {CATEGORIES_DE[key][0]}.",
                    "Für den täglichen Einsatz, inklusive zwei Jahren Garantie.",
                ),
                specification_en=paragraphs(
                    f"Weight: {weight} g",
                    f"Warranty: {warranty} months",
                    f"Color: {color}",
                ),
                specification_de=paragraphs(
                    f"Gewicht: {weight} g",
                    f"Garantie: {warranty} Monate",
                    f"Farbe: {COLORS[color]}",
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
