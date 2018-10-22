from django.urls import path

from respool.api.v1 import views

urlpatterns = [
    # API Version 1
    path('items/', views.ApiItems.as_view(), name='items'),
    path('items/<int:pk>/', views.ApiItem.as_view(), name='item'),
    path('items/<int:pk>/order-images', views.ApiItemImageOrdering.as_view(), name='item-image-ordering'),
    path('items/default-image', views.ApiItemImagesDefault.as_view(), name='items-default-image'),
    path('rental-fees/intervals', views.ApiRentalFeeIntervallOptions.as_view(), name='rental-fee-intervall-options'),
]
