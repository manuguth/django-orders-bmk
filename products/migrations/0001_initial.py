# Generated by Django 3.0 on 2021-06-17 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=220)),
                ('short_title', models.CharField(max_length=220)),
                ('description', models.CharField(max_length=220)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('limit_per_timeslot', models.IntegerField(blank=True, null=True)),
                ('category', models.CharField(choices=[('food', 'Essen'), ('drinks', 'Getraenke')], default='food', max_length=220)),
            ],
        ),
    ]
