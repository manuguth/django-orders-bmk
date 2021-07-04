from django.db import models
from decimal import Decimal
from django.db.models.signals import pre_save, post_save
from products.models import Product



class Order(models.Model):
    
    time_stamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=220)
    email = models.EmailField(max_length=220)
    phone = models.CharField(max_length=220)
    comments = models.CharField(max_length=220)
    time_slot = models.DateTimeField(max_length=220)
    price_total = models.FloatField()
    ordered_products = models.JSONField(default=dict)
    order_summary = models.CharField(max_length=400)
    n_ordered_products = models.IntegerField()
    order_hash = models.CharField(max_length=200)
    order_type = models.CharField(max_length=200, default="portal")
    
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
    def calculate(self):
        price = 0 
        products = 0 
        summary = []
        for item in self.ordered_products:
            if self.ordered_products[item] is None:
                continue
            price += self.ordered_products[item] * Product.objects.get(short_title=item).price
            products += self.ordered_products[item]
            summary.append(f"{item}({self.ordered_products[item]}x)")
        summary = ', '.join(summary)
        setattr(self, "price_total", price)
        setattr(self, "n_ordered_products", products)
        setattr(self, "order_summary", summary)
        if summary != self.order_summary:
            self.save()
        return price, products, summary
    

def order_post_save(sender, instance, *args, **kwargs):
    instance.calculate()

post_save.connect(order_post_save, sender=Order)
