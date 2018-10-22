from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from respool.models import Item, RentalFee, Category
from accounts.models import Lender

'''Authors: Sebastian Brehm, Michael Götz'''


class ItemForm(forms.Form):
    """
        represents all form field that are used by all item types.

        Author: Michael Götz
    """
    title = forms.CharField(required=True, label='Titel')
    description = forms.CharField(required=True, label='Beschreibung')
    type = forms.IntegerField(required=True)
    categories = forms.ModelMultipleChoiceField(required=False,
                                                label='Kategorien',
                                                queryset=Category.objects.all())

    loan_agreement_file = forms.FileField(required=False, label='Leihvertrag')
    images = forms.FileField(required=False, label='Bilder',
                             widget=forms.ClearableFileInput(attrs={'multiple': True}))

    location_title = forms.CharField(required=False, label='Bezeichnung')
    location_house_number = forms.IntegerField(required=True, min_value=0, label='Hausnummer')
    location_street = forms.CharField(required=True, label='Straße')
    location_city = forms.CharField(required=True, label='Stadt/Ort')
    location_latitude = forms.FloatField(required=False, label='Longitude')
    location_longitude = forms.FloatField(required=False, label='Latitude')

    loan_caution = forms.FloatField(required=False, label='Kaution')
    loan_single_rent = forms.FloatField(required=False, label='Einmalige Leihgebühr')
    loan_rental_fee_interval_unit = forms.ChoiceField(required=False, label='Zahlungintervall',
                                                      choices=RentalFee.INTERVAL_UNIT_CHOICES)
    loan_rental_fee_costs = forms.FloatField(required=False, label='Mietkosten')


class ItemDimensionForm(forms.Form):
    """
        represents the dimension form fields

        Author: Michael Götz
    """
    dimension_width = forms.FloatField(required=True, min_value=0.0, label='Breite')
    dimension_height = forms.FloatField(required=True, min_value=0.0, label='Höhe')
    dimension_depth = forms.FloatField(required=True, min_value=0.0, label='Tiefe')


class ItemVenueForm(ItemForm, ItemDimensionForm):
    """
        Implement ItemForm and ItemDimensionForm and exends them to represent a Venue Item

        Author: Michael Götz
    """

    def clean(self):
        """ check venue item constraints"""
        if self.cleaned_data['type'] == Item.VENUE:
            height = self.cleaned_data.get('dimension_height')
            depth = self.cleaned_data.get('dimension_depth')
            width = self.cleaned_data.get('dimension_width')
            if not all([height, depth, width]):
                raise ValidationError(
                    'Venue item need value for attributes: dimension_width, dimension_height, dimension_depth')
        else:
            raise ValidationError('No Venue type')


class ItemServiceForm(ItemForm):
    """
        Implement ItemForm and extends it to represent a Service Item

        Author: Michael Götz
    """

    def clean(self):
        """ check service item constraints"""
        height = self.cleaned_data.get('dimension_height')
        depth = self.cleaned_data.get('dimension_depth')
        width = self.cleaned_data.get('dimension_width')
        amount = self.cleaned_data.get('amount')
        weight = self.cleaned_data.get('weight')
        if self.cleaned_data['type'] == Item.SERVICE:
            if any([weight, amount, height, depth, width]):
                raise ValidationError('Service item cannot have the following attributes: weight, amount, dimension')
        else:
            raise ValidationError('No Service type')


class ItemObjectForm(ItemForm, ItemDimensionForm):
    """
        Implement ItemForm and ItemDimensionForm and exends them to represent a Object Item

        Author: Michael Götz
    """
    weight = forms.FloatField(required=True, min_value=0.0, label='Gewicht')
    amount = forms.FloatField(required=True, min_value=0, label='Anzahl')

    def clean(self):
        """ check object item constraints"""
        height = self.cleaned_data.get('dimension_height')
        depth = self.cleaned_data.get('dimension_depth')
        width = self.cleaned_data.get('dimension_width')
        amount = self.cleaned_data.get('amount')
        weight = self.cleaned_data.get('weight')
        if self.cleaned_data['type'] == Item.OBJECT:
            if not all([amount, weight, height, depth, width]):
                raise ValidationError(
                    'Object item needs values for attributes: dimension_width, dimension_height, dimension_depth, amount, weight')
        else:
            raise ValidationError('Unknown Item type')


class LenderForm(UserCreationForm):
    """
        Form to create a Lender

        Author: Sebastian Brehm
    """
    first_name = forms.CharField(required=True, label='Vorname')
    last_name = forms.CharField(required=True, label='Nachname')
    email = forms.EmailField(required=True, label='E-Mail-Adresse', max_length=200)
    password1 = forms.CharField(required=True, label='Passwort')
    password2 = forms.CharField(required=True, label='Passwort wiederholen')
    phone_number = forms.CharField(required=False, label='Telefon')
    phone_number_mobile = forms.CharField(required=False, label='Mobil')
    type = forms.ChoiceField(required=True,
                             label='Vertreten Sie eine Organisation oder treten Sie als Privatperson auf?',
                             choices=Lender.TYPE_CHOICES)
    description = forms.CharField(required=False, label='Beschreibung')
    loan_agreement = forms.FileField(required=False, label='Standard Leihvertrag')
    website = forms.CharField(required=False, label='Website')
    location_title = forms.CharField(required=False, label='Bezeichnung')
    location_street = forms.CharField(required=True, label='Straße')
    location_house_number = forms.IntegerField(required=True, label='Hausnummer')
    location_city = forms.CharField(required=True, label='Ort')
    location_latitude = forms.FloatField(required=False, label='Längengrad (optional)')
    location_longitude = forms.FloatField(required=False, label='Breitengrad (optional)')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone_number',
                  'phone_number_mobile', 'type', 'description',
                  'loan_agreement', 'website', 'location_title', 'location_street', 'location_house_number',
                  'location_latitude',
                  'location_longitude',)


class BorrowerForm(UserCreationForm):
    """
        Form to create a Borrower

        Author: Sebastian Brehm
    """
    first_name = forms.CharField(required=True, label='Vorname')
    last_name = forms.CharField(required=True, label='Nachname')
    email = forms.EmailField(required=True, label='E-Mail-Adresse', max_length=200)
    password1 = forms.CharField(required=True, label='Passwort')
    password2 = forms.CharField(required=True, label='Passwort wiederholen')
    phone_number = forms.CharField(required=False, label='Telefon')
    phone_number_mobile = forms.CharField(required=False, label='Mobil')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone_number',
                  'phone_number_mobile',)


class EditProfileForm(UserChangeForm):
    """
        Form which allows the user to edit his/her profile data

        Author: Sebastian Brehm
    """
    phone_number = forms.CharField(required=False, label='Telefon')
    phone_number_mobile = forms.CharField(required=False, label='Mobil')

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'password'
        )
