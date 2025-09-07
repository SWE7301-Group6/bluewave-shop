from django.core.management.base import BaseCommand
from django.utils.text import slugify
from decimal import Decimal
from shop.models import Product

# One subscription + five one-time products
CATALOG = [
    {
        "name": "Researcher Data Subscription (Processed)",
        "type": Product.SUBSCRIPTION,
        "price_gbp": Decimal("49.00"),
        "description": "Monthly access to processed, analytics-ready environmental metrics via the BlueWave API.",
    },
    {
        "name": "BlueWave Micro-Desal S1 (Solar Buoy)",
        "type": Product.ONE_TIME,
        "price_gbp": Decimal("3499.00"),
        "description": "Solar-powered micro-desalination buoy for off-grid coastal sites.",
    },
    {
        "name": "SWRO-5K Seawater RO (5,000 GPD)",
        "type": Product.ONE_TIME,
        "price_gbp": Decimal("18999.00"),
        "description": "Compact seawater reverse osmosis skid with energy recovery.",
    },
    {
        "name": "Under-sink RO (Household)",
        "type": Product.ONE_TIME,
        "price_gbp": Decimal("399.00"),
        "description": "Five-stage under-sink RO for homes and clinics.",
    },
    {
        "name": "Water Softener 48k Grain",
        "type": Product.ONE_TIME,
        "price_gbp": Decimal("749.00"),
        "description": "Ion-exchange softener to protect plumbing and appliances from scale.",
    },
    {
        "name": "Pretreatment Skid (MMF + Carbon)",
        "type": Product.ONE_TIME,
        "price_gbp": Decimal("5499.00"),
        "description": "Multimedia + activated carbon filtration skid to condition RO feedwater.",
    },
]


class Command(BaseCommand):
    help = "Seed 1 subscription + 5 desalination/softener products (uses price_cents). Idempotent."

    def handle(self, *args, **kwargs):
        created, updated = 0, 0
        # Create/update the catalog
        seeded_slugs = set()

        for item in CATALOG:
            name = item["name"]
            slug = slugify(name)
            seeded_slugs.add(slug)

            price_cents = int(item["price_gbp"] * 100)  # store in pence
            defaults = {
                "name": name,
                "description": item["description"],
                "price_cents": price_cents,
                "product_type": item["type"],
                "active": True,
            }

            obj, was_created = Product.objects.get_or_create(slug=slug, defaults=defaults)
            if was_created:
                created += 1
            else:
                # Update core fields but DO NOT overwrite a non-empty stripe_price_id
                dirty = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        dirty = True

                # Never clobber stripe_price_id if already set in DB
                # (Leave it as-is; fill via Admin if needed)
                if dirty:
                    obj.save()
                    updated += 1

        # Ensure only this subscription stays active (optional, since you said one subscription)
        # Deactivate any other SUBSCRIPTION products not in our seeded_slugs
        sub_qs = Product.objects.filter(product_type=Product.SUBSCRIPTION).exclude(slug__in=seeded_slugs)
        deactivated = sub_qs.update(active=False)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. Created: {created}, Updated: {updated}, Deactivated other subscriptions: {deactivated}"
        ))
