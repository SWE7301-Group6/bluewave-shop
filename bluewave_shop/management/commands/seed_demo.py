from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import Product

class Command(BaseCommand):
    help = "Create demo products and users"

    def handle(self, *args, **opts):
        # Users
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "Admin123!")
        if not User.objects.filter(username="customer").exists():
            User.objects.create_user("customer", "customer@example.com", "Customer123!")
        if not User.objects.filter(username="researcher").exists():
            User.objects.create_user("researcher", "researcher@example.com", "Researcher123!")

        # Products
        Product.objects.get_or_create(
            slug="micro-desalination-unit",
            defaults=dict(name="Micro‑desalination Unit", description="Compact solar‑powered unit.", price_cents=149900),
        )
        Product.objects.get_or_create(
            slug="data-subscription-pro",
            defaults=dict(name="Data Subscription — Pro", description="Real‑time + historical metrics.", price_cents=4900, product_type="SUBSCRIPTION"),
        )
        self.stdout.write(self.style.SUCCESS("Demo users and products created."))
