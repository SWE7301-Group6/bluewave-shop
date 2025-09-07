from django.conf import settings
from django.db import models

class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    stripe_subscription_id = models.CharField(max_length=200, blank=True, default="")
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Subscription<{self.user.username}:{'active' if self.active else 'inactive'}>"
