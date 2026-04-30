from django.contrib import admin
from django.urls import path
from . import views #Referencio al archivo views para usar sus funciones.

app_name = 'orders'

urlpatterns = [
    path('<slug>', views.orders, name='orders'),
]