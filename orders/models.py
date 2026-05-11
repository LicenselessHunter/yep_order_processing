from django.db import models
from django.utils import timezone
from datetime import timedelta
from encrypted_fields.fields import EncryptedTextField #Aquí se importan los campos para encriptar data. Tener en cuenta que estos campos van a seguir siendo visibles en la página de admin. 

# Create your models here.

class ml_credentials(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    access_token = EncryptedTextField() #access_token para usar la api de mercado libre. Expira en 6 horas, se debe renovar con el refresh_token
    refresh_token = EncryptedTextField()
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True) #auto_now --> automatically update the field to the current date and time every time the object is saved.

    def is_expired(self): #Define custom methods on a model to add custom “row-level” functionality to your objects. Cada vez que este método sea llamado va a correr para el objeto referenciado.

        #The self (Puede tener otro nombre, pero este es el que se usa tipicamente) parameter is a reference to the current instance of the class. It is used to access properties and methods that belong to the class. Without self, Python would not know which object's properties you want to access.

        #Without self, Python would not know which object's properties you want to access

        # Usamos un margen de 5 minutos para evitar que expire durante la ejecución. 
        # In Python, timedelta is a class within the datetime module used to represent a duration or the difference between two dates or times. It allows you to perform datetime arithmetic, such as adding time to a current date or calculating the gap between two specific moments. 
        return timezone.now() >= (self.expires_at - timedelta(minutes=5))
        #Ej: expires_at = 2026-04-15 01:52:47.079295 --> expires_at - timedelta(minutes=5) = 2026-04-15 01:47:47.079295 (5 minutos menos)


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

    ORDER_STATUS = [
        ('ready_to_print', 'ready_to_print'),
        ('ready_to_ship', 'ready_to_ship'),
    ]

    marketplace = models.ForeignKey(marketplace, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100)
    shipping_id = models.CharField(max_length=100, blank=True)
    order_type = models.CharField(max_length=20, blank=True, choices=ORDER_TYPE_CHOICES)
    client_nickname = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, blank=True, choices=ORDER_STATUS)
    creation_date_time = models.DateTimeField(null=True)
    estimated_pickup_time = models.DateTimeField(null=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.estimated_pickup_time} - {self.order_type} - {self.client_nickname}"


class order_product(models.Model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    sku_seller = models.CharField(max_length=100, blank=True)
    sku_marketplace = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.order} - {self.sku_seller} (x{self.quantity})"