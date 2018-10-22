from django.core.management.base import BaseCommand

from respool.management.sample_data_creation import data_creator


class Command(BaseCommand):
    """Command for populating the database with users and items.
    Also uploads images and loan agreements"""

    help = "Creates sample data and inserts it to db"

    def handle(self, *args, **options):
        print("start importing data")
        data_creator.create()
        print("done importing data")
