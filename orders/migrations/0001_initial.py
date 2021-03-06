# Generated by Django 3.2.4 on 2021-06-22 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_stamp', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=220)),
                ('email', models.EmailField(max_length=220)),
                ('phone', models.CharField(max_length=220)),
                ('comments', models.CharField(max_length=220)),
                ('time_slot', models.DateTimeField(max_length=220)),
                ('ordered_products', models.JSONField(default=dict)),
            ],
        ),
    ]
