import os
import subprocess
from django.contrib import admin
from django.utils import timezone
# Register your models here.
import locale
from .models import Inventory


if 'WEBSITE_HOSTNAME' not in os.environ:
    locale.setlocale(locale.LC_ALL, 'de_DE')
elif 'WEBSITE_HOSTNAME' in os.environ:
    bashCommand = "echo 'de_DE ISO-8859-1' >> /etc/locale.gen && locale-gen"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
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
