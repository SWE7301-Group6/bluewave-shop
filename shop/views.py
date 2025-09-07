from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Product, Order, OrderItem, PurchaseApproval
import stripe

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

# Admin panel views (simple examples)
def is_staff(user): return user.is_staff

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
