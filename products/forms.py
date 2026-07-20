from django import forms #Se está importando la creación de forms de django para que podamos crear nuestro propio model form.
from . import models #Desde "."(directorio actual) se va a importar "models.py"
from django.forms import BaseFormSet
from django.core.exceptions import ValidationError



class product_create_form(forms.ModelForm): #Esta clase va a representar el producto, va a heredar de "forms.ModelForm"
	class Meta: #Esta clase va a contener los campos o elementos que queremos mostrar en el form.
		model = models.product #El model que vamos a usar, va a ser igual a la clase Producto de "models.py"
		fields = ['sku', 'product_name', 'category', 'stock', 'ean'] 

		labels = {
            'sku':'SKU',
			'product_name':'Nombre del producto',
            'category':'Categoría',
			'stock':'Stock',
            'ean':'EAN',
		}

class product_edit_form(forms.ModelForm):
    class Meta:
        model = models.product
        fields = ['product_name', 'category', 'stock', 'ean']

        labels = {
            'product_name': 'Nombre del producto',
            'category': 'Categoría',
            'stock': 'Stock',
            'ean': 'EAN',
        }
		

class derivated_sku_form(forms.ModelForm): #Esta clase va a representar el producto, va a heredar de "forms.ModelForm"
	class Meta: #Esta clase va a contener los campos o elementos que queremos mostrar en el form.
		model = models.derivated_sku #El model que vamos a usar, va a ser igual a la clase Producto de "models.py"
		fields = ['sku'] 

		labels = {
            'sku':'SKU derivado',
		}

class BaseDerivatedFormSet(BaseFormSet):
    def clean(self):
        """Checks for duplicate skus across all forms in the formset."""
        
        # If an individual form already has errors, skip cross-form validation
        if any(self.errors):
            return

        skus = set()
        for form in self.forms:
            
            if self.can_delete and self._should_delete_form(form):
                continue

            if not form.has_changed():
                continue

            sku = form.cleaned_data.get('sku')
            if sku in skus:
                raise ValidationError("Sku derivado repetido en formulario.")
            skus.add(sku)