import json
import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import ml_credentials, api_error
from pathlib import Path
from django.db import transaction #module that provides a few ways to control how database transactions are managed.
#Django’s default transaction behavior:
#Django’s default behavior is to run in autocommit mode. Each query is immediately committed to the database, unless a transaction is active. Django uses transactions or savepoints automatically to guarantee the integrity of ORM operations that require multiple queries, especially delete() and update() queries.

from django.http import HttpResponse
from django.utils import timezone

def create_api_error(response):
    api_error.objects.create(
        api_status_code=response.status_code,
        api_response_text=response.text,
        api_response_url=response.url,
    )


def ml_refresh_token(user_id):
    #---- REFRESH TOKEN ----

    #Ten en cuenta que el access token generado expirará transcurridas 6 horas desde que se solicitó. Por eso, para asegurar que puedas trabajar por un tiempo prolongado y no sea necesario solicitar constantemente al usuario que se vuelva a loguear para generar un token nuevo, te brindamos la solución de trabajar con un refresh token. Además, recuerda que el refresh_token es de uso único y recibirás uno nuevo en cada proceso de actualización del token.

    #atomic() Atomicity is the defining property of database transactions. atomic allows us to create a block of code within which the atomicity on the database is guaranteed. If the block of code is successfully completed, the changes are committed to the database. If there is an exception, the changes are rolled back. 
    #En este caso, el bloque sería todo lo que encierra 'transaction.atomic()', en lugar de hacer un autocommit a los queries de inmediato (Como lo hace django tradicionalmente), esta atomicidad va a asegurar que los cambios a la base de datos se completen si el bloque de código se completa con exito.

    with transaction.atomic():
        #Los workers bloqueados esperaran aquí hasta que el worker encargado de refrescar el refresh_token termine.

        ml_creds = ml_credentials.objects.select_for_update().get(user_id=user_id) #select_for_update: Returns a queryset that will lock rows until the end of the transaction (la transaction.atomic()), generating a SELECT ... FOR UPDATE SQL statement on supported databases. Esencialmente, cuando llegue un worker, esto va a poner un lock en las credenciales de mercado libre dentro de la tabla de base de datos 'ml_credentials', para que este worker Y SOLO ESTE WORKER pueda actualizar las credenciales de mercado libre.

        #Esto va a evitar que múltiples workers concurrentes intenten actualizar las credenciales de mercado libre y se generen errores. Los workers bloqueado van a esperar en la línea anterior hasta que el worker elegido haya terminado.

        if not ml_creds.is_expired(): #Esto es para los workers bloqueados que estaban esperando. Van a confirmar que el access_token ya fue renovado y lo van a recoger. Para ellos, la función terminara aquí.
            print('')
            print('access_token ya fue restaurado')
            print('')
            return ml_creds.access_token


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

def get_order_data(order_id):
    #---- BUSCAR ÓRDENES ----

    #Una orden es una solicitud que realiza un cliente para una publicación con intención de comprarlo conforme a una serie de condiciones que seleccionará en el flujo del proceso de compra (checkout). Todas las condiciones de la venta se detallan en la orden, la cual se replicará para las cuentas del comprador y el vendedor.

    #Recuerda que actualmente se guardan órdenes creadas hasta 12 meses y si realizas la búsqueda como vendedor, filtras órdenes canceladas.

    access_token = ml_access_token() #Se llama a la función para obtener y/o renovar el access_token de mercado libre

    headers = {
        'Authorization': f'Bearer {access_token}',
    }


    response = requests.get(f'https://api.mercadolibre.com/orders/{order_id}', headers=headers)
    return response

def get_pack_data(pack_id):
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

def get_shipping_items(shipping_id):
    access_token = ml_access_token() #Se llama a la función para obtener y/o renovar el access_token de mercado libre

    headers = {
        'Authorization': f'Bearer {access_token}',
        'x-format-new': 'true',
    }

    response = requests.get(f'https://api.mercadolibre.com/shipments/{shipping_id}/items', headers=headers)

    return response  


def get_max_dispatch_time(shipping_id):
    access_token = ml_access_token() #Se llama a la función para obtener y/o renovar el access_token de mercado libre

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(f'https://api.mercadolibre.com/shipments/{shipping_id}/sla', headers=headers)
    return response




def get_shipment_label(shipping_ids_string, logistic_type):
    
    access_token = ml_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    url = f'https://api.mercadolibre.com/shipment_labels?shipment_ids={shipping_ids_string}&response_type=pdf'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        #Aquí se crea el objeto HttpResponse, el cuál vamos a usar para entregarle el pdf al browser y lo procese.

        #El primer parámetro es el contenido crudo del archivo pdf como bytestring, no hay necedidad de entenderlo, es solo para que lo procese la máquina.
        #content_type --> It tells the user's web browser what kind of data it is receiving before it tries to process it. The browser instantly recognizes it as a PDF document.
        FileHttpResponse = HttpResponse(response.content, content_type='application/pdf')

        filename = f"etiquetas_ml_{logistic_type}_{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}.pdf"
        FileHttpResponse['Content-Disposition'] = f'attachment; filename="{filename}"'
        #The HTTP Content-Disposition header indicates whether content should be displayed inline in the browser as a web page or part of a web page or downloaded as an attachment locally. The first parameter in the HTTP context is either inline (default value, indicating it can be displayed inside the Web page, or as the Web page) or attachment (indicating it should be downloaded, que es justamente el que uso).

        #También aprovecho de usar el parámetro 'filename' para ponerle nombre al archivo.
        
        #The HTTP Content Disposition is a response-type header field that gives information on how to process the response payload and additional information such as filename when user saves it locally.

        return FileHttpResponse
        
    else:
        create_api_error(response)
        return None


def get_user_data(user_id):
    access_token = ml_access_token() #Se llama a la función para obtener y/o renovar el access_token de mercado libre

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(f'https://api.mercadolibre.com/users/{user_id}', headers=headers)

    return response