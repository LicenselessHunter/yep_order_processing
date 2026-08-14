from django.contrib import admin
from django.urls import path
from . import views #Referencio al archivo views para usar sus funciones.

app_name = 'products'

urlpatterns = [
    path('', views.products_catalogue, name='products_catalogue'),
    path('create-product/', views.create_product, name='create_product'),
    path('product-detail/<int:id>/', views.product_detail, name='product_detail'),
    path('edit-product/<int:id>/', views.edit_product, name='edit_product'),

]
