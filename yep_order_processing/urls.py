from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('orders/', include('orders.urls')), #Se incluye el archivo "oreders.urls" y con ello acceso a sus url. en la pagina.
]
