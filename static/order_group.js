

const activate_label_scan_btn = document.getElementById('activate-label-scan-btn');
const cancel_label_scan_btn = document.getElementById('cancel-label-scan-btn');
const label_scan_modal = document.getElementById('label-scan-modal');


let html5QrCode = new Html5Qrcode("label-reader");
//Initialize the code scanner. El parámetro que acepta es el id del elemento html que va a abrir el scanner. En este caso, el div con id 'reader'. En el segundo parámetro se puede especificar explicitamente los tipos de códigos que se pueden escanearm en este caso, el escaner solo permite EAN_13.

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

activate_label_scan_btn.addEventListener('click', () => {
    label_scan_modal.style.display = 'flex';
    label_scan_modal.style.flexDirection = 'column';
    label_scan_modal.style.alignItems = 'center';
    label_scan_modal.style.justifyContent = 'center';


    html5QrCode.start(
            { facingMode: "environment" },  // back camera
            { fps: 10, qrbox: {width: 200, height: 100} }, //frame per second, the default value for this is 2, but it can be increased to get faster scanning. Increasing too high value could affect performance. Value >1000 will simply fail.
            //Use this property to limit the region of the viewfinder you want to use for scanning. The rest of the viewfinder would be shaded.
            (decodedText) => {
                console.log(decodedText)
                fetch(`/orders/scanned-order-label/${decodedText}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrftoken,
                        },
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.order_id) {
                            const orders_from_group = document.querySelectorAll('.order-from-group-container');

                            orders_from_group.forEach(order => {
                                order.style.display = 'none';
                            });

                            const order_scanned = document.querySelector(
                                `[data-order-id="${data.order_id}"]`
                            );
                            
                            order_scanned.style.display = 'flex';
                        }
                        label_scan_modal.style.display = 'none';
                        html5QrCode.stop(); //Stops streaming QR Code video and scanning.

                    });

            }
        );

});

cancel_label_scan_btn.addEventListener('click', () => {
    label_scan_modal.style.display = 'none';
    html5QrCode.stop(); //Stops streaming QR Code video and scanning.
});
