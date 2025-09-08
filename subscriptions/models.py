from django.conf import settings
from django.db import models
from django.utils import timezone


class UserSubscription(models.Model):
    """
    Tracks a user's live Stripe subscription so API access can expire automatically.
    """
    STATUS_CHOICES = [
        ("incomplete", "incomplete"),
        ("incomplete_expired", "incomplete_expired"),
        ("trialing", "trialing"),
        ("active", "active"),
        ("past_due", "past_due"),
        ("canceled", "canceled"),
        ("unpaid", "unpaid"),
        ("paused", "paused"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=120, blank=True, default="")
    stripe_subscription_id = models.CharField(max_length=120, unique=True)
    price_id = models.CharField(max_length=120, blank=True, default="")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="incomplete")
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active_now(self) -> bool:
        """
        Active if status is active/trialing (optionally allow past_due as grace)
        AND we're still inside the current billing period.
        """
        if self.status in ("active", "trialing", "past_due"):
            return bool(self.current_period_end and self.current_period_end > timezone.now())
        return False

    def __str__(self):
        return f"{self.user} · {self.stripe_subscription_id} · {self.status}"

class Subscription(UserSubscription):
    class Meta:
        proxy = True