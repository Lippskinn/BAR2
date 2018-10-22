from django.core.management.base import BaseCommand

from accounts.models import Borrower, Lender
from respool.models import Category, Dimension, Image, Item, LoanAgreement, Loan, Location, RentalFee, TimeInterval


class Command(BaseCommand):
    """
    Command for removing all content and users (except super users) from the db.
    """
    help = "Creates sample data and inserts it to db"

    def handle(self, *args, **options):
        print("Deleting item entries from db (excluding superusers)")
        borrowers = Borrower.objects.all()
        for borrower in borrowers:
            if not borrower.user.is_superuser:
                borrower.user.delete()
            borrower.delete()
        lenders = Lender.objects.all()
        for lender in lenders:
            if not lender.user.is_superuser:
                lender.user.delete()
            lender.delete()
        Item.objects.all().delete()
        Image.objects.all().delete()
        Dimension.objects.all().delete()
        Category.objects.all().delete()
        LoanAgreement.objects.all().delete()
        Loan.objects.all().delete()
        Location.objects.all().delete()
        RentalFee.objects.all().delete()
        TimeInterval.objects.all().delete()
        print("all items removed")
