from django.core.management.base import BaseCommand, CommandError
from inventory.models import Inventory
import yaml
from django.utils import timezone
from django.utils.dateparse import parse_datetime


class Command(BaseCommand):
    help = 'Adds timeslots using a yaml file'

    def add_arguments(self, parser):
        parser.add_argument('yaml', type=str)
    
    def handle(self, *args, **options):
        with open(options['yaml']) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        for item in data:
            class_date = timezone.localtime(
            parse_datetime(item["time_slot"]))
            
            if Inventory.objects.filter(time_slot=class_date).exists():
                self.stdout.write(f'{class_date.strftime("%A %d. %B %H:%M")} already exists, skipping ...')
            else:
                inventory = Inventory(
                    time_slot=class_date,
                    day_slot=item["day_slot"],
                )
                inventory.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Adding timeslot {class_date.strftime("%A %d. %B %H:%M")}'))
