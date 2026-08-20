from django.contrib import admin
from .models import product_category, product, derivated_sku
from import_export.admin import ImportExportModelAdmin
from .resources import product_admin_resource, derivated_sku_resource, product_category_admin_resource

class product_admin(ImportExportModelAdmin):
    resource_class = product_admin_resource

class derivated_sku_admin(ImportExportModelAdmin):
    resource_class = derivated_sku_resource

class product_category_admin(ImportExportModelAdmin):
    resource_class = product_category_admin_resource

# Register your models here.
admin.site.register(product, product_admin)
admin.site.register(derivated_sku, derivated_sku_admin)
admin.site.register(product_category, product_category_admin)

