from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F, Min, Count, Q #Min() function is used to find the minimun value of a particular field
from .models import order, marketplace, orders_group, order_product, direct_orders_update_log
from .forms import finish_orders_group_form
from products.models import product, derivated_sku
from django_q.tasks import async_task
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import date
from django.views.decorators.http import require_POST #The decorators in django.views.decorators.http can be used to restrict access to views based on the request method. These decorators will return a django.http.HttpResponseNotAllowed if the conditions are not met. Para este caso solo usaremos de las requests de tipo POST.
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib import messages
import json
from django_q.models import OrmQ
from django.db import transaction


@csrf_exempt 
@require_POST #Decorator to require that a view only accepts the POST method.
@login_not_required
def ml_webhook(request): #Este view recibe las notificaciones de mercado libre, para luego ser procesados asincrónicamente.

    notification_data = json.loads(request.body)

    async_task('orders.async_functions.process_notification', notification_data) #Aquí se van a procesar las notificaciones de manera asincrónica y paralela.

    return HttpResponse(status=200) #Se debe responder rapidamente a mercado libre con una respuesta '200' (En menos de 0.5 segundos) o mercado libre va a desactivar las notificaciones por 'fallback'

# ML no envía CSRF token. Sin @csrf_exempt, Django rechazaría todos los webhooks de ML con un 403 Forbidden porque no incluyen el token 

#A good example where @csrf_exempt is used is to build a webhook, that will receive informations from another site via a POST request. You then must be able to receive data even if it has no csrf token. *Quizás se podría agregar seguridad a esto.



# Create your views here.
#Este view va a recibir data a través de una solicitud POST de javascript Fetch Api
@require_POST #Decorator to require that a view only accepts the POST method.
def scanned_order_label(request, group_id):
    group_instance = get_object_or_404(orders_group, id=group_id)

    data = json.loads(request.body)
    label_data = data.get('label_data_json')
    
    #Si es que viene de un ML Flex
    try:
        label_data = json.loads(label_data)
        shipping_id = label_data['id']

    #Si es que viene de un ML Colecta
    except:
        shipping_id = label_data

    '''
    if group_instance.logistic_type == 'collect':
        shipping_id = label_data

    elif group_instance.logistic_type == 'flex':
        #print(label_data)
        label_data = json.loads(label_data)

        try:
            shipping_id = label_data['id']

        except:
            return JsonResponse({'error': 'Esta etiqueta no corresponde a un pedido flex'})
    '''

    try:
        order_instance = order.objects.get(shipping_id=shipping_id)

    except order.DoesNotExist:
        return JsonResponse({'error': 'No se encontro la orden vinculada a esta etiqueta dentro de este sistema'})

    else:
        if order_instance.orders_group != group_instance:
                return JsonResponse({
                    'error': 'La orden vinculada a esta etiqueta no pertencece al grupo de pedido actual'})

        redirect_url = reverse('orders:prepare_order', kwargs={'group_id': group_id, 'id': order_instance.id})
        return JsonResponse({'redirect_url': redirect_url})


@require_POST #Decorator to require that a view only accepts the POST method.
def scan_product_ean(request, id):
    order_instance = order.objects.get(id=id)
    group_instance = orders_group.objects.get(id=order_instance.orders_group.id)

    scanned_ean = request.POST.get('barcode') #request.POST.get() is a method used to safely retrieve data submitted from an HTML form via an HTTP POST request.

    try:
        product_instance = product.objects.get(ean=scanned_ean)
    except product.DoesNotExist:
        response = HttpResponse('El código escaneado no está registrado en sistema', status=400)
        return response

    derivated_skus = derivated_sku.objects.filter(local_product=product_instance).values_list('sku', flat=True)
    matching_skus = [product_instance.sku, *derivated_skus]
    #El * es el operador de "unpacking" (desempaquetado) de Python. derivated_skus es un queryset/iterable (por values_list('sku', flat=True)) con cero o más strings de SKU. *derivated_skus expande esos elementos individualmente dentro de la lista 'matching_skus'.

    #Sin desempaquetado (*):
    #matching_skus --> ["YEP1015", ["YEP1015R", "YEP1015B"]]

    #Con desempaquetado (*):
    #matching_skus --> ["YEP1015", "YEP1015R", "YEP1015B"]

    matching_order_products = order_product.objects.filter(order=order_instance, sku_seller__in=matching_skus) #Query que contiene los objetos 'order_product' ralacionado a la orden actual y en donde su campo 'sku_seller' esté contenido dentro de la lista 'matching_skus'. Este query va a contener el producto base de la orden y su skus derivados si es que existen.

    order_product_instance = matching_order_products.filter(quantity_scanned__lt=F('quantity')).order_by('id').first() #Dentro del query recién creado, se va a tomar el 'order_product' que tenga su campo 'quantity_scanned' menor a su campo 'quantity'...

    if order_product_instance is None: #En el caso en que el producto escaneado no esté relacionado a la orden
        #En el caso en que el producto escaneado esté relacionado a la orden, pero ya fue completado (quantity_scanned=quantity).
        if matching_order_products.exists():
            response = HttpResponse('Este producto ya fue completado para esta orden', status=400)
            return response

        #En el caso en que el producto escaneado no esté relacionado a la orden.
        response = HttpResponse('La orden actual no contiene el producto del código escaneado', status=400)
        return response

    if product_instance.stock == 0 and order_product_instance.prepared_without_stock == False:
        response = HttpResponse(f'El producto {product_instance.sku} no tiene stock disponible', status=400)
        #response['HX-Trigger'] = 'noStock'
        response['No-Stock-product'] = json.dumps({'orderProductId': order_product_instance.id}) #Header personalizado del http request, aquí se pasará JSON con el id del 'order_product' sin stock. Esto se procesará en el archivo JS, dentro del evento 'htmx:responseError'.
        return response


    order_product_instance.quantity_scanned += 1
    order_product_instance.save()

    if order_product_instance.prepared_without_stock == False:
        product_instance.stock -= 1
        product_instance.save()

    order_fully_scanned = not order_product.objects.filter(order=order_instance).exclude(quantity_scanned=F('quantity')).exists()

    if order_fully_scanned:
        order_instance.status = 'prepared'
        order_instance.save()
        
        redirect_url = reverse('orders:order_group', kwargs={'id': group_instance.id})
        response = HttpResponse(status=200)
        response['HX-Redirect'] = redirect_url
        return response
    

    context = {
        'order': order_instance,
        'order_group': group_instance,
    }

    return render(request, 'orders/partials/scanned_order.html', context)


def orders(request, slug):
    marketplace_instance = marketplace.objects.get(slug=slug)
    today = timezone.now()

    try:
        update_log_in_progress = direct_orders_update_log.objects.get(marketplace=marketplace_instance, finished=False)
    except:
        update_log_in_progress = None

    #Estos son los contadores totales para la ordenes de mercado libre, se van a mostrar en el template.
    collect_ready_to_print = order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='collect', status='ready_to_print')
    collect_ready_to_ship = order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='collect', status='ready_to_ship')
    flex_ready_to_print = order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='flex', status='ready_to_print')
    flex_ready_to_ship = order.objects.filter(estimated_pickup_time__lte=today, marketplace=marketplace_instance, logistic_type='flex', status='ready_to_ship')

    products_sku_set = product.objects.values_list('sku', flat=True)
    derivated_skus_set = derivated_sku.objects.values_list('sku', flat=True)
    out_of_stock_skus_set = product.objects.filter(stock=0).values_list('sku', flat=True)
    out_of_stock_derivated_skus_set = derivated_sku.objects.filter(local_product__stock=0).values_list('sku', flat=True)


    #En esta lista, se va a almacenar diccionarios con la data necesaria para renderizar las ordenes de cada tipo/status de mercado libre de hoy. Cada diccionario de la lista representa un grupo de data, en este caso hay un diccionario para colecta y otro para flex. Independiente del diccionario, todos usan la misma estructura html, esto se hace esencialmente para evitar escribir html redundante.
    #Cada diccionario contiene: 
    # El nombre para el id del div.
    # El query con los registros de ordenes para el respectivo tipo logístico y status.
    orders_queries_dict = []
    #El diccionario parte vacío, solo se agregan elementos si es que los queries de ordenes existen. Esto se hace para solo renderizar el contenido disponible (las queries que tienen objetos 'order') en el template.
    
    if collect_ready_to_print.count() > 0:
        orders_queries_dict.append(
            {
                'div_id': 'ml_collect_orders_print',
                'orders_query': collect_ready_to_print.order_by('-creation_date_time'),
            },
        )

    if collect_ready_to_ship.count() > 0:
        orders_queries_dict.append(
            {
                'div_id': 'ml_collect_orders_ship',
                'orders_query': collect_ready_to_ship.order_by('-creation_date_time'),
            },
        )

    if flex_ready_to_print.count() > 0:
        orders_queries_dict.append(
            {
                'div_id': 'ml_flex_orders_print',
                'orders_query': flex_ready_to_print.order_by('-creation_date_time'),
            },
        )

    if flex_ready_to_ship.count() > 0:
        orders_queries_dict.append(
            {
                'div_id': 'ml_flex_orders_ship',
                'orders_query': flex_ready_to_ship.order_by('-creation_date_time'),
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
    organized_ml_collect = collect_ready_to_print.annotate(sku=Min('order_product__sku_seller')).order_by('sku')

    if organized_ml_collect.exists():
        organized_orders_dict.append({
            'div_id': 'collect_labels_modal',
            'orders_query': organized_ml_collect,
            'btn_name': 'print_collect_orders',
        })

    #Esto contendrá las órdenes organizadas por SKU para flex que necesitan imprimirse.
    organized_ml_flex = flex_ready_to_print.annotate(sku=Min('order_product__sku_seller')).order_by('sku')

    if organized_ml_flex.exists():
        organized_orders_dict.append({
            'div_id': 'flex_labels_modal',
            'orders_query': organized_ml_flex,
            'btn_name': 'print_flex_orders',
        })



    if request.method == 'POST' and 'update_today_orders' in request.POST:

        with transaction.atomic():
            # Bloquea la fila de este marketplace hasta que termine la transacción.
            # Así, si dos requests llegan casi al mismo tiempo, la segunda espera
            # a que la primera haga commit antes de poder leer/escribir.
            locked_marketplace = marketplace.objects.select_for_update().get(pk=marketplace_instance.pk)

            if direct_orders_update_log.objects.filter(marketplace=locked_marketplace, finished=False).exists():
                messages.error(request, 'Ya hay una actualización manual en progreso.')
                return redirect('orders:orders', slug=marketplace_instance.slug)

            direct_orders_update_log.objects.create(marketplace=locked_marketplace)

        messages.success(request, 'Actualización de órdenes de mercado libre iniciado con éxito.')
        async_task(f"orders.async_functions.manual_update_ml_orders")
        return redirect('orders:orders', slug=marketplace_instance.slug)


    if request.method == 'POST' and 'print_collect_orders' in request.POST:

        if direct_orders_update_log.objects.filter(marketplace=marketplace_instance, finished=False).exists():
            messages.error(request, 'No puedes imprimir cuando hay una actualización manual de órdenes en progreso.')
            return redirect('orders:orders', slug=marketplace_instance.slug)

        async_task(f"orders.async_functions.print_ml_orders", organized_ml_collect)



    if request.method == 'POST' and 'print_flex_orders' in request.POST:

        if direct_orders_update_log.objects.filter(marketplace=marketplace_instance, finished=False).exists():
            messages.error(request, 'No puedes imprimir cuando hay una actualización manual de órdenes en progreso.')
            return redirect('orders:orders', slug=marketplace_instance.slug)

        async_task(f"orders.async_functions.print_ml_orders", organized_ml_flex)


    if request.method == 'POST' and 'collect_prepare_btn' in request.POST:
        
        if direct_orders_update_log.objects.filter(marketplace=marketplace_instance, finished=False).exists():
            messages.error(request, 'No puedes preparar pedidos cuando hay una actualización manual de órdenes en progreso.')
            return redirect('orders:orders', slug=marketplace_instance.slug)

        
        group = orders_group.objects.create(marketplace=marketplace_instance, logistic_type='collect', created_by = request.user)
        collect_ready_to_ship.update(orders_group=group, status='preparing')
        messages.success(request, 'Grupo de pedidos iniciado con éxito.')
        return redirect('orders:order_group', id=group.id)


    if request.method == 'POST' and 'flex_prepare_btn' in request.POST:

        if direct_orders_update_log.objects.filter(marketplace=marketplace_instance, finished=False).exists():
            messages.error(request, 'No puedes preparar pedidos cuando hay una actualización manual de órdenes en progreso.')
            return redirect('orders:orders', slug=marketplace_instance.slug)

        group = orders_group.objects.create(marketplace=marketplace_instance, logistic_type='flex', created_by = request.user)
        flex_ready_to_ship.update(orders_group=group, status='preparing')
        messages.success(request, 'Grupo de pedidos iniciado con éxito.')
        return redirect('orders:order_group', id=group.id)


    context = {
        'marketplace_instance': marketplace_instance,
        'orders_queries_dict': orders_queries_dict,
        'collect_ready_to_print': collect_ready_to_print,
        'collect_ready_to_ship': collect_ready_to_ship,
        'flex_ready_to_print': flex_ready_to_print,
        'flex_ready_to_ship': flex_ready_to_ship,
        'organized_orders_dict': organized_orders_dict,
        'products_sku_set': products_sku_set,
        'derivated_skus_set': derivated_skus_set,
        'out_of_stock_skus_set': out_of_stock_skus_set,
        'out_of_stock_derivated_skus_set': out_of_stock_derivated_skus_set,
        'update_log_in_progress': update_log_in_progress,
    }

    return render(request, 'orders/orders.html', context)

def order_group(request, id):
    order_group_instance = get_object_or_404(orders_group, id=id)
    group_orders = order.objects.filter(orders_group=order_group_instance)
    prepared_orders_count = group_orders.filter(status='prepared').count()
    total_orders_count = group_orders.count()

    products_sku_set = product.objects.values_list('sku', flat=True)
    derivated_skus_set = derivated_sku.objects.values_list('sku', flat=True)
    out_of_stock_skus_set = product.objects.filter(stock=0).values_list('sku', flat=True)
    out_of_stock_derivated_skus_set = derivated_sku.objects.filter(local_product__stock=0).values_list('sku', flat=True)



    if request.method == 'POST' and 'confirm-order-processing' in request.POST:
        
        if order_group_instance.status == 'prepared' or prepared_orders_count == 0:
            messages.error(request, 'No puedes procesar este grupo.')
            return redirect('orders:order_group', id=order_group_instance.id)
        
        if prepared_orders_count < total_orders_count:

            for order_instance in group_orders.exclude(status='prepared'):
                if order_product.objects.filter(order=order_instance, quantity_scanned__gt=0).exists():
                    order_instance.status = 'partially_prepared'
                else:
                    order_instance.status = 'not_prepared'
                order_instance.save()

        order_group_instance.status = 'prepared'
        order_group_instance.prepared_date_time = timezone.now()
        order_group_instance.prepared_by = request.user
        order_group_instance.save()

        messages.success(request, 'Grupo preparado con éxito.')
        return redirect('orders:order_group', id=order_group_instance.id)

    context = {
        'order_group_instance': order_group_instance,
        'group_orders': group_orders,
        'prepared_orders_count': prepared_orders_count,
        'total_orders_count': total_orders_count,
        'products_sku_set': products_sku_set,
        'derivated_skus_set': derivated_skus_set,
        'out_of_stock_skus_set': out_of_stock_skus_set,
        'out_of_stock_derivated_skus_set': out_of_stock_derivated_skus_set,
    }

    #Si es un get request de un elemento con atributos HTMX
    if request.headers.get('HX-Request'):
        #Este get request va a traer el html con el contenido parcial que consiste en las ordenes correspondientes al grupo de preparación. Este html va a ser solicitado mediante polling cada x segundos con la última data de estos de la base de datos, permitiendo la actualización automática del front-end.
        return render(request, 'orders/partials/order_group_htmx.html', context)

    return render(request, 'orders/order_group.html', context)


def finish_order_group(request, group_id):
    group_instance = get_object_or_404(orders_group, id=group_id)

    if group_instance.status != 'prepared':
        messages.error(request, f'No puedes finalizar este grupo')
        return redirect('orders:order_group', id=group_instance.id)

    if request.method == 'POST':
        form = finish_orders_group_form(request.POST, request.FILES, instance=group_instance)
        
        if form.is_valid():
            form.save()

            group_instance.status = 'finalized'
            group_instance.finalized_date_time = timezone.now()
            group_instance.finalized_by = request.user
            group_instance.save()

            messages.success(request, f'Grupo de órdenes correctamente finalizado')
            return redirect('orders:order_group', id=group_instance.id)

    else:
        form = finish_orders_group_form(instance=group_instance)
    
    context = {
        'group_instance': group_instance,
        'form': form,
    }

    return render(request, 'orders/finish_order_group.html', context)


def prepare_order(request, group_id, id):

    order_instance = get_object_or_404(order, id=id)
    group_instance = get_object_or_404(orders_group, id=group_id)

    if request.method == 'POST' and 'prepare-noStock-product' in request.POST:
        no_stock_order_product = order_product.objects.get(id = request.POST.get('product-id-without-stock'))
        no_stock_order_product.prepared_without_stock = True
        no_stock_order_product.save()

        messages.success(request, 'Ahora puedes preparar el producto sin stock')
        return redirect('orders:prepare_order', group_id=group_instance.id, id=order_instance.id)

    context = {
        'order': order_instance,
        'order_group': group_instance,
    }

    #Si es un get request de un elemento con atributos HTMX
    if request.headers.get('HX-Request'):
        return render(request, 'orders/partials/scanned_order.html', context)

    return render(request, 'orders/prepare_order.html', context)


def groups_of_orders(request, slug):
    marketplace_instance = marketplace.objects.get(slug=slug)
    groups_of_orders = orders_group.objects.annotate(
        prepared_count=Count('order', filter=Q(order__status='prepared'))
    ).order_by('-id')

    context = {
        'groups_of_orders': groups_of_orders,
        'marketplace_instance': marketplace_instance,
    }

    return render(request, 'orders/groups_of_orders.html', context)