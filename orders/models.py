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
    # time_stamp = models.DateTimeField(max_length=220)
    ordered_products = models.JSONField(default=dict)
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
    

    def calculate(self, save=False):
        if self.ordered_product != []:
            return {}
        total = 0
        for item in self.ordered_products:
            total += item['price']
        subtotal = Decimal(self.product.price)  # 29.99 -> 2999
        tax_rate = Decimal(0.12)  # 0.12 -> 12
        tax_total = subtotal * tax_rate  # 1.29 1.2900000003
        tax_total = Decimal("%.2f" % (tax_total))
        total = subtotal + tax_total
        total = Decimal("%.2f" % (total))
        print(total)
        totals = {
            "subtotal": subtotal,
            "tax": tax_total,
            "total": total
        }
        for k, v in totals.items():
            setattr(self, k, v)
            if save == True:
                self.save()
        return totals


# def order_pre_save(sender, instance, *args, **kwargs):
#     instance.calculate(save=False)


# pre_save.connect(order_pre_save, sender=Order)
