from django.shortcuts import render
from .models import order, marketplace
from django_q.tasks import async_task

# Create your views here.
def orders(request, slug):
    marketplace_instance = marketplace.objects.get(slug=slug)


    collect_ready_to_print_total = order.objects.filter(marketplace=marketplace_instance, order_type='collect', status='ready_to_print').count()

    collect_ready_to_ship_total = order.objects.filter(marketplace=marketplace_instance, order_type='collect', status='ready_to_ship').count()

    flex_ready_to_print_total = order.objects.filter(marketplace=marketplace_instance, order_type='flex', status='ready_to_print').count()

    flex_ready_to_ship_total = order.objects.filter(marketplace=marketplace_instance, order_type='flex', status='ready_to_ship').count()


    orders_queries_dict = [
        {
            'div_id': 'ml_collect_orders_print',
            'orders_query': order.objects.filter(marketplace=marketplace_instance, order_type='collect', status='ready_to_print').order_by('-creation_date_time'),
        },
        {
            'div_id': 'ml_collect_orders_ship',
            'orders_query': order.objects.filter(marketplace=marketplace_instance, order_type='collect', status='ready_to_ship').order_by('-creation_date_time'),
        },
        {
            'div_id': 'ml_flex_orders_print',
            'orders_query': order.objects.filter(marketplace=marketplace_instance, order_type='flex', status='ready_to_print').order_by('-creation_date_time'),
        },
        {
            'div_id': 'ml_flex_orders_ship',
            'orders_query': order.objects.filter(marketplace=marketplace_instance, order_type='flex', status='ready_to_ship').order_by('-creation_date_time'),
        },
    ]

    if request.method == 'POST' and 'update_today_orders' in request.POST:

        async_task(f"orders.async_functions.update_today_ml_orders")

    context = {
        'marketplace_instance': marketplace_instance,
        'orders_queries_dict': orders_queries_dict,
        'collect_ready_to_print_total': collect_ready_to_print_total,
        'collect_ready_to_ship_total': collect_ready_to_ship_total,
        'flex_ready_to_print_total': flex_ready_to_print_total,
        'flex_ready_to_ship_total': flex_ready_to_ship_total,
    }

    return render(request, 'orders/orders.html', context)