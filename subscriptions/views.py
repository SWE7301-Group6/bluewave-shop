from django.shortcuts import render
from shop.models import Product

def subscriptions_home(request):
    subs = Product.objects.filter(product_type=Product.SUBSCRIPTION, active=True)
    return render(request, "subscriptions/subscribe.html", {"subs": subs})
