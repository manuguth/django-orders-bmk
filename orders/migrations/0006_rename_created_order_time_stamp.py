# Generated by Django 3.2.4 on 2021-06-20 19:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_alter_order_ordered_products'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='created',
            new_name='time_stamp',
        ),
    ]
