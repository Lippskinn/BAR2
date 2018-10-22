import logging

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from accounts.models import Lender, Borrower
from core.tokens import account_activation_token
from accounts.forms import ItemVenueForm, ItemObjectForm, ItemServiceForm, LenderForm, BorrowerForm, \
    EditProfileForm
from respool.models import Item, Image, Location, Dimension, Loan, RentalFee, LoanAgreement, reset_image_order_ids, \
    get_next_order_id

logger = logging.getLogger(__name__)

""" Authors: Marius Hofmann, Sebastian Brehm, Michael Götz"""


# Create your views here.
def addItem(request):
    """
    Item adding overview.
    Shows adding options

    :param request: request object
    :return: item adding overview page
    """
    return render(request, 'accounts/add_item/add_item.jinja', {'title': 'Item hinzufügen'})


def account(request):
    """
    Page where a user can see his/her account information

    :param request: request object
    :return: Borrower or Lender profile page
    """
    if hasattr(request.user, 'borrower'):
        borrower_user = Borrower.objects.get(user=request.user)
        return render(request, 'accounts/borrower_profile.jinja',
                      {'title': 'Profil', 'borrower': borrower_user})
    else:
        user_items = Item.objects.filter(lender__user=request.user)
        lender_user = Lender.objects.get(user=request.user)
        return render(request, 'accounts/lender_profile.jinja',
                      {'title': 'Profil', 'lender': lender_user, 'user_items': user_items, })


def edit_account(request):
    """
    Page where a user can change his/her profile data

    :param request: request object
    :return: Account overview page or edit profile page
    """
    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST, instance=request.user)

        if profile_form.is_valid():
            profile_form.save()
            return redirect(reverse('accounts:account'))
    else:
        profile_form = EditProfileForm(instance=request.user)
        return render(request, 'accounts/edit_profile.jinja', {'title': 'Profil editieren',
                                                               'profile_form': profile_form, })


def public_lender_profile(request, lender_pk):
    """
    Public page which displays information about a lender

    :param request: request object
    :param lender_pk: primary key to identificate the lender
    :return: public lender profile page
    """
    lender = Lender.objects.get(id=lender_pk)
    items = Item.objects.filter(lender=lender)
    return render(request, 'accounts/public_lender_profile.jinja',
                  {'title': "Verleiher: " + lender.user.username, 'lender': lender, 'items': items})


def registration(request):
    """
    renders the registration choice page

    :param request:
    :return: rendered registration choice page
    """
    return render(request, 'accounts/registration/registrationpage.jinja', {
        'title': 'Möchten Sie leihen oder verleihen? (Hinweis: Auch ein Verleiher kann sich Ressourcen leihen.)'})


def get_initial_basic_object(item):
    """
    builds an item object with all basic attributes filled for a formular preparation

    :param item: the item which shall be converted
    :return: the prepared object
    """
    inital_item = {'title': item.title,
                   'description': item.description,
                   'type': item.type,
                   'categories': [category.id for category in item.categories.all()],
                   'location_title': item.location.title,
                   'location_house_number': item.location.house_number,
                   'location_street': item.location.street,
                   'location_city': item.location.city,
                   'location_latitude': item.location.latitude,
                   'location_longitude': item.location.longitude,
                   'loan_caution': item.loan.caution,
                   'loan_single_rent': item.loan.single_rent,
                   }
    if item.loan.rental_fee:
        inital_item['loan_rental_fee_costs'] = item.loan.rental_fee.costs
        inital_item['loan_rental_fee_interval_unit'] = item.loan.rental_fee.interval_unit

    return inital_item


def save_basic_item_attributes(form, user, item=None):
    """
    saves the basic item attribute values in an item database object.
    if an item is given the values will be overwritten
    otherwise a new object will be created

    :param form: the formular which shall be saved
    :param user: the user which saving the item
    :param item: the item which shall be updated
    :return: the updated item
    """
    title = form.cleaned_data.get('title')
    description = form.cleaned_data.get('description')
    type = form.cleaned_data.get('type')
    lender = Lender.objects.get(user=user)
    location, _ = Location.objects.get_or_create(
        house_number=form.cleaned_data.get('location_house_number'),
        street=form.cleaned_data.get('location_street'),
        city=form.cleaned_data.get('location_city'),
        defaults={
            'title': form.cleaned_data.get('location_title'),
            'latitude': form.cleaned_data.get('location_latitude'),
            'longitude': form.cleaned_data.get('location_longitude')})
    if not item:
        item = Item.objects.create(title=title, description=description, type=type, lender=lender, location=location)
    else:
        item.title = title
        item.description = form.cleaned_data.get('description')
        item.type = type
        item.lender = lender
        item.location = location
    item.categories.set(form.cleaned_data.get('categories'))

    # remove existing loan_agreement if new one is provided
    if item.loan_agreement and form.cleaned_data.get('loan_agreement_file'):
        item.loan_agreement.delete()

    item.loan_agreement = LoanAgreement.objects.create(file=form.cleaned_data.get('loan_agreement_file'))

    images_to_delete_ids = form.data.getlist('deleteImages')
    if images_to_delete_ids:
        images_to_delete = item.images.filter(id__in=images_to_delete_ids).all()
        for image in images_to_delete:
            image.delete()

    reset_image_order_ids(item)

    if form.files:
        image_files = form.files.getlist('images')
        next_order_id = get_next_order_id(item)
        if image_files:
            for index, image_file in enumerate(image_files):
                item.images.add(Image.objects.create(file=image_file, order_id=index + next_order_id))

    if form.cleaned_data.get('loan_rental_fee_interval_unit') and form.cleaned_data.get('loan_rental_fee_costs'):
        rental_fee, _ = RentalFee.objects.get_or_create(
            interval_unit=form.cleaned_data.get('loan_rental_fee_interval_unit'),
            costs=form.cleaned_data.get('loan_rental_fee_costs'))
    else:
        rental_fee = None
    item.loan, _ = Loan.objects.get_or_create(caution=form.cleaned_data.get('loan_caution'),
                                              single_rent=form.cleaned_data.get('loan_single_rent'),
                                              rental_fee=rental_fee)

    return item


def add_item_venue(request):
    """
        render adding formular for venue item and save the formular

        :param request:
        :return: render formular again on failure or redirect to account overview on success
        """
    item_base_form = ItemVenueForm(initial={'type': Item.VENUE, },
                                   data=request.POST or None,
                                   files=request.FILES or None)
    if request.method == 'POST':
        if item_base_form.is_valid():
            item = save_basic_item_attributes(item_base_form, request.user)
            item.dimension, _ = Dimension.objects.get_or_create(
                width=item_base_form.cleaned_data.get('dimension_width'),
                height=item_base_form.cleaned_data.get('dimension_height'),
                depth=item_base_form.cleaned_data.get('dimension_depth'))
            item.save()
            return redirect('accounts:account')
    return render(request, 'accounts/add_item/venue_item_form.jinja', {'title': 'Einen Veranstaltungsort hinzufügen',
                                                                       'item_base_form': item_base_form, 'item': None})


def add_item_service(request):
    """
        render adding formular for service item and save the formular

        :param request:
        :return: render formular again on failure or redirect to account overview on success
        """
    item_base_form = ItemServiceForm(initial={'type': Item.SERVICE},
                                     data=request.POST or None,
                                     files=request.FILES or None)
    if request.method == 'POST':
        if item_base_form.is_valid():
            item = save_basic_item_attributes(item_base_form, request.user)
            item.save()
            return redirect('accounts:account')
    # if a GET (or any other method) we'll create a blank form
    return render(request, 'accounts/add_item/service_item_form.jinja',
                  {'title': 'Einen Service hinzufügen',
                   'item_base_form': item_base_form, 'item': None})


def add_item_object(request):
    """
    render adding formular for object item and save the formular

    :param request:
    :return: render formular again on failure or redirect to account overview on success
    """
    item_base_form = ItemObjectForm(initial={'type': Item.OBJECT},
                                    data=request.POST or None,
                                    files=request.FILES or None)

    if request.method == 'POST':
        if item_base_form.is_valid():
            item = save_basic_item_attributes(item_base_form, request.user)
            dimension, _ = Dimension.objects.get_or_create(width=item_base_form.cleaned_data.get('dimension_width'),
                                                           height=item_base_form.cleaned_data.get('dimension_height'),
                                                           depth=item_base_form.cleaned_data.get('dimension_depth'))
            item.weight = item_base_form.cleaned_data.get('weight')
            item.amount = item_base_form.cleaned_data.get('amount')
            item.dimension = dimension
            item.save()
            return redirect('accounts:account')
    return render(request, 'accounts/add_item/object_item_form.jinja', {'title': 'Ein Objekt hinzufügen',
                                                                        'item_base_form': item_base_form, 'item': None})


def edit_item_venue(request, item):
    """
    render editing formular for venue items and save the formular

    :param request:
    :param item: item which shall be edited
    :return: render formular again on failure or redirect to account overview on success
    """
    initial_item = get_initial_basic_object(item)
    initial_item['dimension_height'] = item.dimension.height
    initial_item['dimension_width'] = item.dimension.width
    initial_item['dimension_depth'] = item.dimension.depth
    form = ItemVenueForm(initial=initial_item,
                         data=request.POST or None,
                         files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            item = save_basic_item_attributes(form=form, user=request.user, item=item)
            item.dimension, _ = Dimension.objects.get_or_create(width=form.cleaned_data.get('dimension_width'),
                                                                height=form.cleaned_data.get('dimension_height'),
                                                                depth=form.cleaned_data.get('dimension_depth'))
            item.save()
            return redirect('accounts:account')
    return render(request, 'accounts/add_item/venue_item_form.jinja',
                  {'title': 'Einen Venanstaltungsort editieren',
                   'item': item,
                   'item_base_form': form,
                   })


def edit_item_service(request, item):
    """
    render editing formular for service items and save the formular

    :param request:
    :param item: item which shall be edited
    :return: render formular again on failure or redirect to account overview on success
    """
    form = ItemServiceForm(initial=get_initial_basic_object(item),
                           data=request.POST or None,
                           files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            item = save_basic_item_attributes(form=form, user=request.user, item=item)
            item.save()
            return redirect('accounts:account')
    return render(request, 'accounts/add_item/service_item_form.jinja',
                  {'title': 'Einen Service editieren',
                   'item': item,
                   'item_base_form': form,
                   })


def edit_item_object(request, item):
    """
    render editing formular for object items and save the formular

    :param request:
    :param item: item which shall be edited
    :return: render formular again on failure or redirect to account overview on success
    """
    initial_item = get_initial_basic_object(item)
    initial_item['weight'] = item.weight
    initial_item['amount'] = item.amount
    initial_item['dimension_height'] = item.dimension.height
    initial_item['dimension_width'] = item.dimension.width
    initial_item['dimension_depth'] = item.dimension.depth
    form = ItemObjectForm(initial=initial_item,
                          data=request.POST or None,
                          files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            item = save_basic_item_attributes(form=form, user=request.user, item=item)
            item.dimension, _ = Dimension.objects.get_or_create(width=form.cleaned_data.get('dimension_width'),
                                                                height=form.cleaned_data.get('dimension_height'),
                                                                depth=form.cleaned_data.get('dimension_depth'))
            item.weight = form.cleaned_data.get('weight')
            item.amount = form.cleaned_data.get('amount')
            item.save()
            return redirect('accounts:account')
    return render(request, 'accounts/add_item/object_item_form.jinja',
                  {'title': 'Ein Objekt editieren',
                   'item': item,
                   'item_base_form': form,
                   })


def edit_item(request, pk):
    """
    controls all item editing functionality.
    editing of all the item types and saving of all three item types.

    :param request:
    :param pk: item which shall be edited
    :return: redirect to error page on hard (not on field errors) errors or render the formular initial or on field errors
    """
    item = Item.objects.get(id=pk)
    if item.type == Item.VENUE:
        return edit_item_venue(request, item)
    elif item.type == Item.SERVICE:
        return edit_item_service(request, item)
    elif item.type == Item.OBJECT:
        return edit_item_object(request, item)
    else:
        return request('error')


def order_images(request, pk):
    """
    render the image sorting page

    :param request:
    :param pk: item (id) which images shall be sorted
    :return: rendered image sorting page
    """
    item = Item.objects.get(id=pk)
    return render(request, 'accounts/add_item/image_ordering_form.jinja',
                  {'title': '{}: Bilder anordnen'.format(item.title),
                   'item': item, })


def remove_item(request, pk):
    """
    removes the item with the pk if the user is permitted

    :param request:
    :param pk: the items id
    :return: redirect to an error page if user not permitted or item not found or the account page on success
    """
    try:
        item = Item.objects.get(id=pk)
        if request.user.is_authenticated and item.lender.user == request.user:
            item.delete()
            return redirect('accounts:account')
    except (ObjectDoesNotExist, MultipleObjectsReturned) as err:
        pass
    return redirect('error')


def registration_lender(request):
    """
    Registration as lender.

    :param request: request object
    :return: registration done page or lender registration page
    """
    if request.method == 'POST':
        lender_form = LenderForm(request.POST, request.FILES)
        if lender_form.is_valid():
            user_data = {
                'first_name': lender_form.cleaned_data.get('first_name'),
                'last_name': lender_form.cleaned_data.get('last_name'),
                'email': lender_form.cleaned_data.get('email'),
                'username': lender_form.cleaned_data.get('username'),
                'password': lender_form.cleaned_data.get('password1')}
            user = User.objects.create_user(**user_data)
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.save()

            lender_data = {
                'phone_number': lender_form.cleaned_data.get('phone_number'),
                'phone_number_mobile': lender_form.cleaned_data.get('phone_number_mobile'),
                'type': lender_form.cleaned_data.get('type'),
                'description': lender_form.cleaned_data.get('description'),
                'default_loan_agreement': lender_form.cleaned_data.get('loan_agreement'),
                'website': lender_form.cleaned_data.get('website')
            }
            location, _ = Location.objects.get_or_create(title=lender_form.cleaned_data['location_title'],
                                                         street=lender_form.cleaned_data['location_street'],
                                                         house_number=lender_form.cleaned_data['location_house_number'],
                                                         city=lender_form.cleaned_data['location_city'],
                                                         latitude=lender_form.cleaned_data['location_latitude'],
                                                         longitude=lender_form.cleaned_data['location_longitude'])
            lender_data['location'] = location
            lender = Lender.objects.create(user=user, **lender_data)

            lender.user.is_active = False
            lender.user.save()

            current_site = get_current_site(request)
            subject = 'Aktivieren Sie Ihren Account beim Ressourcenpool'
            message = render_to_string('accounts/registration/account_activation_email.jinja', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('accounts:registration_done')
        else:
            return render(request, 'accounts/registration/registration_lender.jinja',
                          {'lender_form': lender_form,
                           'title': 'Registrierung als Verleiher',
                           })
    else:
        return render(request, 'accounts/registration/registration_lender.jinja',
                      {'lender_form': LenderForm(),
                       'title': 'Registrierung als Verleiher'
                       })


def registration_borrower(request):
    """
    Registration as borrower.

    :param request: request object
    :return: registration done page or borrower registration page
    """
    if request.method == 'POST':
        borrower_form = BorrowerForm(request.POST)
        if borrower_form.is_valid():
            user_data = {
                'first_name': borrower_form.cleaned_data.get('first_name'),
                'last_name': borrower_form.cleaned_data.get('last_name'),
                'email': borrower_form.cleaned_data.get('email'),
                'username': borrower_form.cleaned_data.get('username'),
                'password': borrower_form.cleaned_data.get('password1')}
            user = User.objects.create_user(**user_data)
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.save()

            borrower_data = {
                'phone_number': borrower_form.cleaned_data.get('phone_number'),
                'phone_number_mobile': borrower_form.cleaned_data.get('phone_number_mobile')
            }

            borrower = Borrower.objects.create(user=user, **borrower_data)

            borrower.user.is_active = False
            borrower.user.save()

            current_site = get_current_site(request)
            subject = 'Aktivieren Sie Ihren Account beim Ressourcenpool'
            message = render_to_string('accounts/registration/account_activation_email.jinja', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('accounts:registration_done')
        else:
            print(borrower_form.errors)
            return render(request, 'accounts/registration/registration_borrower.jinja',
                          {'borrower_form': borrower_form,
                           'title': 'Registrierung: Leiher'})
    else:
        return render(request, 'accounts/registration/registration_borrower.jinja',
                      {'borrower_form': BorrowerForm(),
                       'title': 'Registrierung: Leiher'})


def activate(request, uidb64, token):
    """
    Setting the user active after he/she registrated and has clicked on the activation link in the mail

    :param request:
    :param uidb64: the base64 encoded user id send per mail
    :param token: the registration token send per mail
    :return: a success page if the user is activated or an error page if not

    Authors: Michael Götz, Marius Hofmann
    """
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('accounts:registration_success')
    else:
        return redirect('accounts:registration_error')


def registration_success(request):
    """
    Registration success page.

    :param request: request object
    :return: registration success page.
    """
    return render(request, 'accounts/registration/registration_success.jinja')


def registration_error(request):
    """
    Registration error page.

    :param request: request object
    :return: registration error page.
    """
    return render(request, 'accounts/registration/registration_error.jinja')


def registration_done(request):
    """
    Registration done page, appears when the user filles the registration form and clicks on registrate

    :param request: request object
    :return: registration done page 
    """
    return render(request, 'accounts/registration/registration_done.jinja')
