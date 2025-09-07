from django.urls import path
from .views import subscriptions_home

urlpatterns = [
    path("", subscriptions_home, name="subscriptions_home"),
]
