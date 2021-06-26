from django.db import models
from decimal import Decimal
from django.db.models.signals import pre_save



class Order(models.Model):
    
    time_stamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=220)
    email = models.EmailField(max_length=220)
    phone = models.CharField(max_length=220)
    comments = models.CharField(max_length=220)
    time_slot = models.DateTimeField(max_length=220)
    price_total = models.FloatField()
    ordered_products = models.JSONField(default=dict)
    n_ordered_products = models.IntegerField()
    order_hash = models.CharField(max_length=200)
    invoice = models.FileField()
    
    # ordered_products field
    # for sqlite only json Fields are possible
    # if using PostgreSQL, an ArrayField is available
    # https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/fields/#arrayfield
    # list of dictionary with keys:
    # {
        # "product": <unique_product_key>,
        # "price": <product_prize>,
        # "amount": <amount_of_ordered_product>,
        # <optional>:
        # "short_name": <short_name_for_labels>,
        # "short_name_w_n": <short_name_for_labels_with_amount>,
    # }
    # the ordered_products
    # mail, phone, comments, time slot, time stamp,
    
