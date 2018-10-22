import logging
import os
import uuid
from datetime import datetime
from io import BytesIO

from PIL import Image as pil_image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.db.models import Max
from django.dispatch import receiver

from respool.utils import geocoding

logger = logging.getLogger(__name__)

'''Models for managing required data of the app'''
'''Authors: Michael Götz, Marius Hofmann'''

MAX_ITEM_TITLE_LENGTH = 64
MAX_ITEM_DESCRIPTION_LENGTH = 1024
MAX_CATEGORY_TITLE_LENGTH = 32
MAX_CATEGORY_TOKEN_LENGTH = 8
MAX_LOCATION_TITLE_LENGTH = 32
MAX_LOCATION_ADDRESS_LENGTH = 32

THUMB_SIZE = (320, 320)


class Item(models.Model):
    """
    Represents a single entry in the resource pool.
    Can be of one main type venue, service or object.
    Other fields are optional resp. required based on that type.
    """

    VENUE = 0
    SERVICE = 1
    OBJECT = 2

    TYPE_CHOICES = ((VENUE, 'Veranstaltungsort'), (SERVICE, 'Dienstleistung'), (OBJECT, 'Objekt'))

    title = models.CharField(max_length=MAX_ITEM_TITLE_LENGTH)
    description = models.TextField(max_length=MAX_ITEM_DESCRIPTION_LENGTH)
    type = models.IntegerField(choices=TYPE_CHOICES)
    categories = models.ManyToManyField('Category', blank=True)
    loan_agreement = models.ForeignKey('LoanAgreement', on_delete=models.SET_NULL, null=True, blank=True)
    images = models.ManyToManyField('Image', blank=True)
    location = models.ForeignKey('Location', on_delete=models.PROTECT)
    lender = models.ForeignKey('accounts.Lender', on_delete=models.CASCADE)
    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, blank=True, null=True)
    occupancies = models.ManyToManyField('TimeInterval', blank=True)
    dimension = models.ForeignKey('Dimension', on_delete=models.CASCADE, null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    amount = models.PositiveIntegerField(null=True, blank=True)

    def clean(self):
        """
        Overwritten default function for checking required fields based on Item Type.
        Called on save.
        """
        if self.type == Item.VENUE:
            if any([self.weight, self.amount]):
                raise ValidationError('Venue item cannot have the following attributes: weight, amount')
            if not all([self.dimension, ]):
                raise ValidationError('Venue item need value for attribute dimension')
        elif self.type == Item.SERVICE:
            if any([self.weight, self.amount, self.dimension]):
                raise ValidationError('Service item cannot have the following attributes: weight, amount, dimension')
        elif self.type == Item.OBJECT:
            if not all([self.dimension, self.amount, self.weight, ]):
                raise ValidationError('Object item need value for attributes: dimension, amount, weight')
        else:
            raise ValidationError('Unknown Item type')

    def __str__(self):
        return '{} - {}'.format(self.title, self.TYPE_CHOICES[self.type][1])


@receiver(models.signals.pre_delete, sender=Item)
def delete_referenced_files(sender, instance, *args, **kwargs):
    """
    Deletes Image instances when a Item is deleted.
    Called via receiver/signal on Item pre_delete

    :param sender: The Item model class that just had an instance created. Unused in this case.
    :param instance: Instance of the triggering Item model class.
    :param args: list of positional arguments passed to Item.__init__(). Unused in this case.
    :param kwargs: dictionary of keyword arguments passed to Item.__init__(). Unused in this case.
    :return:
    """
    for image in instance.images.all():
        image.delete()

    if instance.loan_agreement:
        try:
            instance.loan_agreement.delete()
        except models.ProtectedError:
            pass


class LoanAgreement(models.Model):
    """
    Holds a single file used as a loan agreement.
    Files are saved to an separate 'agreements' folder
    """
    file = models.FileField(upload_to='agreements/')

    def __str__(self):
        return '{}'.format(self.file.name)


@receiver(models.signals.post_delete, sender=LoanAgreement)
def delete_LoanAgreement(sender, instance, *args, **kwargs):
    """
    Deletes loanAgreement file from filesystem when LoanAgreement instance is deleted.
    Called via receiver/signal on LoanAgreement `post_delete`.
    Idea: https://stackoverflow.com/questions/33080360/how-to-delete-files-from-filesystem-using-post-delete-django-1-8

    :param sender: The LoanAgreement model class that just had an instance created. Unused in this case.
    :param instance: Instance of the triggering LoanAgreement model class.
    :param args: list of positional arguments passed to LoanAgreement.__init__(). Unused in this case.
    :param kwargs: dictionary of keyword arguments passed to LoanAgreement.__init__(). Unused in this case.
    :return:
    """
    if instance.file:
        if os.path.exists(instance.file.path):
            os.remove(instance.file.path)


class Category(models.Model):
    """
    Represents a single category which can be referenced by Item instance.
    """
    title = models.CharField(max_length=MAX_CATEGORY_TITLE_LENGTH)

    def __str__(self):
        return '{}'.format(self.title)


class Dimension(models.Model):
    """
    Wrapper to hold three Floats representing the extent/dimension of an Item
    """
    width = models.FloatField()
    height = models.FloatField()
    depth = models.FloatField()

    def __str__(self):
        return 'W {:10.3f} - H {:10.3f} - D {:10.3f}'.format(self.width, self.height, self.depth)


def image_path(instance, filename):
    """
    Returns the path for saving the file of an Image

    :param instance: Unused.
    :param filename: filename of the file to be saved
    :return: Path containing a subfolder 'images', the current date as a folder and an uuid as the image filename.
    """
    name, extension = os.path.splitext(filename)
    date = datetime.now().strftime('%Y/%m/%d')
    return 'item/images/{}/{}{}'.format(date, uuid.uuid4(), extension)


def thumb_path(instance, filename):
    """
    Returns the path for saving the thumb file of an Image

    :param instance: Unused.
    :param filename: filename of the file to be saved
    :return: Path containing a subfolder 'thumbs', the current date as a folder and an uuid as the image filename.
    """
    name, extension = os.path.splitext(filename)
    date = datetime.now().strftime('%Y/%m/%d')
    return 'item/thumbs/{}/{}{}'.format(date, uuid.uuid4(), extension)


class Image(models.Model):
    """
    Holds a single image, a thumbnail and an order id.
    """
    file = models.ImageField(upload_to=image_path)
    thumb = models.ImageField(upload_to=thumb_path, null=True, blank=True)
    order_id = models.PositiveSmallIntegerField()

    def __str__(self):
        return '{} - {}'.format(self.order_id, self.file.name)

    class Meta:
        # explicitly sort by order_id as it used for image ordering
        ordering = ['order_id']


@receiver(models.signals.pre_save, sender=Image)
def save_image(sender, instance, *args, **kwargs):
    """
    Creates a thumbnail for the image and saves it to the Image instance.
    Called via receiver/signal on Image `pre_save`
    """
    image = pil_image.open(instance.file)
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')
    image.thumbnail(THUMB_SIZE, pil_image.ANTIALIAS)

    # save the thumbnail to memory
    temp_handle = BytesIO()
    image.save(temp_handle, 'jpeg')
    temp_handle.seek(0)  # rewind the file

    # save to the thumbnail field
    instance.thumb = SimpleUploadedFile(os.path.split(instance.file.name)[-1],
                                        temp_handle.read(),
                                        content_type='image/jpg')


@receiver(models.signals.post_delete, sender=Image)
def delete_image(sender, instance, *args, **kwargs):
    """
    Deletes image files from the file system on Image `post_delete`
    Idea: https://stackoverflow.com/questions/33080360/how-to-delete-files-from-filesystem-using-post-delete-django-1-8
    """
    if instance.file and os.path.exists(instance.file.path):
        os.remove(instance.file.path)
    if instance.thumb and os.path.exists(instance.thumb.path):
        os.remove(instance.thumb.path)


def reset_image_order_ids(item):
    """
    Resets the order ids of all images of the given item from 1 to n.
    Used to remove gaps/jumps in the order ids, e.g. when a image is deleted.

    :param item: Item for which the order ids of the images should be reset.
    :return:
    """
    for index, image in enumerate(item.images.all()):
        image.order_id = index + 1
        image.save()


def get_next_order_id(item):
    """
    Returns the next order id to be used for an image for a given item.

    :param item: Item which a new image shall be added to.
    :return: The next order id to be used (current maximum order id + 1)
    """
    images = item.images.all()
    if not images:
        return 1
    return images.aggregate(Max('order_id')).get('order_id__max') + 1


class Location(models.Model):
    """
    Wrapper class for holding a single address and its coordinates.
    """
    title = models.CharField(max_length=MAX_LOCATION_TITLE_LENGTH, null=True, blank=True)
    house_number = models.PositiveIntegerField()
    street = models.CharField(max_length=MAX_LOCATION_ADDRESS_LENGTH)
    city = models.CharField(max_length=MAX_LOCATION_ADDRESS_LENGTH, default='Bamberg')
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return '{} {} - {}'.format(self.street, self.house_number, self.city)


@receiver(models.signals.pre_save, sender=Location)
def add_geocode(sender, instance, *args, **kwargs):
    """
    Adds the coordinates to a Location instance if not provided by the user.
    Uses address and geocode api to retrieve longitude and latitude for provided address.
    Called on Location 'pre_save'.

    :param sender: Unused.
    :param instance: Instance of the triggering Location model class.
    :param args: Unused.
    :param kwargs: Unused.
    :return:
    """
    # only get geocode from adress if not provided already
    if not instance.longitude or not instance.latitude:
        latitude, longitude = geocoding.getGeoCode(house_number=instance.house_number, street=instance.street,
                                                   city=instance.city)
        if latitude and longitude:
            instance.longitude = longitude
            instance.latitude = latitude


class Loan(models.Model):
    """
    Holds all financial aspects of lending an Item.
    Item is free if all fields are null/none.
    """
    caution = models.FloatField(blank=True, null=True)
    single_rent = models.FloatField(blank=True, null=True)
    rental_fee = models.ForeignKey('RentalFee', on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        if not (self.caution and self.rental_fee and self.single_rent):
            return "none/free"
        return 'caution: {} - single rent: {} - rental free: {}'.format(self.caution, self.single_rent,
                                                                        self.rental_fee.costs)


class RentalFee(models.Model):
    """
    Holds interval and costs for representing a reoccurring payment / rent.
    """
    HOURLY = 0
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3

    INTERVAL_UNIT_CHOICES = ((HOURLY, 'Stunde'), (DAILY, 'Tag'), (WEEKLY, 'Woche'), (MONTHLY, 'Monat'))

    interval_unit = models.IntegerField(choices=INTERVAL_UNIT_CHOICES)
    costs = models.FloatField()

    def __str__(self):
        return '{} € pro {}'.format(self.costs, self.INTERVAL_UNIT_CHOICES[self.interval_unit][1])


class TimeInterval(models.Model):
    """
    Wrapper class for representing a timespan from 'datetime a' to 'datetime b'
    """
    start_time = models.DateTimeField(blank=False, null=False)
    end_time = models.DateTimeField(blank=False, null=False)

    def clean(self):
        """Called on save. Ensures that end time is after start time, raises ValidationError otherwise"""
        if self.start_time.date() > self.end_time.date():
            raise ValidationError('The end time has be after the start time!')

    def __str__(self):
        return '{} - {}'.format(self.start_time.strftime('%d %b %Y %H:%M'), self.end_time.strftime('%d %b %Y %H:%M'))
