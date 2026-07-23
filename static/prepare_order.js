/* En este diccionario se usa la biblioteca JS 'html5-qrcode', el cuál permite renderizar un escaner de códigos QR y otros tipos de códigos. Documentación: https://github.com/mebjas/html5-qrcode */
const activate_scan_btn = document.getElementById('activate-product-scanner-btn');
const cancel_scan_btn = document.getElementById('product-scanner-cancel-btn');
const product_scan_modal = document.getElementById('product-scanner-modal');

const p_element = document.getElementById('order-id');
const order_id = p_element.dataset.orderId;

const ean_scan_error_modal = document.getElementById('ean-scan-error-modal');
const close_ean_error_modal = document.getElementById('close-ean-error-modal')

const no_stock_modal = document.getElementById('no-stock-modal')
const close_no_stock_modal = document.getElementById('close-no-stock-modal')

let html5QrCode = new Html5Qrcode("product-reader", { formatsToSupport: [ Html5QrcodeSupportedFormats.EAN_13 ] });
//Initialize the code scanner. El parámetro que acepta es el id del elemento html que va a abrir el scanner. En este caso, el div con id 'reader'. En el segundo parámetro se puede especificar explicitamente los tipos de códigos que se pueden escanearm en este caso, el escaner solo permite EAN_13.

//Con esta función se puede recoger un csrf token para luego usar para AJAX Post requests. Esta función la saque directamente de la documentación de django, así que no hay necesidad de entenderlo en detalle: https://docs.djangoproject.com/en/6.0/howto/csrf/#using-csrf-protection-with-ajax
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

//The htmx:response:error event fires when the server responds with an HTTP error status code (400 or higher). Un status_code erroneo es reconocido por htmx y le dice que no debe cambiar el el elemento target (En este caso #scanned-order-container). Sn este evento, htmx cambiaría el elemento target entero por un modal de error.
document.body.addEventListener('htmx:responseError', function(evt) {
    //const msg = evt.detail.xhr.responseText;

    //detail.xhr - the XMLHttpRequest. Is an API in the form of a JavaScript object whose methods transmit HTTP requests from a web browser to a web server. Lo vamos a usar para acceder a los detalles de la petición AJAX de htmx en caso de que tenga un status_code erroneo dentro del view 'scan_product_ean'.  

    const msg = evt.detail.xhr.responseText; // detail.xhr.responseText: Returns the text received from a server following a request being sent. El texto crudo del httpresponse desde el view de django.
    const NoStockHeader = evt.detail.xhr.getResponseHeader('No-Stock-product'); //The XMLHttpRequest method getResponseHeader() returns the string containing the text of a particular header's value. Esto es lo que va a recoger el JSON con el id del 'order_product' sin stock.


    if (NoStockHeader != null) { //Si es un error de escaneo de producto relacionado a no tener stock.
        let NoStockData = JSON.parse(NoStockHeader); //The JSON.parse() static method parses a JSON string, constructing the JavaScript value or object described by the string. 

        no_stock_product_input = document.getElementById('product-id-without-stock')
        no_stock_product_input.value = NoStockData.orderProductId;

        //no_stock_modal.dataset.orderProductId = NoStockData.orderProductId; //Esta instrucción crea/actualiza un atributo 'data-order-product-id="<id>"' dentro de <div id="no-stock-modal">.
        no_stock_modal.style.display = 'flex';
        no_stock_modal.style.flexDirection = 'column';
        no_stock_modal.style.alignItems = 'center';
        no_stock_modal.style.justifyContent = 'center';
        document.getElementById('no-stock-warning-text').textContent = msg;

    } else { //Si es un error de escaneo de producto de cualquier otro tipo. (Estos no tienen header)
        ean_scan_error_modal.style.display = 'flex';
        ean_scan_error_modal.style.flexDirection = 'column';
        ean_scan_error_modal.style.alignItems = 'center';
        ean_scan_error_modal.style.justifyContent = 'center';
        document.getElementById('ean-scan-error-text').textContent = msg;
    }

});

activate_scan_btn.addEventListener('click', () => {
    product_scan_modal.style.display = 'flex';
    product_scan_modal.style.flexDirection = 'column';
    product_scan_modal.style.alignItems = 'center';
    product_scan_modal.style.justifyContent = 'center';

    html5QrCode.start(
        { facingMode: "environment" },  // back camera
        { fps: 10, qrbox: {width: 200, height: 100} }, //frame per second, the default value for this is 2, but it can be increased to get faster scanning. Increasing too high value could affect performance. Value >1000 will simply fail.
        //Use this property to limit the region of the viewfinder you want to use for scanning. The rest of the viewfinder would be shaded.
        (decodedText) => {
            //Primero se detiene el escaner de html5QrCode limpiamente (Esto va a asegurar que solo se procese una lectura de escaner) y luego se procesa la promesa exitosa de esta operación asíncrona con .then()
            html5QrCode.stop().then(() => {
                product_scan_modal.style.display = 'none';
                //Issues an htmx-style AJAX request. En este caso es un POST request. Esto es lo que va a permitir actualizar el font-end del contador en tiempo real.
                htmx.ajax('POST', `/orders/${order_id}/scan-product-ean/`, {
                    target: '#scanned-order-container',
                    headers: {
                        'X-CSRFToken': csrftoken // Provide safety authentication to Django
                    },
                    //values to submit with the request
                    values: { 
                        'barcode': decodedText  // Send the barcode payload under 'request.POST'. Esto es lo que contiene el EAN.
                    }
                })
            });
            
        }
    );
});

//start(cameraIdOrConfig, configuration, qrCodeSuccessCallback, qrCodeErrorCallback): Promise<null> -->Start scanning QR codes or bar codes for a given camera.
    //cameraIdOrConfig --> Identifier of the camera, it can either be the camera id retrieved from Html5Qrcode#getCameras() method or object with facing mode constraint.
    //configuration --> Extra configurations to tune the code scanner.
    //qrCodeSuccessCallback --> Callback called when an instance of a QR code or any other supported bar code is found.
    //qrCodeErrorCallback --> Callback called in cases where no instance of QR code or any other supported bar code is found.


cancel_scan_btn.addEventListener('click', () => {
    product_scan_modal.style.display = 'none';
    html5QrCode.stop(); //Stops streaming QR Code video and scanning.
});

close_ean_error_modal.addEventListener('click', () => {
    ean_scan_error_modal.style.display = 'none';
});

close_no_stock_modal.addEventListener('click', () => {
    no_stock_modal.style.display = 'none';
});