from django.contrib import admin
from django.urls import path, include
from . import views #Referencio al archivo views para usar sus funciones.
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('accounts.urls')), #Se incluye el archivo "Accounts.urls" y con ello acceso a sus url. en la pagina.
    path('orders/', include('orders.urls')), #Se incluye el archivo "oreders.urls" y con ello acceso a sus url. en la pagina.
    path('products/', include('products.urls')),
] 
#Esta línea te permite servir los archivos (Como imágenes, PDFs, etc) subidos por el usuario en el ambiente de 'desarrollo'. Esta de debe anclar al urlpatterns.
#Énfasis en que esto funciona solo y únicamente en al ambiente de DESARROLLO. Si el DEBUG de settings.py es False, esta línea simplemente es ignorada.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
