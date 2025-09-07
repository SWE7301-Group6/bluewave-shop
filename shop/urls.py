from django.urls import path
from .views import product_list, product_detail, create_checkout_session, checkout_success, checkout_cancel, orders_view

urlpatterns = [
    path("", product_list, name="product_list"),
    path("orders/", orders_view, name="orders"),
    path("<slug:slug>/checkout/", create_checkout_session, name="create_checkout_session"),
    path("success/", checkout_success, name="checkout_success"),
    path("cancel/", checkout_cancel, name="checkout_cancel"),
    path("<slug:slug>/", product_detail, name="product_detail"),
]
