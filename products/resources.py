from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from . import models


class product_admin_resource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(models.product_category, field='category_name')
    )

    class Meta:
        model = models.product
        fields = ('sku', 'product_name', 'stock', 'category', 'ean')
        import_id_fields = ('sku',)


class derivated_sku_resource(resources.ModelResource):
    local_product_header = fields.Field(
        column_name='sku_base',
        attribute='local_product',
        widget=ForeignKeyWidget(models.product, field='sku')
    )

    derivated_sku_header = fields.Field(attribute='sku', column_name='sku_derivado')


    class Meta:
        model = models.derivated_sku
        fields = ('local_product_header', 'derivated_sku_header')
        import_id_fields = ('derivated_sku_header',)