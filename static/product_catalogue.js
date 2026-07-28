let product_dropbtn; /*Esta variable servira de manera global para referenciar al botón de activación del dropdown.

/*Esta función se activa al hacer click en cualquier lugar de la ventana*/
window.addEventListener('click', function(event) { 
  /*Si es que se clickea algún botón para activar el dropdown del sidebar*/
  if (event.target.matches('.product-option-btn')) { 

    /*'event.target' va a ser el elemento exacto al que se hizo click.*/
    
    /*Si es que ya había un dropdown activado, este se cerrara, para evitar que se active más de un dropdown a la vez*/
    if (product_dropbtn){ 
      product_dropbtn.children[0].style.display = "none";
    } 
    
    product_dropbtn = event.target
    
    product_dropbtn.children[0].style.display = "flex"; /*Se activa el dropdown*/
  }

  /*Si es que se hace click en cualquier lugar de la ventana, excepto un botón de activción del dropdown*/
  else if (!event.target.matches('.product-option-btn') && product_dropbtn) {
    product_dropbtn.children[0].style.display = "none"; /*Se desactiva el dropdown*/
  }
});