from django.contrib import admin
from .models import product_category, product, derivated_sku

# Register your models here.
admin.site.register(product_category)
admin.site.register(product)
admin.site.register(derivated_sku)
