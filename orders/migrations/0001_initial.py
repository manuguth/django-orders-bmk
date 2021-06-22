# Generated by Django 3.0 on 2021-06-17 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=220)),
                ('email', models.EmailField(max_length=220)),
                ('phone', models.CharField(max_length=220)),
                ('comments', models.CharField(max_length=220)),
                ('time_slot', models.DateTimeField(max_length=220)),
                ('time_stamp', models.DateTimeField(max_length=220)),
            ],
        ),
    ]