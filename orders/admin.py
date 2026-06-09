from django.contrib import admin
from .models import marketplace, order, order_product, ml_credentials, api_error

# Register your models here.
admin.site.register(marketplace)
admin.site.register(order)
admin.site.register(order_product)
admin.site.register(ml_credentials)
admin.site.register(api_error)
