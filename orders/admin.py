from django.contrib import admin

# Register your models here.

from .models import Order


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'time_slot',
        'price_total',
        'ordered_products',
    )

admin.site.register(Order, OrderAdmin)
