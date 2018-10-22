from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.reverse import reverse

from accounts.models import Lender
from respool.models import Item, Dimension, LoanAgreement, Image, Location, Loan, RentalFee, Category, TimeInterval

'''
Author: Michael Götz, Marius Hofmann
'''


class DefaultItemImageSerializer(serializers.Serializer):
    """
        serialize image url
    """
    image = serializers.URLField()


class DimensionSerializer(serializers.ModelSerializer):
    """
        serialize dimension
         width, height, depth
    """

    class Meta:
        model = Dimension
        fields = ('width', 'height', 'depth')


class LoanAgreementSerializer(serializers.ModelSerializer):
    """
        serialize a loanagreement file
    """

    class Meta:
        model = LoanAgreement
        fields = ('file',)


class DefaultImageThumbSerializer(serializers.ModelSerializer):
    """
        serializes a image with thumb
    """

    class Meta:
        model = Image
        fields = ('thumb', 'file')


class TinyItemSerializer(serializers.HyperlinkedModelSerializer):
    """
        serialize item:
         id, title
    """

    class Meta:
        model = Item
        fields = ('id', 'title',)


class MinimalItemSerializer(serializers.HyperlinkedModelSerializer):
    """
        generate the detail page url and returns the first priotized image as default image.

        serialize item
         'id', 'title', 'description', 'default_image', 'detail_page_url'
    """
    default_image = serializers.SerializerMethodField()
    detail_page_url = serializers.SerializerMethodField('get_detail_item_url')

    def get_detail_item_url(self, instance):
        return reverse('respool:item-detail', [instance.id], request=self.context['request'])

    def get_default_image(self, instance):
        image = instance.images.all().first()
        if image:
            return DefaultImageThumbSerializer(image).data
        return None

    class Meta:
        model = Item
        fields = ('id', 'title', 'description', 'default_image', 'detail_page_url')


class LocationLongitudeLatitudeSerializer(serializers.ModelSerializer):
    """
        serialize location:
         latitude, longitude
    """

    class Meta:
        model = Location
        fields = ('latitude', 'longitude')


class LocationSerializer(serializers.ModelSerializer):
    """
     serialize location:
      'title', 'house_number', 'street', 'city', 'latitude', 'longitude'
    """

    class Meta:
        model = Location
        fields = ('title', 'house_number', 'street', 'city', 'latitude', 'longitude')


class UserSerializer(serializers.ModelSerializer):
    """
        serialize user:
         username, first_name, last_name
    """

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')


class LenderSerializer(serializers.ModelSerializer):
    """
        serialize lender:
         id, user('username', 'first_name', 'last_name')
    """
    user = UserSerializer(many=False, read_only=True)

    class Meta:
        model = Lender
        fields = ('id', 'user')


class RentalFeeSerializer(serializers.ModelSerializer):
    """
        serialize rentalfee:
         interval_unit, costs
    """

    class Meta:
        model = RentalFee
        fields = ('interval_unit', 'costs')


class RentalFeeChoicesSerializer(serializers.Serializer):
    """
        serialize a rental fee intervall unit
    """
    id = serializers.CharField()
    title = serializers.CharField()


class LoanSerializer(serializers.ModelSerializer):
    """
        serialize rental fee:
         'caution', 'single_rent', 'rental_fee'('interval_unit', 'costs')
    """
    rental_fee = RentalFeeSerializer(many=False, read_only=True)

    class Meta:
        model = Loan
        fields = ('caution', 'single_rent', 'rental_fee')


class CategorySerializer(serializers.ModelSerializer):
    """
        serialize a single category:
         id, title
    """

    class Meta:
        model = Category
        fields = ('id', 'title')


class TimeIntervalSerializer(serializers.ModelSerializer):
    """
        serialize time intervall:
         'start_time', 'end_time'
    """

    class Meta:
        model = TimeInterval
        fields = ('start_time', 'end_time')


class ItemSerializer(serializers.ModelSerializer):
    """
        serialize item:
         'id', 'title', 'description', 'dimension'('width', 'height', 'depth'), 'weight', 'amount', 'type', 'loan_agreement', 'images',
            'location'('title', 'house_number', 'street', 'city', 'latitude', 'longitude'), 'lender'('id', 'user'), 'lending'('caution', 'single_rent', 'rental_fee'), 'occupancies'[('start_time', 'end_time')]
    """
    dimension = DimensionSerializer(many=False, read_only=True)
    loan_agreement = LoanAgreementSerializer(many=False, read_only=True)
    images = DefaultImageThumbSerializer(many=True, read_only=True)
    location = LocationSerializer(many=False, read_only=True)
    lender = LenderSerializer(many=False, read_only=True)
    lending = LoanSerializer(many=False, read_only=True)
    occupancies = TimeIntervalSerializer(many=True, read_only=True)

    class Meta:
        model = Item
        fields = (
            'id', 'title', 'description', 'dimension', 'weight', 'amount', 'type', 'loan_agreement', 'images',
            'location', 'lender', 'lending', 'occupancies')


class ItemLocationSerializer(serializers.ModelSerializer):
    """
        serialize item:
         'id', 'title', 'location'
    """
    location = LocationSerializer(many=False, read_only=True)

    class Meta:
        model = Item
        fields = ('id', 'title', 'location')


class ExtendedItemSerializer(serializers.HyperlinkedModelSerializer):
    """
        Reduced item serializer to reduce data transfer on search requests
    """
    default_image = serializers.SerializerMethodField()
    detail_page_url = serializers.SerializerMethodField('get_detail_item_url')
    location = LocationSerializer(many=False, read_only=True)

    def get_detail_item_url(self, instance):
        return reverse('respool:item-detail', [instance.id], request=self.context['request'])

    def get_default_image(self, instance):
        image = instance.images.all().first()
        if image:
            return DefaultImageThumbSerializer(image).data
        return None

    class Meta:
        model = Item
        fields = ('id', 'title', 'description', 'default_image', 'detail_page_url', 'location')
