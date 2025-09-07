from django.conf import settings
from django.db import models
from django.utils import timezone

class Product(models.Model):
    ONE_TIME = "ONE_TIME"
    SUBSCRIPTION = "SUBSCRIPTION"
    PRODUCT_TYPES = [(ONE_TIME, "One‑time"), (SUBSCRIPTION, "Subscription")]
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price_cents = models.PositiveIntegerField(default=0)  # used as fallback when not using Stripe Price
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default=ONE_TIME)
    stripe_price_id = models.CharField(max_length=100, blank=True, default="")  # required for live checkout
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_session_id = models.CharField(max_length=200, blank=True, default="")
    total_cents = models.PositiveIntegerField(default=0)
    paid = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)  # admin marks true upon fulfillment
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_cents = models.PositiveIntegerField(default=0)  # snapshot

class PurchaseApproval(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="approval")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def approve(self, user):
        self.approved_by = user
        self.approved_at = timezone.now()
        self.order.approved = True
        self.order.save()
        self.save()
