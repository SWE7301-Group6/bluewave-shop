from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Kept for compatibility; we also compute access from live Stripe status:
    is_researcher = models.BooleanField(default=False)

    totp_secret = models.CharField(max_length=64, blank=True, default="")
    totp_enabled = models.BooleanField(default=False)

    # API token issued by BlueWave API
    api_jwt = models.TextField(blank=True, default="")
    api_jwt_expires_at = models.DateTimeField(null=True, blank=True)

    def has_valid_api_token(self):
        return bool(self.api_jwt and self.api_jwt_expires_at and self.api_jwt_expires_at > timezone.now())

    @property
    def has_active_subscription(self) -> bool:
        """
        True if the user has an active (or trialing/past_due) subscription whose period hasn't ended.
        """
        try:
            from subscriptions.models import UserSubscription
            return UserSubscription.objects.filter(
                user=self.user,
                status__in=["active", "trialing", "past_due"],
                current_period_end__gt=timezone.now(),
            ).exists()
        except Exception:
            return False

    def __str__(self):
        return f"Profile<{self.user.username}>"
