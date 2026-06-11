import json
from django.conf import settings
from datetime import date, datetime
from .models import marketplace, order, order_product
from .ml_api_resources import search_orders, get_order_data, get_pack_data, get_shipping_data, get_shipping_items, get_max_dispatch_time, get_shipment_label, get_user_data, create_api_error
from django.db import transaction #module that provides a few ways to control how database transactions are managed.
#Django’s default transaction behavior:
#Django’s default behavior is to run in autocommit mode. Each query is immediately committed to the database, unless a transaction is active. Django uses transactions or savepoints automatically to guarantee the integrity of ORM operations that require multiple queries, especially delete() and update() queries.



def inspect_order_status(order_status):
    
    #---- Se verifica si la orden corresponde a un acuerdo de entrega y tiene status = paid (orden normal) o status = released (orden pack) ----
    if order_status != 'paid' and order_status != 'released':     
        return False

    return True


def inspect_logistic_type(shipping_dict):
    if shipping_dict['logistic']['type'] == 'cross_docking':
        logistic_type = 'collect'

    elif shipping_dict['logistic']['type'] == 'self_service':
        logistic_type = 'flex'

    else:
        print('La orden no es colecta ni flex')
        print('')
        return False

    return logistic_type


def inspect_estimated_dispatch_time(shipping_id):
    estimated_response = get_max_dispatch_time(shipping_id)
    if estimated_response.status_code != 200:
        create_api_error(estimated_response)
        print('Descartado por error en la api')
        print('')
        return False
    estimated_dict = json.loads(estimated_response.text)

    print(estimated_dict)

    try:
        expected_dispatch_time = datetime.fromisoformat(estimated_dict['expected_date'].replace('Z', '+00:00')).date()

    except:
        print('Descartado por no tener expected_dispatch_time')
        print('')
        return False

    return expected_dispatch_time


def inspect_shipping_status(shipping_dict):
    if shipping_dict['substatus'] == 'ready_to_print':
        shipping_status = 'ready_to_print'

    #substatus == 'ready_for_pickup' --> colecta
    #substatus == 'printed' --> flex
    elif shipping_dict['substatus'] == 'ready_for_pickup' or shipping_dict['substatus'] == 'printed':
        shipping_status = 'ready_to_ship'

    else:
        return False

    return shipping_status


def create_products_for_order(processing_order, order_items):

    for item in order_items:
        order_product.objects.create(
            order=processing_order,
            sku_seller=item['item'].get('seller_sku', ''),
            sku_marketplace=item['item']['id'],
            quantity=item['quantity'],
        )


def process_order(order_data, order_type):
    
    #get_or_create() --> A convenience method for looking up an object with the given kwargs (may be empty if your model has defaults for all fields), creating one if necessary. Returns a tuple of (object, created), where object is the retrieved or created object and created is a boolean specifying whether a new object was created.

    #get_or_create() Ayuda a prevenir duplicados, pero en el caso que reciba múltiples procesos concurrentes que quieran crear un objeto, no es suficiente. Para esto se debe aplicar 'uniqueness' a nivel de la base de datos. Si se revisa el archivo 'models.py' se puede ver que esto se aplica en el model 'order' en su clase 'meta', permitiendo que por cada marketplace no puedan existir múltiples órdenes con el mismo order_id.

    #En circunstancias normales, intentar crear objetos duplicados con 'uniqueness' aplicado, detonaría la excepción 'IntegrityError' y daría error en la ejecución, pero con get_or_create, detras de escena se capturaría esta excepción y se reintenta el get del objeto creado por el primer request.
    processing_order, new_order = order.objects.get_or_create(
        order_id=order_data['id'],
        marketplace=marketplace.objects.get(slug='mercado-libre'),
    )

    if order_type == 'normal_order':
        shipping_id = order_data['shipping']['id']

    elif order_type == 'pack_order':
        #Hay algunas ocasiones en donde el PACK nisiquiera tiene un key 'id' para el shipment definido, en su lugar, este se deja como un valor null --> "shipment":null
        try:
            shipping_id = order_data['shipment']['id']
        
        except:
            shipping_id = None

    print(shipping_id)

    if shipping_id is None:
        processing_order.delete()
        print('La orden no tiene shipping_id')
        print('')
        return

    
    #----- ES UNA ORDEN YA EXISTENTE EN LA BASE DE DATOS -----
    if not new_order:

        #atomic() Atomicity is the defining property of database transactions. atomic allows us to create a block of code within which the atomicity on the database is guaranteed. If the block of code is successfully completed, the changes are committed to the database. If there is an exception, the changes are rolled back. 
        #En este caso, el bloque sería todo lo que encierra 'transaction.atomic()', en lugar de hacer un autocommit a los queries de inmediato (Como lo hace django tradicionalmente), esta atomicidad va a asegurar que los cambios a la base de datos se completen si el bloque de código se completa con exito.
        
        with transaction.atomic():
            #select_for_update: Returns a queryset that will lock rows until the end of the transaction (la transaction.atomic()), generating a SELECT ... FOR UPDATE SQL statement on supported databases. Esencialmente, cuando llegue un worker, esto va a poner un lock para evitar 2 o más workers hagan actualización al mismo producto al mismo tiempo.

            #Tener en cuenta que select_for_update() no evita INSERTs (creaciones) concurrentes, solo bloquea registros en la base de datos si estos ya exitían con anterioridad en la base de datos. Es por esta razón que se tiene esto solo cuando se actualiza una orden. La creación concurrente de una misma órden se evita más arriba con el get_or_create y 'uniqueness' a nivel de base de datos. 
            
            try:
                processing_order = order.objects.select_for_update().get(order_id=processing_order.order_id)

            except order.DoesNotExist:
                print('Otro worker anterior ya elimino esta orden, saliendo')
                print('')
                return

            #VER SI ES UNA ORDEN PAGADA
            if not inspect_order_status(order_data['status']):
                processing_order.delete()
                print('La orden no tiene status paid o released')
                print('')
                return
                
            #DETERMINAR STATUS DEL SHIPPING
            shipping_response = get_shipping_data(shipping_id)
            if shipping_response.status_code != 200:
                create_api_error(shipping_response)
                return
            shipping_dict = json.loads(shipping_response.text)

            shipping_status = inspect_shipping_status(shipping_dict)
            if not shipping_status:
                processing_order.delete()
                print('Orden descartada por status no valido')
                print('')
                return


            #SE ACTUALIZA EL STATUS DE LA ORDEN SI ES NECESARIO
            if processing_order.status != shipping_status:
                processing_order.status = shipping_status
                processing_order.save()

            print('Orden actualizada con exito.')
            print('')
            return True
        

    
    #----- ES UNA NUEVA ORDEN, NO ESTÁ EN LA BASE DE DATOS -----

    #VER SI ES UNA ORDEN PAGADA
    if not inspect_order_status(order_data['status']):
        processing_order.delete()
        print('La orden no tiene status paid o released')
        print('')
        return
    
    #DETERMINAR TIPO LOGÍSTICO
    shipping_response = get_shipping_data(shipping_id)
    if shipping_response.status_code != 200:
        processing_order.delete()
        create_api_error(shipping_response)
        return
    shipping_dict = json.loads(shipping_response.text)
    
    logistic_type = inspect_logistic_type(shipping_dict)
    if not logistic_type:
        processing_order.delete()
        return


    #DETERMINAR STATUS DEL SHIPPING
    shipping_status = inspect_shipping_status(shipping_dict)
    if not shipping_status:
        #transaction.set_rollback(True)
        processing_order.delete()
        print('Orden descartada por status no valido')
        print('')
        return


    #VER LA FECHA DE DESPACHO ESTIMADA DE LA ORDEN. SI NO ES PARA HOY O UNA FECHA ANTERIOR (Orden atrasada), LA ORDEN SE DESCARTA.
    expected_dispatch_time = inspect_estimated_dispatch_time(shipping_id)
    if not expected_dispatch_time:
        processing_order.delete()
        return
    

    #LA DATA DEL PACK NO TIENE EL NICKNAME DEL CLIENTE POR DEFECTO, ASÍ QUE SE OBTIENE VÍA API.
    if order_type == 'pack_order':
        user_data_response = get_user_data(order_data['buyer']['id'])
        if user_data_response.status_code != 200:
            processing_order.delete()
            create_api_error(user_data_response)
            return
        user_data_dict = json.loads(user_data_response.text)
        client_nickname = user_data_dict['nickname']
    
    else:
        client_nickname = order_data['buyer']['nickname']


    #ACTUALIZAR ORDEN RECIÉN CREADA
    processing_order.shipping_id = shipping_id
    processing_order.logistic_type = logistic_type
    processing_order.client_nickname = client_nickname
    processing_order.status = shipping_status
    processing_order.creation_date_time = order_data['date_created']
    processing_order.estimated_pickup_time = expected_dispatch_time
    processing_order.marketplace = marketplace.objects.get(slug='mercado-libre')

    processing_order.save()

    #Se crean los registros de los productos asociados a la orden
    if order_type == 'normal_order':
        create_products_for_order(processing_order, order_data['order_items'])


    elif order_type == 'pack_order':

        for individual_order_id in order_data['orders']:
            individual_order_response = get_order_data(individual_order_id['id'])
            if individual_order_response.status_code != 200:
                processing_order.delete()
                create_api_error(individual_order_response)
                return
            individual_order_data = json.loads(individual_order_response.text)
            create_products_for_order(processing_order, individual_order_data['order_items'])

    print('Orden creada con exito.')
    print('')
    return True



def process_notification(notification_data):
    topic = notification_data['topic']
    resource = notification_data['resource']


    if topic == 'orders_v2':
        order_id = resource.split('/')[-1]

        #---- Determinar si el order_id corresponde a un 'pack' o a una orden normal----
        order_response = get_order_data(order_id)    

        if order_response.status_code == 200: #Es orden normal
            order_data = json.loads(order_response.text)

            if order_data['pack_id'] is not None: #Si es que la orden pertenece a un PACK
                pack_response = get_pack_data(order_data['pack_id'])
                if pack_response.status_code != 200:
                    create_api_error(pack_response)
                    return
                order_data = json.loads(pack_response.text)
                print('')
                print('orders_v2: Procesando PACK: ', str(order_data['id']))

                order_type = 'pack_order'
            
            else:
                print('')
                print('orders_v2: Procesando orden: ', str(order_data['id']))

                order_type = 'normal_order'


        elif order_response.status_code == 404:
            pack_response = get_pack_data(order_id)

            if pack_response.status_code == 200: #Es PACK
                order_data = json.loads(pack_response.text)
                print('')
                print('orders_v2: Procesando PACK: ', str(order_data['id']))

                order_type = 'pack_order'

            else:
                create_api_error(pack_response)
                return

        else:
            create_api_error(order_response)
            return

    elif topic == 'shipments':
        shipping_id = resource.split('/')[-1]

        shipping_items_response = get_shipping_items(shipping_id)
        if shipping_items_response.status_code != 200:
            create_api_error(shipping_items_response)
            return
        shipping_items_data = json.loads(shipping_items_response.text)

        order_id = shipping_items_data[0]['order_id'] #Los items de un shipping solo considera órdenes normales, por lo que se toma la primera orden (puede ser cualquiera en realidad) y este se va a usar para determinar si pertenece a un PACK o no.
        order_response = get_order_data(order_id)
        if order_response.status_code != 200:
            create_api_error(order_response)
            return
        order_data = json.loads(order_response.text)

        if order_data['pack_id'] is not None: #Si es que la orden pertenece a un PACK

            pack_response = get_pack_data(order_data['pack_id'])
            if pack_response.status_code != 200:
                create_api_error(pack_response)
                return
            order_data = json.loads(pack_response.text)
            print('')
            print('shipments: Procesando PACK: ', str(order_data['id']))
            
            order_type = 'pack_order'

        else:
            print('')
            print('shipments: Procesando orden: ', str(order_data['id']))

            order_type = 'normal_order'
            
    process_order(order_data, order_type)



def manual_update_ml_orders():

    offset_value = 0
    orders_response = search_orders(offset_value) #El recurso 'Buscar Ordenes' de la API de mercado libre, va a traer las ordenes validas para ingresar y actualizar dentro de este software. Hay que tener en cuenta que este recurso NO trae las órdenes PACK de manera exlicita, pero si trae las ordenes individuales contenidas en estas, por lo que se pueden obtener los PACKs a través de estas.

    if orders_response.status_code != 200:
        create_api_error(orders_response)
        return

    orders_dict = json.loads(orders_response.text)
    total_orders = orders_dict['paging']['total']
    

    valid_orders_ids = set()  #Recolecta IDs devueltos por la API. Este set se va a usar para contener las ids de todas las ordenes validas (Que se consideran para hoy de mercado libre) recibidas por la api de mercado libre. Toda orden que exista dentro de la base de datos de este software, pero que no tenga su id registrada en este set, será eliminada. Esto es para actualizar las ordenes actuales dentro de este software, eliminando las ordenes que ya no tienen status válidos. También se usará para evitar que se evalue un PACK múltiples veces.

    while True:

        for order_data in orders_dict['results']:
            
            if order_data['pack_id'] is not None: #Si es que la orden individual pertenece a un PACK
                #Si el PACK ya fue evaluado.
                if order_data['pack_id'] in valid_orders_ids:
                    continue

                pack_response = get_pack_data(order_data['pack_id'])
                if pack_response.status_code != 200:
                    create_api_error(pack_response)
                    continue
                order_data = json.loads(pack_response.text)
                print('')
                print('Procesando PACK: ', str(order_data['id']))
                process_order_bool = process_order(order_data, 'pack_order')                
            
            else:
                print('')
                print('Procesando orden: ', str(order_data['id']))
                process_order_bool = process_order(order_data, 'normal_order')


            if process_order_bool:
                valid_orders_ids.add(str(order_data['id']))  #registra cada ID


        offset_value += 51 #El recurso "Buscar Ordenes" de mercado libre tiene un límite de 51 items, es por esto que se le tiene que sumar al offset y llamar al recurso denuevo si se requieren más órdenes aparte de las primeras 51.

        orders_response = search_orders(offset_value)
        if orders_response.status_code != 200:
            create_api_error(orders_response)
            return
        orders_dict = json.loads(orders_response.text)

        if not orders_dict['results']: #Si el recurso 'Buscar Órdenes' de la API de mercado libre entrego una lista de órdenes vacía.
            break

    order.objects.filter(marketplace=marketplace.objects.get(slug='mercado-libre')).exclude(order_id__in=valid_orders_ids).delete() #Finalmente, se eliminan las ordenes dentro del sistema que no entrego el recurso de la api de mercado libre "buscar ordenes".

    
def print_ml_orders(organized_ml_orders):

    shipping_ids_string = str(list(organized_ml_orders.values_list('shipping_id', flat=True))).replace(" ", "").replace("'", "")[1:-1]
    #values_list() --> Returns a QuerySet as a tuple. Las tuplas en Python son un tipo o estructura de datos que permite almacenar datos de una manera muy parecida a las listas, con la salvedad de que son inmutables.

    #flat=True --> If you only pass in a single field, you can also pass in the flat parameter. If True, this will mean the returned results are single values, rather than 1-tuples. An example should make the difference clearer:
    #Sin flat: <QuerySet[(1,), (2,), (3,), ...]>
    #Con flat: <QuerySet [1, 2, 3, ...]>

    #str(list()).replace(" ", "") --> Primero se va a convertir en lista para que sea mutable, luego se converira a string.
    #Antes: <QuerySet [1, 2, 3, ...]>
    #Después: "[1,2,3,...]"

    #[1:-1] --> Finalmente, se quitarán los corchetes de la lista. Con esto, los shippings ids tendrán el formato para ser aceptado por el recurso de impresión de etiquetas de API de ML.

    get_shipment_label(shipping_ids_string)