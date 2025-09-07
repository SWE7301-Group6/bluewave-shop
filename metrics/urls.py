from django.urls import path
from .views import dashboard, metrics_proxy

urlpatterns = [
    path("dashboard/", dashboard, name="metrics_dashboard"),
    path("proxy/", metrics_proxy, name="metrics_proxy"),
]
