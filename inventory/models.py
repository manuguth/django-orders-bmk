from django.db import models

# Create your models here.


class Inventory(models.Model):

    time_slot = models.DateTimeField(max_length=220)
    day_slot = models.CharField(max_length=220)
    order_limit = models.IntegerField(default=25)
    received_orders = models.IntegerField(default=0)
    