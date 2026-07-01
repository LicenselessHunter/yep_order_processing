/* En este diccionario se usa la biblioteca JS 'html5-qrcode', el cuál permite renderizar un escaner de códigos QR y otros tipos de códigos. Documentación: https://github.com/mebjas/html5-qrcode */

let html5QrCode = new Html5Qrcode("reader", { formatsToSupport: [ Html5QrcodeSupportedFormats.EAN_13 ] });
//Initialize the code scanner. El parámetro que acepta es el id del elemento html que va a abrir el scanner. En este caso, el div con id 'reader'. En el segundo parámetro se puede especificar explicitamente los tipos de códigos que se pueden escanearm en este caso, el escaner solo permite EAN_13.

let activate_scan_btn = document.getElementById('activate-scan');
let cancel_scan_btn = document.getElementById('cancel-scan');


activate_scan_btn.addEventListener('click', () => {
    cancel_scan_btn.style.display = 'block';
    activate_scan_btn.style.display = 'none';

    html5QrCode.start(
        { facingMode: "environment" },  // back camera
        { fps: 10, qrbox: {width: 200, height: 100} }, //frame per second, the default value for this is 2, but it can be increased to get faster scanning. Increasing too high value could affect performance. Value >1000 will simply fail.
        //Use this property to limit the region of the viewfinder you want to use for scanning. The rest of the viewfinder would be shaded.
        (decodedText) => {
            activate_scan_btn.style.display = 'block';
            cancel_scan_btn.style.display = 'none';
            document.getElementById('id_ean').value = decodedText; //Se toma el input del ean y como valor se agrega el 'decodedText', que en este caso sería el número del barcode escaneado.
            html5QrCode.stop(); //Stops streaming QR Code video and scanning.
        }
    );
});

//start(cameraIdOrConfig, configuration, qrCodeSuccessCallback, qrCodeErrorCallback): Promise<null> -->Start scanning QR codes or bar codes for a given camera.
    //cameraIdOrConfig --> Identifier of the camera, it can either be the camera id retrieved from Html5Qrcode#getCameras() method or object with facing mode constraint.
    //configuration --> Extra configurations to tune the code scanner.
    //qrCodeSuccessCallback --> Callback called when an instance of a QR code or any other supported bar code is found.
    //qrCodeErrorCallback --> Callback called in cases where no instance of QR code or any other supported bar code is found.


cancel_scan_btn.addEventListener('click', () => {
    activate_scan_btn.style.display = 'block';
    cancel_scan_btn.style.display = 'none';
    html5QrCode.stop(); //Stops streaming QR Code video and scanning.
});



