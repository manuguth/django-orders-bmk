# Generated by Django 3.2.4 on 2021-07-04 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_order_order_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_summary',
            field=models.CharField(default='Test', max_length=400),
            preserve_default=False,
        ),
    ]
