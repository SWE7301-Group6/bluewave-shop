from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_researcher = models.BooleanField(default=False)  # gets set true when a subscription activates
    totp_secret = models.CharField(max_length=64, blank=True, default="")
    totp_enabled = models.BooleanField(default=False)

    # API token issued by BlueWave API
    api_jwt = models.TextField(blank=True, default="")
    api_jwt_expires_at = models.DateTimeField(null=True, blank=True)

    def has_valid_api_token(self):
        return self.api_jwt and self.api_jwt_expires_at and self.api_jwt_expires_at > timezone.now()

    def __str__(self):
        return f"Profile<{self.user.username}>"
