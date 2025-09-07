from django.urls import path
from shop.views import pending_orders, approve_order

urlpatterns = [
    path('pending-orders/', pending_orders, name='pending_orders'),
    path('approve-order/<int:order_id>/', approve_order, name='approve_order'),
]
