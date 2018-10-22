from __future__ import unicode_literals

from datetime import datetime

import coreapi
import coreschema
from django.db.models import Q
from django.templatetags.static import static
from rest_framework import generics, schemas, views, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from respool.api.v1.serializers import MinimalItemSerializer, ItemSerializer, DefaultItemImageSerializer, \
    CategorySerializer, RentalFeeChoicesSerializer, ExtendedItemSerializer
from respool.models import Item, Category, RentalFee
from respool.utils import geocoding

'''
Authors: Michael Götz, Marius Hofmann
'''


@permission_classes((AllowAny,))
class ApiItems(generics.ListAPIView):
    """
        Return a list of items filtered by given parameter.
    """
    schema = schemas.AutoSchema(manual_fields=[
        coreapi.Field(
            "search-token",
            required=False,
            location="query",
            schema=coreschema.String(
                description='Search for the token in each title of an item'
            ),
        ),
        coreapi.Field(
            "type",
            required=False,
            location="query",
            schema=coreschema.Integer(
                description='int value that represents the type'
            ),
        ),
        coreapi.Field(
            "lender",
            required=False,
            location="query",
            schema=coreschema.String(description='array of lender ids'),

        ),
        coreapi.Field(
            "min-amount",
            required=False,
            location="query",
            schema=coreschema.Integer(description='minimal amount of an object item'),
        ),
        coreapi.Field(
            "max-weight",
            required=False,
            location="query",
            schema=coreschema.Number(description='max weight of an object item in kg', ),
        ),
        coreapi.Field(
            "categories",
            required=False,
            location="query",
            schema=coreschema.String(description='array of category ids', ),
        ),
        coreapi.Field(
            "max-caution",
            required=False,
            location="query",
            schema=coreschema.Number(description='maximal caution in €', ),
        ),
        coreapi.Field(
            "max-single-rent",
            required=False,
            location="query",
            schema=coreschema.Number(description='maximal single rent in €', ),
        ),
        coreapi.Field(
            "max-rental-fee-costs",
            required=False,
            location="query",
            schema=coreschema.Number(description='maximal rental fee costs in €', ),
        ),
        coreapi.Field(
            "rental-fee-interval",
            required=False,
            location="query",
            schema=coreschema.Number(description='int representation of an rental fee interval', ),
        ),
        coreapi.Field(
            "min-height",
            required=False,
            location="query",
            schema=coreschema.Number(description='min height of an object or location item in meter', ),
        ),
        coreapi.Field(
            "max-height",
            required=False,
            location="query",
            schema=coreschema.Number(description='max height of an object or location item in meter', ),
        ),
        coreapi.Field(
            "min-width",
            required=False,
            location="query",
            schema=coreschema.Number(description='min width of an object or location item in meter', ),

        ),
        coreapi.Field(
            "max-width",
            required=False,
            location="query",
            schema=coreschema.Number(description='max width of an object or location item in meter', ),
        ),
        coreapi.Field(
            "min-depth",
            required=False,
            location="query",
            schema=coreschema.Number(description='min depth of an object or location item in meter', ),
        ),
        coreapi.Field(
            "max-depth",
            required=False,
            location="query",
            schema=coreschema.Number(description='max depth of an object or location item in meter', ),
        ),
        coreapi.Field(
            "start-date",
            required=False,
            location="query",
            schema=coreschema.String(
                description='needed for occupancy search. format = %Y-%m-%d. Requires: end-date field', ),
        ),
        coreapi.Field(
            "end-date",
            required=False,
            location="query",
            schema=coreschema.String(
                description='needed for occupancy search. format = %Y-%m-%d. Requires: start-date field', ),
        ),
        coreapi.Field(
            "house-number",
            required=False,
            location="query",
            schema=coreschema.Integer(
                description='needed for bounding box search. Requires: street, city, distance field', ),
        ),
        coreapi.Field(
            "street",
            required=False,
            location="query",
            schema=coreschema.String(
                description='needed for bounding box search. Requires: house-number, city, distance field', ),
        ),
        coreapi.Field(
            "city",
            required=False,
            location="query",
            schema=coreschema.String(
                description='needed for radius based search. Requires: house-number, street, distance field', ),
        ),
        coreapi.Field(
            "distance",
            required=False,
            location="query",
            schema=coreschema.String(
                description='needed for radius based search. Requires: house-number, street, city field', ),
        ),
    ])

    def get_serializer_class(self):
        type = self.request.query_params.get('data-type')
        if type == 'map':
            return ExtendedItemSerializer
        return MinimalItemSerializer

    def get_queryset(self):
        queryset = Item.objects.all()
        search_token = self.request.query_params.get('search-token')
        if search_token:
            queryset = queryset.filter(title__icontains=search_token)
        type = self.request.query_params.get('type')
        if type:
            queryset = queryset.filter(type=type)
        lenders = self.request.query_params.getlist('lender')
        if lenders:
            queryset = queryset.filter(lender__in=lenders)
        min_amount = self.request.query_params.get('min-amount')
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        max_weight = self.request.query_params.get('max-weight')
        if max_weight:
            queryset = queryset.filter(weight__lte=max_weight)
        categories = self.request.query_params.getlist('categories')
        if categories:
            for category in categories:
                queryset = queryset.filter(categories__id=category)

        max_caution = self.request.query_params.get('max-caution')
        max_single_rent = self.request.query_params.get('max-single-rent')
        max_rental_fee_costs = self.request.query_params.get('max-rental-fee-costs')
        rental_fee_interval = self.request.query_params.get('rental-fee-interval')
        if max_caution:
            queryset = queryset.filter(loan__caution__lte=max_caution)
        if max_single_rent:
            queryset = queryset.filter(loan__single_rent__lte=max_single_rent)
        if max_rental_fee_costs:
            queryset = queryset.filter(loan__rental_fee__costs__lte=max_rental_fee_costs)
        if rental_fee_interval:
            queryset = queryset.filter(loan__rental_fee__interval_unit=int(rental_fee_interval))

        min_height = self.request.query_params.get('min-height')
        max_height = self.request.query_params.get('max-height')
        min_width = self.request.query_params.get('min-width')
        max_width = self.request.query_params.get('max-width')
        min_depth = self.request.query_params.get('min-depth')
        max_depth = self.request.query_params.get('max-depth')
        if max_height:
            queryset = queryset.filter(dimension__height__lte=max_height)
        if max_width:
            queryset = queryset.filter(dimension__width__lte=max_width)
        if max_depth:
            queryset = queryset.filter(dimension__depth__lte=max_depth)

        if min_height:
            queryset = queryset.filter(dimension__height__gte=min_height)
        if min_width:
            queryset = queryset.filter(dimension__width__gte=min_width)
        if min_depth:
            queryset = queryset.filter(dimension__depth__gte=min_depth)

        start_date = self.request.query_params.get('start-date')
        end_date = self.request.query_params.get('end-date')

        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=23, minute=59)
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59)
            queryset = queryset.filter((
                                               Q(occupancies__start_time__gt=start_date_obj)
                                               &
                                               Q(occupancies__start_time__gt=end_date_obj))
                                       | (
                                               Q(occupancies__end_time__lt=start_date_obj)
                                               &
                                               Q(occupancies__end_time__lt=end_date_obj))).distinct()

        house_number = self.request.query_params.get('house-number')
        street = self.request.query_params.get('street')
        city = self.request.query_params.get('city')
        distance = self.request.query_params.get('distance')
        if all([house_number, street, city, distance]):
            latitude, longitude = geocoding.getGeoCode(house_number=house_number, street=street, city=city)
            if latitude and longitude:
                min_latitude, max_latitude, min_longitude, max_longitude = geocoding.getBoundingBox(latitude, longitude,
                                                                                                    distance)
                queryset = queryset.filter(location__latitude__gt=min_latitude, location__latitude__lt=max_latitude,
                                           location__longitude__gt=min_longitude, location__longitude__lt=max_longitude)
        return queryset

    def list(self, request, *args, **kwargs):
        items = self.get_queryset()
        categories = Category.objects.filter(item__in=items).distinct()
        item_serializer = self.get_serializer(items, many=True)
        category_serializer = CategorySerializer(categories, many=True)
        return Response({
            "categories": category_serializer.data,
            "items": item_serializer.data,
        })


@permission_classes((AllowAny,))
class ApiItem(generics.RetrieveAPIView):
    """
        Returns id, title, description, dimension, weight, amount, type, loan_agreement, images, location, lender, occupancies
    """
    serializer_class = ItemSerializer
    queryset = Item.objects.all()


@permission_classes((AllowAny,))
class ApiItemImagesDefault(views.APIView):
    """
     Returns the servers default image location
    """

    def get(self, request):
        image = {'image': request.build_absolute_uri(static('images/placeholder.jpg'))}
        results = DefaultItemImageSerializer(image, many=False).data
        return Response(results, status=status.HTTP_200_OK)


@permission_classes((IsAuthenticated,))
class ApiItemImageOrdering(views.APIView):
    """
    Sets the order of images for an item
    """
    def post(self, request, pk):
        item = Item.objects.get(id=pk)
        # TODO: fix getlist for api webinterface "'dict' object has no attribute 'getlist'"
        ordered_image_ids = request.data.getlist('image_ids')
        int_ordered_image_ids = list(map(int, ordered_image_ids))
        for image in item.images.all():
            image.order_id = int(int_ordered_image_ids.index(image.id)) + 1
            image.save()
        return Response("", status=status.HTTP_200_OK)


@permission_classes((AllowAny,))
class ApiRentalFeeIntervallOptions(views.APIView):
    """
    Returns the rental fee interval map
    """

    def get(self, request):
        choices = RentalFee.INTERVAL_UNIT_CHOICES
        rental_fee_intervall_units = []
        for choice in choices:
            rental_fee_intervall_units.append({'id': choice[0], 'title': choice[1]})

        results = RentalFeeChoicesSerializer(rental_fee_intervall_units, many=True).data
        return Response(results, status=status.HTTP_200_OK)
