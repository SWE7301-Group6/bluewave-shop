from django.contrib import admin
from .models import Product, Order, OrderItem, PurchaseApproval

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_type", "price_cents", "active")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_cents", "paid", "approved", "created_at")
    inlines = [OrderItemInline]

admin.site.register(PurchaseApproval)
