from django.db import models

# Create your models here.
class marketplace(models.Model):
    marketplace_name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.marketplace_name


class order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('collect', 'ML Colecta'),
        ('flex', 'ML Flex'),
    ]

    marketplace = models.ForeignKey(marketplace, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100)
    shipping_id = models.CharField(max_length=100, blank=True)
    order_type = models.CharField(max_length=100, blank=True, choices=ORDER_TYPE_CHOICES)
    client_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=100, blank=True)
    creation_date_time = models.DateTimeField(null=True)
    estimated_pickup_time = models.DateTimeField(null=True)

    def __str__(self):
        return f"Order {self.order_id}"


class order_product(models.Model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    sku_seller = models.CharField(max_length=100, blank=True)
    sku_marketplace = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.order} - {self.product} (x{self.quantity})"