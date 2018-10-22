"""respool URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/

Examples:

Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')

Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')

Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

app_name = 'accounts'
urlpatterns = [
    path('account/', views.account, name='account'),
    path('account/edit', views.edit_account, name='edit_account'),
    path('account/<int:lender_pk>/public-profile/', views.public_lender_profile, name='public-lender-profile'),

    path('account/add-item/', views.addItem, name='add-item'),
    path('account/add-item/venue', views.add_item_venue, name='add-item-venue'),
    path('account/add-item/service', views.add_item_service, name='add-item-service'),
    path('account/add-item/object', views.add_item_object, name='add-item-object'),

    path('account/edit-item/<int:pk>/', views.edit_item, name='edit-item'),
    path('account/edit-item/<int:pk>/image-ordering', views.order_images, name='order-images'),

    path('account/delete-item/<int:pk>/', views.remove_item, name='delete-item'),

    path('account/login/', auth_views.login, {'template_name': 'accounts/login.jinja'}, name='login'),
    path('account/logout/', auth_views.logout, {'template_name': 'accounts/logout.jinja'}, name='logout'),
    path('account/registration/registrationpage', views.registration, name='registration'),
    path('account/registration/registration_lender', views.registration_lender, name='registration_lender'),
    path('account/registration/registration_borrower', views.registration_borrower, name='registration_borrower'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
    url(r'^reset-password/$', auth_views.password_reset,
        {'template_name': 'accounts/registration/password_reset_form.jinja',
         'post_reset_redirect': 'accounts:password_reset_done',
         'email_template_name': 'accounts/registration/password_reset_email.jinja'}, name='reset_password'),
    url(r'^reset-password/done/$', auth_views.password_reset_done,
        {'template_name': 'accounts/registration/password_reset_done.jinja'},
        name='password_reset_done'),
    url(r'^reset-password/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm,
        {'template_name': 'accounts/registration/password_reset_confirm.jinja',
         'post_reset_redirect': 'accounts:password_reset_complete'}, name='password_reset_confirm'),
    url(r'^reset-password/complete/$', auth_views.password_reset_complete,
        {'template_name': 'accounts/registration/password_reset_complete.jinja'}, name='password_reset_complete'),
    path('account/registration/registration_success', views.registration_success, name='registration_success'),
    path('account/registration/registration_error', views.registration_error, name='registration_error'),
    path('account/registration/registration_done', views.registration_done, name='registration_done'),
]
