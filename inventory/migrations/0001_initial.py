# Generated by Django 3.2.4 on 2021-06-22 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_slot', models.DateTimeField(max_length=220)),
                ('order_limit', models.IntegerField(default=25)),
                ('received_orders', models.IntegerField(default=0)),
            ],
        ),
    ]
