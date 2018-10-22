from django.contrib.auth.models import User
from django.db import models

from respool.models import Item, LoanAgreement, Location

'''Models for managing user accounts of the app'''
'''Authors: Michael Götz, Marius Hofmann'''

MAX_PHONE_NUMBER_LENGTH = 16
MAX_PHONE_NUMBER_MOBILE_LENGTH = 16
MAX_WEBSITE_LENGTH = 64
MAX_DESC_LENGTH = 1024


class Borrower(models.Model):
    """
    Represents a registered user which can only borrow items.
    Extends the django base user with 'phone number', 'mobile phone number' and a 'booked items' field.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=MAX_PHONE_NUMBER_LENGTH, blank=True, null=True)
    phone_number_mobile = models.CharField(max_length=MAX_PHONE_NUMBER_MOBILE_LENGTH, blank=True, null=True)
    booked_items = models.ManyToManyField(Item, blank=True)

    def __str__(self):
        return '{}'.format(self.user.username)


class Lender(models.Model):
    """
    Represents a registered user which can add new items to the resource pool.
    Extends the django base user with 'phone number', 'mobile phone number', 'website', 'type', 'description' and 'location' fields.
    """
    PRIVATE = 0
    ORGANIZATION = 1

    TYPE_CHOICES = ((PRIVATE, 'Privat'), (ORGANIZATION, 'Organisation'),)

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=MAX_PHONE_NUMBER_LENGTH, blank=True, null=True)
    phone_number_mobile = models.CharField(max_length=MAX_PHONE_NUMBER_MOBILE_LENGTH, blank=True, null=True)
    website = models.CharField(max_length=MAX_WEBSITE_LENGTH, blank=True, null=True)
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)
    description = models.TextField(max_length=MAX_DESC_LENGTH, blank=True, null=True)
    default_loan_agreement = models.ForeignKey(LoanAgreement, on_delete=models.PROTECT, blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        if self.type:
            return '{} - {}'.format(self.user.username, self.TYPE_CHOICES[self.type][1])
        else:
            return '{}'.format(self.user.username)
