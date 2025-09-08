from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import stripe
from django.utils import timezone

from shop.models import Product, Order, OrderItem
from accounts.models import UserProfile
from django.contrib.auth import get_user_model

# Robust import
try:
    from subscriptions.models import Subscription as SubModel
except Exception:
    from subscriptions.models import UserSubscription as SubModel

User = get_user_model()


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest("Webhook secret not set")
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid payload: {e}")

    # Make sure key is set before any API calls
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        product_slug = (session.get("metadata") or {}).get("product_slug")
        user_id = (session.get("metadata") or {}).get("user_id")
        try:
            user = User.objects.get(id=int(user_id))
        except Exception:
            return HttpResponse(status=200)  # ignore silently

        try:
            product = Product.objects.get(slug=product_slug)
        except Product.DoesNotExist:
            product = None

        # Idempotent order creation
        order, created = Order.objects.get_or_create(
            stripe_session_id=session["id"],
            defaults={
                "user": user,
                "paid": (session.get("payment_status") == "paid" or session.get("status") == "complete"),
                "total_cents": (product.price_cents if product else 0),
            },
        )
        if created and product:
            OrderItem.objects.create(order=order, product=product, quantity=1, price_cents=product.price_cents)

        # If subscription product, update subscription table + flag
        if product and product.product_type == Product.SUBSCRIPTION:
            sub_id = session.get("subscription") or ""
            field_names = {f.name for f in SubModel._meta.get_fields()}

            if "active" in field_names:
                # Simple schema
                sub, _ = SubModel.objects.get_or_create(user=user, stripe_subscription_id=sub_id or "")
                sub.active = True
                sub.save()
            else:
                # Robust schema: fetch Subscription from Stripe for status/periods
                if sub_id:
                    try:
                        s = stripe.Subscription.retrieve(sub_id, expand=["items.data.price"])
                    except Exception:
                        s = None
                else:
                    s = None

                sub, _ = SubModel.objects.get_or_create(user=user, stripe_subscription_id=sub_id or "")
                if s:
                    sub.status = s.get("status") or "active"
                    cpe = s.get("current_period_end")
                    sub.current_period_end = timezone.datetime.fromtimestamp(cpe, tz=timezone.utc) if cpe else timezone.now()
                    sub.cancel_at_period_end = bool(s.get("cancel_at_period_end"))
                    # optional if your model has these:
                    if "price_id" in field_names:
                        price = (s.get("items", {}).get("data") or [{}])[0].get("price") or {}
                        sub.price_id = price.get("id") or ""
                    if "stripe_customer_id" in field_names:
                        sub.stripe_customer_id = s.get("customer") or ""
                else:
                    # minimal fallback
                    sub.status = "active"
                    sub.current_period_end = timezone.now() + timezone.timedelta(days=30)
                    sub.cancel_at_period_end = False
                sub.save()

            # flip researcher flag for API gate
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_researcher = True
            profile.save()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.updated"):
        s = event["data"]["object"]
        sub_id = s.get("id")
        field_names = {f.name for f in SubModel._meta.get_fields()}
        try:
            sub = SubModel.objects.get(stripe_subscription_id=sub_id)
        except SubModel.DoesNotExist:
            return HttpResponse(status=200)

        if "active" in field_names:
            # Simple schema
            sub.active = (s.get("status") in ("active", "trialing"))
            sub.save()
            if not sub.active:
                profile, _ = UserProfile.objects.get_or_create(user=sub.user)
                profile.is_researcher = False
                profile.save()
        else:
            # Robust schema
            sub.status = s.get("status") or "canceled"
            cpe = s.get("current_period_end")
            sub.current_period_end = timezone.datetime.fromtimestamp(cpe, tz=timezone.utc) if cpe else sub.current_period_end
            sub.cancel_at_period_end = bool(s.get("cancel_at_period_end"))
            sub.save()

            if sub.status not in ("active", "trialing"):
                profile, _ = UserProfile.objects.get_or_create(user=sub.user)
                profile.is_researcher = False
                profile.save()

    return HttpResponse(status=200)