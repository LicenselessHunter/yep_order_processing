const activate_label_scan_btn = document.getElementById('activate-label-scan-btn');
const cancel_label_scan_btn = document.getElementById('cancel-label-scan-btn');
const label_scan_modal = document.getElementById('label-scan-modal');

const p_element = document.getElementById('order-group-id');
const order_group_id = p_element.dataset.groupId;

const label_scan_error_modal = document.getElementById('label-scan-error-modal');
const close_label_error_modal = document.getElementById('close-label-error-modal')

let html5QrCode = new Html5Qrcode("label-reader");
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


function display_error_modal(error) {
    label_scan_error_modal.style.display = 'flex';
    label_scan_error_modal.style.flexDirection = 'column';
    label_scan_error_modal.style.alignItems = 'center';
    label_scan_error_modal.style.justifyContent = 'center';
    document.getElementById('label-scan-error-text').textContent = error;
}


//Event listener para activar el scanner.
activate_label_scan_btn.addEventListener('click', () => {
    label_scan_modal.style.display = 'flex';
    label_scan_modal.style.flexDirection = 'column';
    label_scan_modal.style.alignItems = 'center';
    label_scan_modal.style.justifyContent = 'center';


    html5QrCode.start(
            { facingMode: "environment" },  // back camera
            { fps: 10, qrbox: {width: 200, height: 100} }, //frame per second, the default value for this is 2, but it can be increased to get faster scanning. Increasing too high value could affect performance. Value >1000 will simply fail.
            //Use this property to limit the region of the viewfinder you want to use for scanning. The rest of the viewfinder would be shaded.
            (decodedText) => { //El decodedText sería el shipping id de una etiqueta.
                //The Fetch API provides a JavaScript interface for making HTTP requests and processing the responses.
                //Para este caso, estamos usando fetch API para mandar un POST request a la url que está en el primer parámetro, en este caso, la url de name 'scanned_order_label'. 
                //En realidad no es estrictamente necesario que esto sea un POST request, pero al dejarlo así garantiza que esto solo se active al usar el scanner, además de otorgar protección CSRF, asegurando que la petición provenga de esta misma aplicación y no de un script malicioso externo que intenta adivinar IDs de envío.
                fetch(`/orders/order_group/${order_group_id}/scanned-order-label/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrftoken,
                        'Content-Type': 'application/json'
                        },

                    body: JSON.stringify({
                        'label_data_json': decodedText
                        })

                    })
                    .then(response => {
                            //if (response.ok) {
                            return response.json();
                            //}
                        })
                    .then(data => {
                            // Primero apagamos el escáner limpiamente

                            html5QrCode.stop().then(() => {
                                if (data.error){
                                    label_scan_modal.style.display = 'none';
                                    display_error_modal(data.error);

                                
                                }else{
                                    // Una vez apagado, redirigimos usando la URL que mandó Django
                                    window.location.href = data.redirect_url;
                                }

                            });
                    })

            }
        );

});

//start(cameraIdOrConfig, configuration, qrCodeSuccessCallback, qrCodeErrorCallback): Promise<null> -->Start scanning QR codes or bar codes for a given camera.
    //cameraIdOrConfig --> Identifier of the camera, it can either be the camera id retrieved from Html5Qrcode#getCameras() method or object with facing mode constraint.
    //configuration --> Extra configurations to tune the code scanner.
    //qrCodeSuccessCallback --> Callback called when an instance of a QR code or any other supported bar code is found.
    //qrCodeErrorCallback --> Callback called in cases where no instance of QR code or any other supported bar code is found.


//Event listener para cerrar el scanner.
cancel_label_scan_btn.addEventListener('click', () => {
    label_scan_modal.style.display = 'none';
    html5QrCode.stop(); //Stops streaming QR Code video and scanning.
});

close_label_error_modal.addEventListener('click', () => {
    label_scan_error_modal.style.display = 'none';
});

