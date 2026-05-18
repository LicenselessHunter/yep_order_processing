import json
import requests
from django.conf import settings
from django.utils import timezone
from datetime import date, datetime, timedelta
from .models import ml_credentials, marketplace, order, order_product



def ml_refresh_token(user_id):
    #---- REFRESH TOKEN ----

    #Ten en cuenta que el access token generado expirará transcurridas 6 horas desde que se solicitó. Por eso, para asegurar que puedas trabajar por un tiempo prolongado y no sea necesario solicitar constantemente al usuario que se vuelva a loguear para generar un token nuevo, te brindamos la solución de trabajar con un refresh token. Además, recuerda que el refresh_token es de uso único y recibirás uno nuevo en cada proceso de actualización del token.

    ml_creds = ml_credentials.objects.get(user_id=user_id)


    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
    }

    payload = {
        'grant_type': 'refresh_token', #refresh_token indica que la operación deseada es actualizar un token.
        'client_id': settings.ML_CLIENT_ID, #client_id que aparece en la página de credenciales de ML.
        'client_secret': settings.ML_CLIENT_SECRET, #client_secret que aparece en la página de credenciales de ML.
        'refresh_token': ml_creds.refresh_token #El refresh token que aparecio en la última respuesta de este mismo recurso, se deberá usar para generar un nuevo tojen una vez que el actual expire.
    }

    response = requests.post('https://api.mercadolibre.com/oauth/token', headers=headers, data=payload)

    if response.status_code == 200:
        token_data = response.json()
        ml_creds.access_token = token_data['access_token']
        ml_creds.refresh_token = token_data['refresh_token']
        ml_creds.expires_at = timezone.now() + timedelta(seconds=token_data['expires_in']) #Se toma el tiempo actual y se usa timedelta para sumarle los 21600 segundos (o 6 horas) con la fecha resultante siendo la fecha en donde va a expirar el nuevo access_token.
        ml_creds.save()
        print('')
        print('access_token restaurado :)')
        print('')

        return ml_creds.access_token


def ml_access_token():
    ml_creds = ml_credentials.objects.get(user_id=settings.ML_SELLER_ID)

    if ml_creds.is_expired():
        print('')
        print('access_token caducado :(')
        print('')
        access_token = ml_refresh_token(ml_creds.user_id)

    else:
        access_token = ml_creds.access_token

    return access_token

def search_orders(offset_value):

    access_token = ml_access_token() #Se llama a la función para obtener y/o renovar el access_token de mercado libre

    headers = {
        'Authorization': f'Bearer {access_token}',
    }


    #response = requests.get('https://api.mercadolibre.com/orders/search?seller=752198086&order.status=paid', headers=headers)

    response = requests.get(f'https://api.mercadolibre.com/orders/search?seller={settings.ML_SELLER_ID}&order.status=paid&shipping.substatus=ready_to_print,ready_for_pickup,printed&offset={offset_value}&sort=date_desc', headers=headers)

    return response


def get_pack(pack_id):
    access_token = ml_access_token() #Se llama a la función para obtener y/o renovar el access_token de mercado libre

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(f'https://api.mercadolibre.com/packs/{pack_id}', headers=headers)

    return response


def get_shipping_data(shipping_id):
    access_token = ml_access_token() #Se llama a la función para obtener y/o renovar el access_token de mercado libre

    headers = {
        'Authorization': f'Bearer {access_token}',
        'x-format-new': 'true',
    }

    response = requests.get(f'https://api.mercadolibre.com/shipments/{shipping_id}', headers=headers)

    return response  


def get_max_dispatch_time(shipping_id):
    access_token = ml_access_token() #Se llama a la función para obtener y/o renovar el access_token de mercado libre

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(f'https://api.mercadolibre.com/shipments/{shipping_id}/sla', headers=headers)
    return response



def update_today_ml_orders():

    offset_value = 0
    orders_response = search_orders(offset_value)

    orders_dict = json.loads(orders_response.text)
    total_orders = orders_dict['paging']['total']
    

    ml_marketplace = marketplace.objects.get(slug='mercado-libre')
    valid_orders_ids = set()  #Recolecta IDs devueltos por la API. Este set se va a usar para contener las ids de todas las ordenes validas (Que se consideran para hoy de mercado libre) recibidas por la api de mercado libre. Toda orden que exista dentro de la base de datos de este software, pero que no tenga su id registrada en este set, será eliminada. Esto es para actualizar las ordenes actuales dentro de este software, eliminado las ordenes que ya no tienen status válidos. 

    while True:

        for order_data in orders_dict['results']:

            #----- PROCESAR PACK -----
            if order_data['pack_id'] != None:
                
                try:
                    order.objects.get(order_id=order_data['pack_id'])

                except:
                    pack_response = get_pack(order_data['pack_id'])
                    pack_dict = json.loads(pack_response.text)

                    order_id = pack_dict['id']
                    shipping_id = pack_dict['shipment']['id']
                    created_date_time = pack_dict['date_created']

                else:
                    pack_order = order.objects.get(order_id=order_data['pack_id'])
                    order_id = pack_order.order_id
                    shipping_id = pack_order.shipping_id
                    created_date_time = pack_order.creation_date_time



            #----- EN CASO DE QUE SEA UNA ORDEN NO ASOCIADA A UN PACK -----
            else:
                order_id = order_data['id']
                shipping_id = order_data['shipping']['id']
                created_date_time = order_data['date_created']

            #SE RECOGE EL NICKNAME DEL USUARIO INDEPENDIENTE SI ES UN PACK O UNA ORDEN NORMAL
            client_nickname = order_data['buyer']['nickname']

            #----- DESCARTAR ORDENES QUE NO SON PARA DESPACHAR HOY -----
            estimated_response = get_max_dispatch_time(shipping_id)
            estimated_dict = json.loads(estimated_response.text)

            expected_dispatch_time = datetime.fromisoformat(estimated_dict['expected_date'].replace('Z', '+00:00')).date()
            today = date.today()

            if expected_dispatch_time > today:
                continue


            #----- DETERMINAR STATUS DE ORDEN ------
            shipping_response = get_shipping_data(shipping_id)
            shipping_dict = json.loads(shipping_response.text)

            if shipping_dict['logistic']['type'] == 'cross_docking':
                logistic_type = 'collect'

            elif shipping_dict['logistic']['type'] == 'self_service':
                logistic_type = 'flex'

            if shipping_dict['substatus'] == 'ready_to_print':
                order_status = 'ready_to_print'

            #substatus == 'ready_for_pickup' --> colecta
            #substatus == 'printed' --> flex
            elif shipping_dict['substatus'] == 'ready_for_pickup' or shipping_dict['substatus'] == 'printed':
                order_status = 'ready_to_ship'



            #------ CREATE ORDER ------
            processing_order, new_order = order.objects.get_or_create(
                order_id = str(order_id),
                defaults= {
                    'marketplace': ml_marketplace,
                    'shipping_id': str(shipping_id),
                    'order_type': logistic_type,
                    'client_nickname': client_nickname,
                    'status': order_status,
                    'creation_date_time': created_date_time,
                    'estimated_pickup_time': estimated_dict['expected_date'],
                }
            )
            
            if new_order:
                for order_item in order_data['order_items']:
                    order_product.objects.create(
                        order=processing_order,
                        sku_seller=order_item['item'].get('seller_sku', ''),
                        sku_marketplace=order_item['item']['id'],
                        quantity=order_item['quantity'],
                    )

            #------ UPDATE EXISTING ORDER IF NECESSARY-----
            if not new_order:
                
                #SI ES QUE ESTA ORDEN CORRESPONDE A UN PACK
                if order_data['pack_id'] != 'null':

                    for order_item in order_data['order_items']:
                        try: 
                            order_product.objects.get(order=processing_order, sku_marketplace=order_item['item']['id'])

                        except:
                            order_product.objects.create(
                                order=processing_order,
                                sku_seller=order_item['item'].get('seller_sku', ''),
                                sku_marketplace=order_item['item']['id'],
                                quantity=order_item['quantity'],
                            )
                
                if processing_order.status != order_status:
                    processing_order.status = order_status
                    processing_order.save()
            
            valid_orders_ids.add(str(order_id))  #registra cada ID

        offset_value += 51 #El recurso "Buscar Ordenes" de mercado libre tiene un límite de 51 items, es por esto que se le tiene que sumar al offset y llamar al recurso denuevo si se requieren más órdenes aparte de las primeras 51.

        orders_response = search_orders(offset_value)
        orders_dict = json.loads(orders_response.text)

        if not orders_dict['results']:
            break

    order.objects.filter(marketplace=ml_marketplace).exclude(order_id__in=valid_orders_ids).delete() #Finalmente, se eliminan la ordenes dentro del sistema que no entrego el recurso de la api de mercado libre "buscar ordenes".