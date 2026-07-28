from django import forms #Se está importando la creación de forms de django para que podamos crear nuestro propio model form.
from . import models #Desde "."(directorio actual) se va a importar "models.py"

class finish_orders_group_form(forms.ModelForm):
    class Meta:
        model = models.orders_group
        fields = ['courier_name', 'courier_license_plate', 'manifest_image']

        labels = {
            'courier_name': 'Nombre del despachador',
            'courier_license_plate': 'Patente del despachador',
            'manifest_image': 'Imagen del manifiesto',
        }

        