from django.shortcuts import render, redirect, get_object_or_404
from .models import product, derivated_sku
from .forms import product_create_form, product_edit_form, derivated_sku_form, BaseDerivatedFormSet
from django.forms import formset_factory, modelformset_factory
from django.contrib import messages


def products_catalogue(request):
    products = product.objects.all()

    context = {
        'products': products,
    }
    
    #messages.success(request, 'hola.')
    #messages.error(request, 'AAAAA.')
    return render(request, 'products/products_catalogue.html', context)



def create_product(request):
    #A formset is a layer of abstraction to work with multiple forms on the same page. It can be best compared to a data grid.
    DerivatedSkuFormSet = formset_factory(derivated_sku_form, formset=BaseDerivatedFormSet) #Se crea la clase del formset, permitiendo crear múltiples instancias de esta. Una instancia de esta clase permitrá crear múltiples forms 'derivated_sku_form'. El parámetro extra define la cantidad de forms vacíos a crear, en este caso se deja en 0 para cuando el usuario activa por primera vez este view.

    if request.method == 'POST':
        form = product_create_form(request.POST)
        formset = DerivatedSkuFormSet(request.POST, prefix='derivated') #In the rendered HTML, formsets include a prefix on each field’s name. By default, the prefix is 'form', but it can be customized using the formset’s prefix argument. name="form-0-title" --> name="derivated-0-title"

        if form.is_valid() and formset.is_valid():
            product_instance = form.save()
            for derivated_form in formset:
                if derivated_form.cleaned_data.get('sku'):
                    derivated = derivated_form.save(commit=False)
                    derivated.local_product = product_instance
                    derivated.save()
            return redirect('products:products_catalogue')

    else:
        form = product_create_form()
        formset = DerivatedSkuFormSet(prefix='derivated') #In the rendered HTML, formsets include a prefix on each field’s name. By default, the prefix is 'form', but it can be customized using the formset’s prefix argument. name="form-0-title" --> name="derivated-0-title"

    context = {
        'form': form, 
        'formset': formset,
    }
    return render(request, 'products/create_product.html', context)



def edit_product(request, id):
    product_instance = get_object_or_404(product, id=id)
    # modelformset_factory para manejar instancias existentes de BD
    ExistingDerivatedFormSet = modelformset_factory(derivated_sku, form=derivated_sku_form, can_delete=True, extra=0)
    NewDerivatedFormset = formset_factory(derivated_sku_form) #Se crea la clase del formset, permitiendo crear múltiples instancias de esta. Una instancia de esta clase permitrá crear múltiples forms 'derivated_sku_form'. El parámetro extra define la cantidad de forms vacíos a crear, en este caso se deja en 0 para cuando el usuario activa por primera vez este view.

    if request.method == 'POST':
        form = product_edit_form(request.POST, instance=product_instance)
        formset = NewDerivatedFormset(request.POST, prefix='derivated') #In the rendered HTML, formsets include a prefix on each field’s name. By default, the prefix is 'form', but it can be customized using the formset’s prefix argument. name="form-0-title" --> name="derivated-0-title"
        existing_derivated_formset = ExistingDerivatedFormSet(
            request.POST,
            queryset=derivated_sku.objects.filter(local_product=product_instance),
            prefix='existing-derivated'
        )
        if form.is_valid() and formset.is_valid() and existing_derivated_formset.is_valid():
            form.save()
            existing_derivated_formset.save()
            for derivated_form in formset:
                if derivated_form.cleaned_data.get('sku'):
                    derivated = derivated_form.save(commit=False)
                    derivated.local_product = product_instance
                    derivated.save()
            return redirect('products:products_catalogue')
    else:
        form = product_edit_form(instance=product_instance)
        formset = NewDerivatedFormset(prefix='derivated') #In the rendered HTML, formsets include a prefix on each field’s name. By default, the prefix is 'form', but it can be customized using the formset’s prefix argument. name="form-0-title" --> name="derivated-0-title"
        existing_derivated_formset = ExistingDerivatedFormSet(
            queryset=derivated_sku.objects.filter(local_product=product_instance),
            prefix='existing-derivated'
        )

    context = {
        'form': form,
        'formset': formset,
        'existing_derivated_formset': existing_derivated_formset,
        'product': product_instance,
    }
    return render(request, 'products/edit_product.html', context)