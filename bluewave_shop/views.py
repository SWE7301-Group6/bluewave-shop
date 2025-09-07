# bluewave_shop/views.py
from django.shortcuts import render
from shop.models import Product

def home(request):
    # Show latest 6 products on the homepage
    products = Product.objects.order_by("-id")[:6]
    return render(request, "home.html", {"products": products})
