from django.core.management.base import BaseCommand, CommandError
from products.models import Product
import yaml
from django.utils import timezone
from django.utils.dateparse import parse_datetime


class Command(BaseCommand):
    help = "Adds products using a yaml file"

    def add_arguments(self, parser):
        parser.add_argument('yaml', type=str)

    def handle(self, *args, **options):
        with open(options["yaml"]) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        for elem in data:
            title = elem["title"]
            if Product.objects.filter(title=title).exists():
                self.stdout.write(f"{title} already exists, skipping ...")
                continue

            product = Product(
                title = elem["title"],
                short_title = elem["short_title"],
                description = elem["description"],
                price = elem["price"],
                display_order = elem["display_order"],
                limit_per_timeslot = elem["limit_per_timeslot"],
                category = elem["category"],
            )
            product.save()
            self.stdout.write(self.style.SUCCESS(
                f"Adding product {title}"))
