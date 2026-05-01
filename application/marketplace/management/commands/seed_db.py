# marketplace/management/commands/seed_db.py
# Seeds the database with sample data for VP testing.
# Run with: python manage.py seed_db
# CSC 648-848 Spring 2026 - Team 17

from django.core.management.base import BaseCommand
from marketplace.models import Role, User, Category, Listing


CATEGORIES = [
    ("Textbooks", "Textbooks and course materials"),
    ("Electronics", "Electronic devices and accessories"),
    ("Furniture", "Furniture and home goods"),
    ("Clothing", "Clothing and accessories"),
    ("Services", "Student services and tutoring"),
    ("Other", "Other items"),
]

INTENT_MAP = {"active": "for_sale", "inactive": "wanted"}

SEED_LISTINGS = [
    # Textbooks
    {
        "title": "Calculus: Early Transcendentals",
        "description": "8th edition by James Stewart. Good condition, some highlights. Perfect for MATH 226.",
        "price": 35.00,
        "category": "Textbooks",
        "listing_type": "product",
        "condition": "Good",
        "status": "active",
    },
    {
        "title": "Introduction to Computer Science Textbook",
        "description": "Need Introduction to Computer Science by Schneider and Gersting, any edition.",
        "price": 20.00,
        "category": "Textbooks",
        "listing_type": "product",
        "condition": "Good",
        "status": "active",
    },
    # Electronics
    {
        "title": "Sony WH-1000XM4 Headphones",
        "description": "Sony WH-1000XM4 noise-cancelling headphones. Used for one semester, great condition.",
        "price": 120.00,
        "category": "Electronics",
        "listing_type": "product",
        "condition": "Like New",
        "status": "active",
    },
    {
        "title": "LED Desk Lamp with USB Charging",
        "description": "LED desk lamp with USB charging port. Adjustable brightness. Works great.",
        "price": 15.00,
        "category": "Electronics",
        "listing_type": "product",
        "condition": "Good",
        "status": "active",
    },
    # Furniture
    {
        "title": "Folding Desk Chair",
        "description": "Comfortable padded folding chair, perfect for dorm rooms. Lightly used.",
        "price": 25.00,
        "category": "Furniture",
        "listing_type": "product",
        "condition": "Good",
        "status": "active",
    },
    {
        "title": "IKEA Desk - White",
        "description": "IKEA LINNMON desk, 59 inch. White. Barely used. Must pick up on campus.",
        "price": 45.00,
        "category": "Furniture",
        "listing_type": "product",
        "condition": "Like New",
        "status": "active",
    },
    # Clothing
    {
        "title": "SFSU Gators Hoodie - Size M",
        "description": "Official SFSU hoodie, size M. Worn a few times, great condition.",
        "price": 20.00,
        "category": "Clothing",
        "listing_type": "product",
        "condition": "Good",
        "status": "active",
    },
    {
        "title": "Looking for XL SFSU Jacket",
        "description": "Looking for any SFSU branded jacket in XL size. Willing to pay up to $40.",
        "price": 40.00,
        "category": "Clothing",
        "listing_type": "product",
        "condition": "Good",
        "status": "active",
    },
    # Services
    {
        "title": "Graphic Design Help",
        "description": "SFSU design student offering logo design, flyers, and presentation decks. Fast turnaround.",
        "price": 25.00,
        "category": "Services",
        "listing_type": "service",
        "condition": "New",
        "status": "active",
    },
    {
        "title": "Math Tutoring - Calculus & Linear Algebra",
        "description": "PhD student offering tutoring for MATH 226, 227, and 325. $20/hr or $35 for 2hrs.",
        "price": 20.00,
        "category": "Services",
        "listing_type": "service",
        "condition": "New",
        "status": "active",
    },
    # Other
    {
        "title": "Trek FX3 Hybrid Bike 2022",
        "description": "2022 Trek FX3 hybrid bike, barely used. Perfect for commuting to SFSU.",
        "price": 350.00,
        "category": "Other",
        "listing_type": "product",
        "condition": "Like New",
        "status": "active",
    },
    {
        "title": "Looking for Mini Fridge",
        "description": "Need a small mini fridge for dorm room, around 1.7-3.0 cubic ft. Budget $50.",
        "price": 50.00,
        "category": "Other",
        "listing_type": "product",
        "condition": "Good",
        "status": "active",
    },
]


class Command(BaseCommand):
    help = "Seeds the database with sample listings for VP testing."

    def handle(self, *args, **kwargs):
        # Create roles
        student_role, _ = Role.objects.get_or_create(role_name="student")

        # Create a seed seller user with hashed password
        seller, created = User.objects.get_or_create(
            sfsu_email="seed_seller@sfsu.edu",
            defaults={
                "first_name": "Seed",
                "last_name": "Seller",
                "role": student_role,
                "password_hash": "temp",
                "account_status": "active",
            }
        )
        if created:
            seller.set_password("SeedPass123!")
            seller.save()

        if Listing.objects.exists():
            self.stdout.write(self.style.WARNING("DB already has listings. Skipping seed."))
            return

        # Create categories
        cat_map = {}
        for name, desc in CATEGORIES:
            cat, _ = Category.objects.get_or_create(category_name=name, defaults={"category_description": desc})
            cat_map[name] = cat

        # Create listings
        for data in SEED_LISTINGS:
            Listing.objects.create(
                title=data["title"],
                description=data["description"],
                price=data["price"],
                listing_type=data["listing_type"],
                condition=data["condition"],
                intent=INTENT_MAP.get(data["status"], "for_sale"),
                category=cat_map[data["category"]],
                seller=seller,
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(SEED_LISTINGS)} listings successfully."))
