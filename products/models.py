from django.core.exceptions import ValidationError
from django.db import models


class product_category(models.Model):
    category_name = models.CharField(max_length=255)
    priority_n = models.IntegerField()

    def __str__(self):
        return self.category_name


class product(models.Model):
    category = models.ForeignKey(
        product_category, on_delete=models.SET_NULL, null=True, blank=True
    )
    sku = models.CharField(unique=True, max_length=100)
    product_name = models.CharField(max_length=255)
    stock = models.IntegerField(default=0)
    ean = models.CharField(unique=True, max_length=50, blank=True, null=True)
    creation_date_time = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if derivated_sku.objects.filter(sku=self.sku).exists(): #Si es que se intenta definir el sku del producto con un sku ya existente como 'sku derivado'.
            raise ValidationError(
                {"sku": 'Este SKU ya se definio para un sku derivado.'}
            )

    def save(self, *args, **kwargs): #You can overwrite the save() method for personalized saving behaviour.
        self.full_clean()
        super().save(*args, **kwargs) # Call the "real" save() method.

    def __str__(self):
        return self.sku


class derivated_sku(models.Model):
    local_product = models.ForeignKey(
        product, on_delete=models.CASCADE, related_name="derivated_skus"
    )
    sku = models.CharField(unique=True, max_length=100)

    def clean(self): #This method should be used to provide custom model validation, and to modify attributes on your model if desired. For instance, you could use it to automatically provide a value for a field, or to do validation that requires access to more than a single field.

    #Tener en cuenta que este método se llama automáticamente en forms cuando se usa el .is_valid(), pero no cuando se usa el .save() dentro del código (Como en views.py por ejemplo). Para que este comportamiento se aplique en .save(), debemos sobreescribir el método del mismo nombre, como lo hacemos más abajo.

        if product.objects.filter(sku=self.sku).exists(): #Si es que un sku derivado es igual al sku de un producto base, levantara un ValidationError
            raise ValidationError(
                {"sku": f'No puedes definir un sku de un producto base como sku derivado.'}
            )

    def save(self, *args, **kwargs): #You can overwrite the save() method for personalized saving behaviour.
        self.full_clean()
        #Al igual que clean() este método se llama automáticamente en forms cuando se usa el .is_valid(), pero no cuando se usa el .save().

        #Cuando se llama full_clean, esto es lo que valida:
            #Validate the model fields - Model.clean_fields() -->This method will validate all fields on your model. The optional exclude argument lets you provide a set of field names to exclude from validation. It will raise a ValidationError if any fields fail validation.

            #Validate the model as a whole - Model.clean() --> El def clean que acabamos de definir.
            
            #Validate the field uniqueness - Model.validate_unique() -->This method is similar to clean_fields(), but validates uniqueness constraints defined via Field.unique, Field.unique_for_date, Field.unique_for_month, Field.unique_for_year, or Meta.unique_together on your model instead of individual field values.

            #Validate the constraints - Model.validate_constraints() --> This method validates all constraints defined in Meta.constraints.

        #De manera resumida, full_clean realiza una validación completa del model, independiente si se llama de un django form o de un .save(). Esto es especialmente importante para que nuestro clean() se aplique por ambos lados. Tener en cuenta que esto es solo a nivel de aplicación, no de base de datos. Si alguien inserta un registro con SQL directo, no se validará.

        super().save(*args, **kwargs) # Call the "real" save() method.

    def __str__(self):
        return self.sku
