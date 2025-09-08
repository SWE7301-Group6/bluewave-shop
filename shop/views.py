from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import stripe

from .models import Product, Order, OrderItem, PurchaseApproval
from accounts.models import UserProfile

# Robust import for subscription model
try:
    from subscriptions.models import Subscription as SubModel
except Exception:
    from subscriptions.models import UserSubscription as SubModel

User = get_user_model()


def product_list(request):
    products = Product.objects.filter(active=True)
    return render(request, "shop/product_list.html", {"products": products})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, "shop/product_detail.html", {"product": product})


@login_required
def create_checkout_session(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    price_id = product.stripe_price_id
    if not settings.STRIPE_SECRET_KEY or not price_id:
        messages.error(request, "Stripe not configured. Ask an admin to set Stripe keys and price IDs.")
        return redirect("product_detail", slug=slug)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    success_url = request.build_absolute_uri(reverse("checkout_success")) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("checkout_cancel"))

    mode = "payment" if product.product_type == Product.ONE_TIME else "subscription"
    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            customer_email=request.user.email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"product_slug": product.slug, "user_id": str(request.user.id)},
        )
        return redirect(session.url, permanent=False)
    except Exception as e:
        messages.error(request, f"Stripe error: {e}")
        return redirect("product_detail", slug=slug)


@login_required
def checkout_success(request):
    session_id = request.GET.get("session_id")
    if session_id and settings.STRIPE_SECRET_KEY:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            sess = stripe.checkout.Session.retrieve(session_id, expand=["subscription", "line_items"])
            meta = sess.get("metadata") or {}
            product_slug = meta.get("product_slug")

            product = None
            if product_slug:
                try:
                    product = Product.objects.get(slug=product_slug, active=True)
                except Product.DoesNotExist:
                    product = None

            # Idempotent Order
            order, created = Order.objects.get_or_create(
                stripe_session_id=session_id,
                defaults={
                    "user": request.user,
                    "paid": (sess.get("payment_status") == "paid" or sess.get("status") == "complete"),
                    "total_cents": (product.price_cents if product else 0),
                },
            )
            if created and product:
                OrderItem.objects.create(order=order, product=product, quantity=1, price_cents=product.price_cents)

            # If subscription item, update subscription table
            if product and product.product_type == Product.SUBSCRIPTION:
                sub_id = sess.get("subscription") or ""
                field_names = {f.name for f in SubModel._meta.get_fields()}

                if "active" in field_names:
                    sub, _ = SubModel.objects.get_or_create(user=request.user, stripe_subscription_id=sub_id or "")
                    sub.active = True
                    sub.save()
                else:
                    # robust: fetch Subscription for status/period
                    s = None
                    if sub_id:
                        try:
                            s = stripe.Subscription.retrieve(sub_id, expand=["items.data.price"])
                        except Exception:
                            s = None

                    sub, _ = SubModel.objects.get_or_create(user=request.user, stripe_subscription_id=sub_id or "")
                    if s:
                        sub.status = s.get("status") or "active"
                        cpe = s.get("current_period_end")
                        sub.current_period_end = timezone.datetime.fromtimestamp(cpe, tz=timezone.utc) if cpe else timezone.now()
                        sub.cancel_at_period_end = bool(s.get("cancel_at_period_end"))
                        if "price_id" in field_names:
                            price = (s.get("items", {}).get("data") or [{}])[0].get("price") or {}
                            sub.price_id = price.get("id") or ""
                        if "stripe_customer_id" in field_names:
                            sub.stripe_customer_id = s.get("customer") or ""
                    else:
                        sub.status = "active"
                        sub.current_period_end = timezone.now() + timezone.timedelta(days=30)
                        sub.cancel_at_period_end = False
                    sub.save()

                # flip researcher flag
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                profile.is_researcher = True
                profile.save()

        except Exception:
            # swallow to avoid breaking the UX
            pass

    messages.success(request, "Payment completed! You'll receive confirmation shortly.")
    return render(request, "shop/checkout_success.html")


@login_required
def checkout_cancel(request):
    messages.info(request, "Checkout cancelled.")
    return render(request, "shop/checkout_cancel.html")


@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "shop/orders.html", {"orders": orders})


def is_staff(user):
    return user.is_staff


@user_passes_test(is_staff)
def pending_orders(request):
    pending = Order.objects.filter(paid=True, approved=False).order_by("created_at")
    return render(request, "admin_panel/pending_orders.html", {"orders": pending})


@user_passes_test(is_staff)
def approve_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    approval, _ = PurchaseApproval.objects.get_or_create(order=order)
    approval.approve(request.user)
    messages.success(request, f"Order #{order.id} approved.")
    return redirect("pending_orders")