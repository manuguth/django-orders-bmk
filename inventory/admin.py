from django.contrib import admin
from django.utils import timezone
# Register your models here.
import locale
from .models import Inventory

locale.setlocale(locale.LC_ALL, 'de_DE')

class InventoryAdmin(admin.ModelAdmin):
    def time_days(self, obj):
        # this converts to the correct tiem zone
        class_date = timezone.localtime(obj.time_slot)
        return class_date.strftime("%A %d. %B %H:%M")
    # TODO: switch to German 
    list_display = (#"time_slot",
                    "time_days",
                    "order_limit",
                    "received_orders")


admin.site.register(Inventory, InventoryAdmin)
