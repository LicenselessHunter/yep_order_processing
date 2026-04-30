from django.shortcuts import render
from .models import order, marketplace

# Create your views here.
def orders(request, slug):
    marketplace_instance = marketplace.objects.get(slug = slug)

    context = {
        'marketplace_instance':marketplace_instance,
    }
    

    return render(request, 'orders/orders.html', context)