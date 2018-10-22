from django.urls import path

from . import views

app_name = 'respool'
urlpatterns = [
    path('', views.home, name='home'),
    # path('home', views.home, name='home'),
    path('map/', views.map, name='map'),
    path('items/<int:pk>/', views.item_detail_page, name='item-detail'),
    path('items/<int:pk>/addToCart', views.item_add_to_cart, name='item-add-to-cart'),
    path('items/<int:pk>/removeFromCart', views.item_remove_from_cart, name='item-remove-from-cart'),

    path('shoppingcart', views.shoppingcart, name='shoppingcart'),

    path('impressum', views.impressum, name='impressum'),
    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),
]
