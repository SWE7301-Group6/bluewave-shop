from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import stripe
from shop.models import Product, Order, OrderItem
from subscriptions.models import Subscription
from accounts.models import UserProfile
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest("Webhook secret not set")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid payload: {e}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        product_slug = session["metadata"].get("product_slug")
        user_id = int(session["metadata"].get("user_id"))
        user = User.objects.get(id=user_id)
        product = Product.objects.get(slug=product_slug)

        order = Order.objects.create(
            user=user,
            stripe_session_id=session["id"],
            paid=True,
            total_cents=product.price_cents,
        )
        OrderItem.objects.create(order=order, product=product, quantity=1, price_cents=product.price_cents)

        # For subscriptions, mark/create subscription and set researcher flag
        if product.product_type == Product.SUBSCRIPTION:
            sub_id = session.get("subscription", "")
            Subscription.objects.create(user=user, stripe_subscription_id=sub_id, active=True)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_researcher = True
            profile.save()

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        try:
            s = Subscription.objects.get(stripe_subscription_id=sub["id"])
            s.active = False
            s.canceled_at = timezone.now()
            s.save()
            profile, _ = UserProfile.objects.get_or_create(user=s.user)
            profile.is_researcher = False
            profile.save()
        except Subscription.DoesNotExist:
            pass

    return HttpResponse(status=200)
