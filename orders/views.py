from django.shortcuts import render
from django.db.models import Min #Min() function is used to find the minimun value of a particular field
from .models import order, marketplace
from django_q.tasks import async_task
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import date
from django.views.decorators.http import require_POST #The decorators in django.views.decorators.http can be used to restrict access to views based on the request method. These decorators will return a django.http.HttpResponseNotAllowed if the conditions are not met. Para este caso solo usaremos de las requests de tipo POST.
from django.http import HttpResponse
import json


# Create your views here.
@csrf_exempt 
@require_POST #Decorator to require that a view only accepts the POST method.
def ml_webhook(request): #Este view recibe las notificaciones de mercado libre, para luego ser procesados asincrónicamente.

    notification_data = json.loads(request.body)

    async_task('orders.async_functions.process_notification', notification_data) #Aquí se van a procesar las notificaciones de manera asincrónica y paralela.

    return HttpResponse(status=200) #Se debe responder rapidamente a mercado libre con una respuesta '200' (En menos de 0.5 segundos) o mercado libre va a desactivar las notificaciones por 'fallback'

# ML no envía CSRF token. Sin @csrf_exempt, Django rechazaría todos los webhooks de ML con un 403 Forbidden porque no incluyen el token 

#A good example where @csrf_exempt is used is to build a webhook, that will receive informations from another site via a POST request. You then must be able to receive data even if it has no csrf token. *Quizás se podría agregar seguridad a esto.




def orders(request, slug):
    marketplace_instance = marketplace.objects.get(slug=slug)
    today = timezone.now()
    #today = date.today()
    print(today)

    #Estos son los contadores totales para la ordenes de mercado libre, se van a mostrar en el template.
    collect_ready_to_print_total = order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='collect', status='ready_to_print').count()
    collect_ready_to_ship_total = order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='collect', status='ready_to_ship').count()
    flex_ready_to_print_total = order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='flex', status='ready_to_print').count()
    flex_ready_to_ship_total = order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='flex', status='ready_to_ship').count()


    #En esta lista, se va a almacenar diccionarios con la data necesaria para renderizar las ordenes de cada tipo/status de mercado libre de hoy. Cada diccionario de la lista representa un grupo de data, en este caso hay un diccionario para colecta y otro para flex. Independiente del diccionario, todos usan la misma estructura html, esto se hace esencialmente para evitar escribir html redundante.
    #Cada diccionario contiene: 
    # El nombre para el id del div.
    # El query con los registros de ordenes para el respectivo tipo logístico y status.
    orders_queries_dict = []
    #El diccionario parte vacío, solo se agregan elementos si es que los queries de ordenes existen. Esto se hace para solo renderizar el contenido disponible (las queries que tienen objetos 'order') en el template.
    
    if collect_ready_to_print_total > 0:
        orders_queries_dict.append(
            {
                'div_id': 'ml_collect_orders_print',
                'orders_query': order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='collect', status='ready_to_print').order_by('-creation_date_time'),
            },
        )

    if collect_ready_to_ship_total > 0:
        orders_queries_dict.append(
            {
                'div_id': 'ml_collect_orders_ship',
                'orders_query': order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='collect', status='ready_to_ship').order_by('-creation_date_time'),
            },
        )

    if flex_ready_to_print_total > 0:
        orders_queries_dict.append(
            {
                'div_id': 'ml_flex_orders_print',
                'orders_query': order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='flex', status='ready_to_print').order_by('-creation_date_time'),
            },
        )

    if flex_ready_to_ship_total > 0:
        orders_queries_dict.append(
            {
                'div_id': 'ml_flex_orders_ship',
                'orders_query': order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='flex', status='ready_to_ship').order_by('-creation_date_time'),
            },
        )


    #En esta lista, se va a almacenar diccionarios con la data necesaria para renderizar las ordenes listas para imprimir cuando se active el modal para confirmar la impresión. Cada diccionario de la lista representa un grupo de data, en este caso hay un diccionario para colecta y otro para flex. Independiente del diccionario, todos usan la misma estructura html, esto se hace esencialmente para evitar escribir html redundante.
    organized_orders_dict = []
    #La lista parte vacía, solo se agregan diccionarios si es que la data correspondiente existe. Esto se hace para solo renderizar el contenido disponible en el template.
    #Cada diccionario contiene: 
    # El nombre para el id del div.
    # El query con los registros de ordenes ordenados por SKU del seller.
    # El nombre del botón para activar la solicitud post correspondiente. Hay un botón para colecta y otro para flex.

    #Esto contendrá las órdenes organizadas por SKU para colecta que necesitan imprimirse.
    organized_ml_collect = order.objects.filter(
        estimated_pickup_time__lte=today,
        marketplace=marketplace_instance,
        logistic_type='collect',
        status='ready_to_print'
    ).annotate(sku=Min('order_product__sku_seller')).order_by('sku')

    if organized_ml_collect.exists():
        organized_orders_dict.append({
            'div_id': 'collect_labels_modal',
            'orders_query': organized_ml_collect,
            'btn_name': 'print_collect_orders',
        })

    #Esto contendrá las órdenes organizadas por SKU para flex que necesitan imprimirse.
    organized_ml_flex = order.objects.filter(
        estimated_pickup_time__lte=today,
        marketplace=marketplace_instance,
        logistic_type='flex',
        status='ready_to_print'
    ).annotate(sku=Min('order_product__sku_seller')).order_by('sku')

    if organized_ml_flex.exists():
        organized_orders_dict.append({
            'div_id': 'flex_labels_modal',
            'orders_query': organized_ml_flex,
            'btn_name': 'print_flex_orders',
        })



    if request.method == 'POST' and 'update_today_orders' in request.POST:

        async_task(f"orders.async_functions.manual_update_ml_orders")



    if request.method == 'POST' and 'print_collect_orders' in request.POST:

        async_task(f"orders.async_functions.print_ml_orders", organized_ml_collect)



    if request.method == 'POST' and 'print_flex_orders' in request.POST:

        async_task(f"orders.async_functions.print_ml_orders", organized_ml_flex)

    context = {
        'marketplace_instance': marketplace_instance,
        'orders_queries_dict': orders_queries_dict,
        'collect_ready_to_print_total': collect_ready_to_print_total,
        'collect_ready_to_ship_total': collect_ready_to_ship_total,
        'flex_ready_to_print_total': flex_ready_to_print_total,
        'flex_ready_to_ship_total': flex_ready_to_ship_total,
        'organized_orders_dict': organized_orders_dict,
    }

    return render(request, 'orders/orders.html', context)