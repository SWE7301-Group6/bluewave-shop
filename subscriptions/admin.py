# subscriptions/admin.py
from django.contrib import admin
from django.apps import apps
from django.utils import timezone
from accounts.models import UserProfile


def get_sub_model():
    """Return subscriptions.Subscription or subscriptions.UserSubscription (whichever exists)."""
    for name in ("Subscription", "UserSubscription"):
        try:
            return apps.get_model("subscriptions", name)
        except LookupError:
            continue
    raise LookupError("No Subscription or UserSubscription model found in 'subscriptions' app.")


SubModel = get_sub_model()
FIELD_NAMES = {f.name for f in SubModel._meta.get_fields()}
SIMPLE_SCHEMA = "active" in FIELD_NAMES  # simple == boolean 'active'; robust == 'status', 'current_period_end', ...


def user_still_active(user) -> bool:
    """Check if the user still has an active subscription (supports simple & robust schemas)."""
    qs = SubModel.objects.filter(user=user)
    if SIMPLE_SCHEMA:
        return qs.filter(active=True).exists()
    # robust schema
    now = timezone.now()
    return qs.filter(status__in=("active", "trialing"), current_period_end__gt=now).exists()


# ----- Admin configuration that adapts to available fields -----
_list_display = ["id", "user", "stripe_subscription_id"]
_list_filter = []
_search_fields = ["user__username", "user__email", "stripe_subscription_id"]

if SIMPLE_SCHEMA:
    # Simple schema (has 'active' boolean)
    _list_display.insert(2, "active")
    _list_filter.append("active")
else:
    # Robust schema fields (add only if present)
    if "status" in FIELD_NAMES:
        _list_display.insert(2, "status")
        _list_filter.append("status")
    if "current_period_end" in FIELD_NAMES:
        _list_display.append("current_period_end")
    if "price_id" in FIELD_NAMES:
        _list_display.append("price_id")
    if "stripe_customer_id" in FIELD_NAMES:
        _list_display.append("stripe_customer_id")
    if "updated_at" in FIELD_NAMES:
        _list_display.append("updated_at")


@admin.register(SubModel)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = _list_display
    list_filter = _list_filter
    search_fields = _search_fields
    ordering = ("-id",)

    def delete_queryset(self, request, queryset):
        affected_users = {obj.user for obj in queryset}
        super().delete_queryset(request, queryset)
        # After deletion, clear researcher flag only if no other active subs remain
        for u in affected_users:
            if not user_still_active(u):
                profile, _ = UserProfile.objects.get_or_create(user=u)
                profile.is_researcher = False
                profile.save()

    def delete_model(self, request, obj):
        u = obj.user
        super().delete_model(request, obj)
        if not user_still_active(u):
            profile, _ = UserProfile.objects.get_or_create(user=u)
            profile.is_researcher = False
            profile.save()
