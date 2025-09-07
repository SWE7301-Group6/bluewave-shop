from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from bluewave_shop.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('shop/', include('shop.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('metrics/', include('metrics.urls')),
    path('payments/', include('payments.urls')),
    path('admin-panel/', include('bluewave_shop.admin_panel_urls')),
]
