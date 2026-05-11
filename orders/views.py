from django.shortcuts import render
from .models import order, marketplace
from django_q.tasks import async_task

# Create your views here.
def orders(request, slug):
    marketplace_instance = marketplace.objects.get(slug=slug)

    collect_ready_to_print = order.objects.filter(marketplace=marketplace_instance, order_type='collect', status='ready_to_print')
    collect_ready_to_ship = order.objects.filter(marketplace=marketplace_instance, order_type='collect', status='ready_to_ship')
    flex_ready_to_print = order.objects.filter(marketplace=marketplace_instance, order_type='flex', status='ready_to_print')
    flex_ready_to_ship = order.objects.filter(marketplace=marketplace_instance, order_type='flex', status='ready_to_ship')

    if request.method == 'POST' and 'update_today_orders' in request.POST:

        async_task(f"orders.async_functions.update_today_ml_orders")

    context = {
        'marketplace_instance': marketplace_instance,
        'collect_ready_to_print': collect_ready_to_print,
        'collect_ready_to_ship': collect_ready_to_ship,
        'flex_ready_to_print': flex_ready_to_print,
        'flex_ready_to_ship': flex_ready_to_ship,
    }

    return render(request, 'orders/orders.html', context)