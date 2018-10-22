import logging

from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from accounts.models import Lender
from .models import Item

logger = logging.getLogger(__name__)

'''Authors: Michael Götz, Marius Hofmann'''


def home(request):
    '''
        render homepage with filter sidebar

    :param request:
    :return: rendered homepage
    '''
    types = {'venue': Item.VENUE, 'service': Item.SERVICE, 'object': Item.OBJECT}
    return render(request, "home.jinja", {'title': 'Willkommen beim Ressourcenpool Bamberg', 'types': types})


def map(request):
    '''
    render map page with leaflet map and filter sidebar

    :param request:
    :return: rendered map page
    '''
    types = {'venue': Item.VENUE, 'service': Item.SERVICE, 'object': Item.OBJECT}
    return render(request, "respool/map/leaflet.jinja", {'title': 'Respool Map', 'types': types})


def item_detail_page(request, pk):
    """
        render all information about  a single item

    :param request:
    :param pk: the items id
    :return: rendered item detail page
    """
    item = Item.objects.get(id=pk)
    title = 'Item: ' + item.title
    is_in_cart = pk in request.session.get('shopping_cart_items', [])

    return render(request, "respool/item_detail_page.jinja", {'title': title, 'item': item, 'is_in_cart': is_in_cart})


def item_add_to_cart(request, pk):
    '''
     Adds an item to the shopping cart saved in the session

    :param request:
    :param pk: the items id
    :return: rendered detail page
    '''
    item = Item.objects.get(id=pk)

    if 'shopping_cart_items' not in request.session or not request.session['shopping_cart_items']:
        request.session['shopping_cart_items'] = [item.id]
    else:
        saved_list = request.session['shopping_cart_items']
        if item.id not in saved_list:
            saved_list.append(item.id)
            request.session['shopping_cart_items'] = saved_list

    return item_detail_page(request=request, pk=pk)


def item_remove_from_cart(request, pk):
    """
        removes an item from the shopping cart saved in the session

    :param request:
    :param pk: the items id
    :return: redirect to the shopping cart page
    """
    item = Item.objects.get(id=pk)

    saved_list = request.session.get('shopping_cart_items', [])
    if item.id in saved_list:
        saved_list.remove(item.id)
        request.session['shopping_cart_items'] = saved_list

    return redirect('respool:shoppingcart')


def impressum(request):
    """
        renders the impressum page

    :param request:
    :return: rendered impressum page
    """
    return render(request, "impressum.jinja",
                  {'title': 'Willkommen beim Ressourcenpool Bamberg', 'text': "Ressourcenpool Bamberg"})


def about(request):
    """
        Renders the about page

    :param request:
    :return: rendered about page
    """
    return render(request, "about.jinja",
                  {'title': 'Willkommen beim Ressourcenpool Bamberg', 'text': "Ressourcenpool Bamberg"})


def contact(request):
    """
        Renders the contact page

    :param request:
    :return: the rendered contact page
    """
    return render(request, "contact.jinja",
                  {'title': 'Willkommen beim Ressourcenpool Bamberg', 'text': "Ressourcenpool Bamberg"})


def shoppingcart(request):
    """
        render the shopping cart with sorterd items by lender

    :param request:
    :return: rendered shopping cart
    """
    item_ids = request.session.get('shopping_cart_items')

    requesting_user = None
    if request.user.is_authenticated:
        requesting_user = User.objects.get(id=request.user.id)
    lender_items = {}
    if item_ids:
        lenders = Lender.objects.filter(item__in=item_ids).distinct()
        for lender in lenders:
            lender_items[lender] = Item.objects.filter(lender=lender, id__in=item_ids)

    return render(request, "respool/shoppingcart.jinja",
                  {'title': 'Warenkorb', 'lender_items': lender_items, 'requesting_user': requesting_user})
