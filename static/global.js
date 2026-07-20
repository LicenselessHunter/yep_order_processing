let NavOpenBtn = document.getElementById('nav-open-btn')
let NavCloseBtn = document.getElementById('nav-close-btn')

let Nav = document.querySelector('nav')

let messages_container = document.getElementById('messages-container') //Elemento que va a contener todo el contenido relacionado a django-messages dentro de 'global.html'.

NavOpenBtn.addEventListener('click', () => {
    Nav.style.display = 'block'
});

NavCloseBtn.addEventListener('click', () => {
    Nav.style.display = 'none'
});



let dropbtn; /*Esta variable servira de manera global para referenciar al botón de activación del dropdown.

/*Esta función se activa al hacer click en cualquier lugar de la ventana*/
window.addEventListener('click', function(event) { 
  /*Si es que se clickea algún botón para activar el dropdown del sidebar*/
  if (event.target.matches('.dropbtn')) { 

    /*'event.target' va a ser el elemento exacto al que se hizo click.*/
    
    /*Si es que ya había un dropdown activado, este se cerrara, para evitar que se active más de un dropdown a la vez*/
    if (dropbtn){ 
      dropbtn.nextElementSibling.style.display = "none";
    } 
    
    dropbtn = event.target
    
    dropbtn.nextElementSibling.style.display = "block"; /*Se activa el dropdown*/
  }

  /*Si es que se hace click en cualquier lugar de la ventana, excepto un botón de activavión del dropdown*/
  else if (!event.target.matches('.dropbtn') && dropbtn) {
    dropbtn.nextElementSibling.style.display = "none"; /*Se desactiva el dropdown*/
  }
});


//Si es que el ul 'messages-container' dentro de global.html no es null (Esto es cuando hay al menos un django messsage activado). Si es que no hay ningún django message activado, entonces este elemento simplemente no existe.
if (messages_container !== null) {

  let messageCloseBtns = document.querySelectorAll('.message-close-btn') //Se recogen los botónes para cerrar los mensajes individuales.

  messageCloseBtns.forEach((btn) => { //Para cada botón para cerrar los mensajes individuales
    btn.addEventListener('click', () => { //Se va a agregar un event listener al hacer click.
      message_type_div = btn.parentElement.parentElement; //Esto va a representar el div que contiene los mensajes según su tipo (success, error, etc)
      
      btn.parentElement.remove() //Se elimina el elemento padre del botón de cierre, es decir, el mensaje individual al que está anclado.

      if (message_type_div.querySelectorAll('li').length === 0) { //Se elimina el div que contiene los mensajes según su tipo (success, error, etc) si es que queda con 0 mensajes.
        message_type_div.remove()
      }

      if (messages_container.querySelectorAll('li').length === 0) { //Si es que el ul 'messages-container' queda con 0 mensajes, entonces se eliminará este elemento entero.
        messages_container.remove()
      }
    });
  });

}