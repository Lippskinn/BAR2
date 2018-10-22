from django.urls import path, include

urlpatterns = [
    # API Version 1
    path('v1/respool/', include('respool.api.v1.urls'))
]
