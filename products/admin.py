from django.contrib import admin

# Register your models here.


from .models import Product


class ProductAdmin(admin.ModelAdmin):  
    list_display = ('title', 'price', 'display_order')


admin.site.register(Product, ProductAdmin)
