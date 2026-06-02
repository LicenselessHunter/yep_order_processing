const ordersTitle = document.querySelector('.orders_title');

const modals = document.querySelectorAll('.modal');
const print_bts = document.querySelectorAll('.print_btn_modal');


print_bts.forEach(btn => {
  btn.addEventListener('click', (e) => {
    if (e.target == document.getElementById('collect_print_btn_modal')) {
      document.getElementById('collect_labels_modal').style.display = 'block';
    } else if (e.target == document.getElementById('flex_print_btn_modal')) {
      document.getElementById('flex_labels_modal').style.display = 'block';
    }
  });
});



modals.forEach(modal => {
  modal.addEventListener('click', (e) => {
    if (e.target.matches('.modal')) {
      //modal = e.target;
      e.target.style.display = "none";
    }
  });
});


const toggles = [];

[
  { 
    btn: document.getElementById('toggle_collect_print'), 
    container: document.getElementById('ml_collect_orders_print'), 
    label: 'Órdenes de colecta para imprimir',
  },
  { 
    btn: document.getElementById('toggle_collect_ship'),  
    container: document.getElementById('ml_collect_orders_ship'),
    label: 'Órdenes de colecta listas para despachar',
  },
  { 
    btn: document.getElementById('toggle_flex_print'),    
    container: document.getElementById('ml_flex_orders_print'),
    label: 'Órdenes de flex para imprimir',
  },
  {
    btn: document.getElementById('toggle_flex_ship'),
    container: document.getElementById('ml_flex_orders_ship'),
    label: 'Órdenes de flex listas para despachar',
  },
].forEach(item => {
  if (item.btn) toggles.push(item);
});



function activateToggle(active) {

  if (print_bts.length != 0) {
    print_bts.forEach(print_btn => {
      print_btn.style.display = 'none';
    });
  }


  toggles.forEach((toggle) => {

    if (toggle.container != active.container || toggle.container == 'flex'){
        toggle.btn.style.fontWeight = 'normal';
        toggle.btn.style.backgroundColor = 'transparent';
        ordersTitle.style.display = 'none';
        toggle.container.style.display = 'none';
    }
  });

  if (active.container.style.display === 'flex'){
      active.btn.style.fontWeight = 'normal';
      active.btn.style.backgroundColor = 'transparent';
      ordersTitle.textContent = '';
      ordersTitle.style.display = 'none';
      active.container.style.display = 'none';

  }else{
      active.btn.style.fontWeight = 'bold';
      active.btn.style.backgroundColor = 'rgb(130, 126, 126)';
      ordersTitle.textContent = active.label;
      ordersTitle.style.display = 'block';
      active.container.style.display = 'flex';

      if (print_bts.length != 0) {
        if (active.btn == document.getElementById('toggle_collect_print')){
          document.getElementById('collect_print_btn_modal').style.display = 'inline-block';
        } else if(active.btn == document.getElementById('toggle_flex_print')) {
          document.getElementById('flex_print_btn_modal').style.display = 'inline-block';
        }
      }
      
  }
}


toggles.forEach((toggle) => {
  toggle.btn.addEventListener('click', () => activateToggle(toggle));  
});

