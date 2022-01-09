from django.db import models


class Product(models.Model):
    FOOD = 'food'
    DRINKS = 'drinks'
    CATEGORY_CHOICES = [
        (FOOD, 'Essen'),
        (DRINKS, 'Getraenke'),
    ]
    title = models.CharField(max_length=220)
    # for labeling
    short_title = models.CharField(max_length=220)
    description = models.CharField(max_length=220)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    display_order = models.IntegerField(null=True, blank=True, default=0)
    # limit per time slot - optional
    limit_per_timeslot = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=220, choices=CATEGORY_CHOICES,
                                default=FOOD,)
    # category
    # integer field for Camembert, Pommes, Steak, Spargel
