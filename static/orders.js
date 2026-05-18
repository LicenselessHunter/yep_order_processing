const ordersTitle = document.querySelector('.orders_title');

const toggles = [
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
];


function activateToggle(active) {

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
        
    }
    
}


toggles.forEach((toggle) => {
    toggle.btn.addEventListener('click', () => activateToggle(toggle));
});

